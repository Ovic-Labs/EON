"""High-performance, CPU-first, in-memory asynchronous Event Bus for OVIC EON."""

import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from enum import Enum
from typing import Any, Final
from uuid import uuid4

from pydantic import Field

from eon.core.backpressure import BackpressurePolicy
from eon.core.delivery import DeliveryOutcome, DeliveryState
from eon.core.event_router import EventRouter
from eon.core.exceptions import (
    EventBusNotRunningError,
    InvalidEventError,
    InvalidLifecycleTransitionError,
    QueueClosedError,
    QueueFullError,
)
from eon.core.metrics import EventBusMetrics, EventBusMetricsSnapshot
from eon.core.priority import EventPriority
from eon.core.subscription import (
    EventHandler,
    Subscription,
    SubscriptionId,
    generate_subscription_id,
)
from eon.schemas.base import EonBaseModel
from eon.schemas.events import EventEnvelope, EventType

DEFAULT_QUEUE_CAPACITY: Final[int] = 1000
DEFAULT_PUBLISH_TIMEOUT: Final[float] = 2.0
DEFAULT_HANDLER_TIMEOUT: Final[float] = 5.0
DEFAULT_SHUTDOWN_TIMEOUT: Final[float] = 5.0
DEFAULT_SYNC_WORKERS: Final[int] = 4
DEFAULT_STARVATION_THRESHOLD: Final[int] = 10


class EventBusLifecycleState(str, Enum):
    """Lifecycle state machine for the Event Bus."""

    CREATED = "created"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    FAILED = "failed"


class EventBusConfig(EonBaseModel):
    """Validated configuration for Event Bus initialization."""

    default_queue_capacity: int = Field(
        default=DEFAULT_QUEUE_CAPACITY,
        gt=0,
        description="Default queue capacity for individual subscriber queues.",
    )
    default_backpressure_policy: BackpressurePolicy = Field(
        default=BackpressurePolicy.WAIT,
        description="Default policy applied when subscriber queue reaches capacity.",
    )
    publish_timeout_seconds: float = Field(
        default=DEFAULT_PUBLISH_TIMEOUT,
        gt=0.0,
        description="Timeout for publishers waiting on queue space under WAIT policy.",
    )
    handler_timeout_seconds: float = Field(
        default=DEFAULT_HANDLER_TIMEOUT,
        gt=0.0,
        description="Maximum execution time permitted for a subscriber handler.",
    )
    shutdown_timeout_seconds: float = Field(
        default=DEFAULT_SHUTDOWN_TIMEOUT,
        gt=0.0,
        description="Maximum time allowed for queues to drain during graceful shutdown.",
    )
    max_workers_per_subscription: int = Field(
        default=1,
        gt=0,
        description="Number of concurrent worker tasks allocated per subscription.",
    )
    sync_executor_workers: int = Field(
        default=DEFAULT_SYNC_WORKERS,
        gt=0,
        description="Maximum worker threads allocated for synchronous handlers.",
    )
    starvation_threshold: int = Field(
        default=DEFAULT_STARVATION_THRESHOLD,
        gt=0,
        description="High-priority dispatches before a waiting lower-priority event is dispatched.",
    )


class EventBus:
    """CPU-first, in-memory, asynchronous Event Bus for OVIC EON.

    Provides:
    - Typed event publishing accepting validated EventEnvelope data contracts.
    - Snapshot-based event routing with exact event-type and wildcard matching.
    - Isolated, bounded priority queues per subscriber with true oldest-event eviction.
    - Explicit backpressure policies (WAIT, REJECT, DROP_NEWEST, DROP_OLDEST).
    - Starvation prevention ensuring lower-priority events are not starved by high-priority traffic.
    - Multi-subscriber concurrent enqueue preventing saturated subscribers from blocking others.
    - Failure isolation: synchronous handlers run in thread executor; exceptions never leak secrets.
    - Robust publish_and_wait with futures resolved on every terminal outcome.
    - Graceful lifecycle shutdown with queue draining, queue closure, and zero task leaks.
    - In-process concurrency-safe metrics.

    NON-AUTHORITY SAFETY NOTICE:
    This Event Bus is a software communication substrate. It is NOT a certified robot
    safety controller (ISO 13849/10218) and possesses NO actuator or motion authorization.
    All emotional, behavioral, and advisory payloads are strictly non-authoritative.
    """

    def __init__(self, config: EventBusConfig | None = None) -> None:
        self._config = config or EventBusConfig()
        self._state = EventBusLifecycleState.CREATED
        self._state_lock = asyncio.Lock()
        self._router = EventRouter()
        self._metrics = EventBusMetrics()
        self._workers: list[asyncio.Task[None]] = []
        self._delivery_waiters: dict[tuple[str, str], list[asyncio.Future[DeliveryOutcome]]] = {}
        self._sync_executor = ThreadPoolExecutor(
            max_workers=self._config.sync_executor_workers,
            thread_name_prefix="eon_sync_worker",
        )

    @property
    def lifecycle_state(self) -> EventBusLifecycleState:
        """Current operational lifecycle state."""
        return self._state

    @property
    def config(self) -> EventBusConfig:
        """Current configuration."""
        return self._config

    def is_running(self) -> bool:
        """Check if event bus is currently active and accepting events."""
        return self._state == EventBusLifecycleState.RUNNING

    async def start(self) -> None:
        """Start the event bus and initialize background dispatch workers.

        Idempotent: Calling start() on an already RUNNING bus is a safe no-op.
        Raises InvalidLifecycleTransitionError if called during STOPPING.
        """
        async with self._state_lock:
            if self._state == EventBusLifecycleState.RUNNING:
                return
            if self._state == EventBusLifecycleState.STOPPING:
                raise InvalidLifecycleTransitionError(
                    "Cannot start Event Bus while it is currently STOPPING."
                )
            if self._state == EventBusLifecycleState.STOPPED:
                raise InvalidLifecycleTransitionError(
                    "Cannot start Event Bus: STOPPED state is terminal."
                )

            self._state = EventBusLifecycleState.RUNNING

            # Start workers for any existing subscriptions
            for sub in self._router.get_all_subscribers():
                self._ensure_workers(sub)

    async def stop(self, timeout: float | None = None) -> None:
        """Gracefully shut down the event bus, closing queues, draining, and stopping workers.

        Idempotent: Calling stop() on an already STOPPED bus is a safe no-op.
        """
        if timeout is not None and timeout < 0.0:
            raise ValueError(f"Shutdown timeout must be non-negative (>= 0.0), got {timeout}")

        async with self._state_lock:
            if self._state == EventBusLifecycleState.STOPPED:
                return
            if self._state == EventBusLifecycleState.CREATED:
                self._state = EventBusLifecycleState.STOPPED
                self._sync_executor.shutdown(wait=False, cancel_futures=True)
                return

            self._state = EventBusLifecycleState.STOPPING

        shutdown_timeout = timeout if timeout is not None else self._config.shutdown_timeout_seconds
        deadline = time.monotonic() + shutdown_timeout if shutdown_timeout > 0 else None
        all_subs = self._router.get_all_subscribers()

        # Step 1: Explicitly close each subscriber queue immediately.
        # This immediately unblocks any publishers waiting on WAIT policy and joiners.
        for sub in all_subs:
            sub.queue.close()

        # Step 2: Drain queues and wait for active handlers to complete up to timeout boundary
        if all_subs:
            drain_tasks = [sub.queue.join() for sub in all_subs]
            try:
                if deadline is not None:
                    remaining = max(0.0, deadline - time.monotonic())
                    if remaining > 0:
                        await asyncio.wait_for(
                            asyncio.gather(*drain_tasks, return_exceptions=True),
                            timeout=remaining,
                        )
                else:
                    await asyncio.gather(*drain_tasks, return_exceptions=True)
            except asyncio.TimeoutError:
                pass

        # Step 3: Cancel all remaining worker tasks
        for worker in self._workers:
            if not worker.done():
                worker.cancel()

        if self._workers:
            try:
                if deadline is not None:
                    remaining = max(0.0, deadline - time.monotonic())
                    if remaining > 0:
                        await asyncio.wait_for(
                            asyncio.gather(*self._workers, return_exceptions=True),
                            timeout=remaining,
                        )
                else:
                    await asyncio.gather(*self._workers, return_exceptions=True)
            except asyncio.TimeoutError:
                pass
        self._workers.clear()

        # Step 4: Evacuate any remaining items in queues, mark them cancelled, and resolve waiters
        for sub in all_subs:
            drained_items = sub.queue.drain()
            for item in drained_items:
                self._metrics.record_cancelled()
                diag_id = f"ERR-SHUT-{uuid4().hex[:8].upper()}"
                cancelled_outcome = DeliveryOutcome.create(
                    event_id=str(item.event_id),
                    subscription_id=sub.subscription_id,
                    state=DeliveryState.CANCELLED,
                    error_category="ShutdownCancelled",
                    diagnostic_id=diag_id,
                )
                self._resolve_waiters(str(item.event_id), sub.subscription_id, cancelled_outcome)

        # Step 5: Shut down synchronous worker executor
        self._sync_executor.shutdown(wait=False, cancel_futures=True)

        async with self._state_lock:
            self._state = EventBusLifecycleState.STOPPED

    async def __aenter__(self) -> "EventBus":
        """Async context manager entry."""
        await self.start()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        """Async context manager exit with guaranteed cleanup."""
        await self.stop()

    def subscribe(
        self,
        event_type: EventType | str,
        handler: EventHandler,
        name: str | None = None,
        backpressure_policy: BackpressurePolicy | None = None,
        queue_capacity: int | None = None,
        timeout_seconds: float | None = None,
        max_concurrency: int | None = None,
    ) -> SubscriptionId:
        """Register a subscriber for the specified event type.

        Can be called before start() or during RUNNING.
        Rejects non-positive configuration values with ValueError.
        Returns unique SubscriptionId.
        """
        if self._state in (EventBusLifecycleState.STOPPING, EventBusLifecycleState.STOPPED):
            raise EventBusNotRunningError(
                f"Cannot subscribe when Event Bus is in state {self._state.value}."
            )

        if queue_capacity is not None:
            if queue_capacity <= 0:
                raise ValueError(f"queue_capacity must be positive (> 0), got {queue_capacity}")
            resolved_capacity = queue_capacity
        else:
            resolved_capacity = self._config.default_queue_capacity

        if timeout_seconds is not None:
            if timeout_seconds <= 0.0:
                raise ValueError(f"timeout_seconds must be positive (> 0.0), got {timeout_seconds}")
            resolved_timeout = timeout_seconds
        else:
            resolved_timeout = self._config.handler_timeout_seconds

        if max_concurrency is not None:
            if max_concurrency <= 0:
                raise ValueError(f"max_concurrency must be positive (> 0), got {max_concurrency}")
            resolved_concurrency = max_concurrency
        else:
            resolved_concurrency = self._config.max_workers_per_subscription

        resolved_policy = (
            backpressure_policy
            if backpressure_policy is not None
            else self._config.default_backpressure_policy
        )

        sub_id = generate_subscription_id()
        etype_str = event_type.value if isinstance(event_type, EventType) else str(event_type)
        sub_name = name or f"sub_{etype_str}_{sub_id[:8]}"

        sub = Subscription(
            subscription_id=sub_id,
            event_type=etype_str,
            handler=handler,
            name=sub_name,
            backpressure_policy=resolved_policy,
            queue_capacity=resolved_capacity,
            timeout_seconds=resolved_timeout,
            max_concurrency=resolved_concurrency,
            starvation_threshold=self._config.starvation_threshold,
        )

        self._router.register(sub)
        if self._state == EventBusLifecycleState.RUNNING:
            self._ensure_workers(sub)

        return sub_id

    async def subscribe_async(
        self,
        event_type: EventType | str,
        handler: EventHandler,
        name: str | None = None,
        backpressure_policy: BackpressurePolicy | None = None,
        queue_capacity: int | None = None,
        timeout_seconds: float | None = None,
        max_concurrency: int | None = None,
    ) -> SubscriptionId:
        """Asynchronously register a subscriber with verified router synchronization."""
        return self.subscribe(
            event_type=event_type,
            handler=handler,
            name=name,
            backpressure_policy=backpressure_policy,
            queue_capacity=queue_capacity,
            timeout_seconds=timeout_seconds,
            max_concurrency=max_concurrency,
        )

    async def unsubscribe(self, subscription_id: SubscriptionId) -> bool:
        """Unregister a subscription, terminate workers, drain pending items, and balance queues."""
        try:
            sub = self._router.unregister(subscription_id)
        except Exception:
            return False

        sub.is_active = False
        sub.queue.close()

        for w in sub.workers:
            if not w.done():
                w.cancel()

        if sub.workers:
            await asyncio.gather(*sub.workers, return_exceptions=True)
            self._workers = [w for w in self._workers if w not in sub.workers]
            sub.workers.clear()

        # Drain any remaining items and record as cancelled
        drained_items = sub.queue.drain()
        for item in drained_items:
            self._metrics.record_cancelled()
            diag_id = f"ERR-UNSUB-{uuid4().hex[:8].upper()}"
            cancelled_outcome = DeliveryOutcome.create(
                event_id=str(item.event_id),
                subscription_id=sub.subscription_id,
                state=DeliveryState.CANCELLED,
                error_category="SubscriptionCancelled",
                diagnostic_id=diag_id,
            )
            self._resolve_waiters(str(item.event_id), sub.subscription_id, cancelled_outcome)

        return True

    def _ensure_workers(self, sub: Subscription) -> None:
        """Ensure worker tasks are running for a given subscription."""
        if not sub.is_active or not self.is_running():
            return

        needed = sub.max_concurrency - len([w for w in sub.workers if not w.done()])
        for _ in range(needed):
            worker_task = asyncio.create_task(
                self._dispatch_worker(sub),
                name=f"worker_{sub.name}_{len(sub.workers)}",
            )
            sub.workers.append(worker_task)
            self._workers.append(worker_task)

    def _register_waiter(
        self,
        event_id: str,
        subscription_id: str,
        future: asyncio.Future[DeliveryOutcome],
    ) -> None:
        """Register a delivery completion future for an event and subscription."""
        key = (event_id, subscription_id)
        self._delivery_waiters.setdefault(key, []).append(future)

    def _resolve_waiters(
        self,
        event_id: str,
        subscription_id: str | None,
        outcome: DeliveryOutcome,
    ) -> None:
        """Resolve all registered completion futures for an event and subscription."""
        if subscription_id is None:
            return
        key = (event_id, subscription_id)
        waiters = self._delivery_waiters.pop(key, None)
        if waiters:
            for fut in waiters:
                if not fut.done():
                    fut.set_result(outcome)

    async def _dispatch_worker(self, sub: Subscription) -> None:
        """Isolated background worker consuming events from a subscriber queue."""
        while self._state in (EventBusLifecycleState.RUNNING, EventBusLifecycleState.STOPPING):
            try:
                priority, event = await sub.queue.get()
            except (asyncio.CancelledError, QueueClosedError):
                break

            start_time = time.monotonic()
            is_timeout = False
            delivery_state = DeliveryState.DELIVERED
            err_category: str | None = None
            diag_id: str | None = None

            try:
                # Execute subscriber handler with timeout, running sync handlers in executor
                await asyncio.wait_for(
                    sub.invoke_handler(event, executor=self._sync_executor),
                    timeout=sub.timeout_seconds,
                )
            except asyncio.TimeoutError:
                is_timeout = True
                delivery_state = DeliveryState.FAILED
                err_category = "HandlerTimeout"
                diag_id = f"ERR-TO-{uuid4().hex[:8].upper()}"
            except asyncio.CancelledError:
                delivery_state = DeliveryState.CANCELLED
                err_category = "HandlerCancelled"
                diag_id = f"ERR-CAN-{uuid4().hex[:8].upper()}"
                sub.queue.task_done()
                outcome = DeliveryOutcome.create(
                    event_id=str(event.event_id),
                    subscription_id=sub.subscription_id,
                    state=delivery_state,
                    duration_ms=(time.monotonic() - start_time) * 1000.0,
                    error_category=err_category,
                    diagnostic_id=diag_id,
                )
                self._metrics.record_cancelled()
                self._resolve_waiters(str(event.event_id), sub.subscription_id, outcome)
                break
            except Exception as exc:
                delivery_state = DeliveryState.FAILED
                err_category = f"HandlerException[{type(exc).__name__}]"
                diag_id = f"ERR-{uuid4().hex[:8].upper()}"
            finally:
                if delivery_state != DeliveryState.CANCELLED:
                    duration_ms = (time.monotonic() - start_time) * 1000.0
                    sub.queue.task_done()
                    outcome = DeliveryOutcome.create(
                        event_id=str(event.event_id),
                        subscription_id=sub.subscription_id,
                        state=delivery_state,
                        duration_ms=duration_ms,
                        error_category=err_category,
                        diagnostic_id=diag_id,
                    )

                    # Update metrics
                    if delivery_state == DeliveryState.DELIVERED:
                        self._metrics.record_delivered(duration_ms)
                    elif delivery_state == DeliveryState.FAILED:
                        self._metrics.record_failed(is_timeout=is_timeout)

                    # Resolve completion waiter
                    self._resolve_waiters(str(event.event_id), sub.subscription_id, outcome)

    def _record_publish_outcome(
        self,
        event_id_str: str,
        sub: Subscription,
        state: DeliveryState,
        evicted: Any | None,
        exc: Exception | None,
        outcomes: list[DeliveryOutcome],
    ) -> None:
        """Record the publication outcome for a subscriber and resolve any eviction waiters."""
        if state == DeliveryState.QUEUED:
            self._metrics.record_accepted()
            outcomes.append(
                DeliveryOutcome.create(
                    event_id=event_id_str,
                    subscription_id=sub.subscription_id,
                    state=DeliveryState.QUEUED,
                )
            )
            if evicted is not None:
                self._metrics.record_dropped()
                diag_id = f"ERR-EVICT-{uuid4().hex[:8].upper()}"
                evicted_outcome = DeliveryOutcome.create(
                    event_id=str(evicted.event_id),
                    subscription_id=sub.subscription_id,
                    state=DeliveryState.DROPPED,
                    error_category="QueueEvicted",
                    diagnostic_id=diag_id,
                )
                self._resolve_waiters(str(evicted.event_id), sub.subscription_id, evicted_outcome)
        elif state == DeliveryState.DROPPED:
            self._metrics.record_dropped()
            diag_id = f"ERR-DROP-{uuid4().hex[:8].upper()}"
            dropped_outcome = DeliveryOutcome.create(
                event_id=event_id_str,
                subscription_id=sub.subscription_id,
                state=DeliveryState.DROPPED,
                error_category=f"Dropped[{sub.backpressure_policy.value}]",
                diagnostic_id=diag_id,
            )
            outcomes.append(dropped_outcome)
            self._resolve_waiters(event_id_str, sub.subscription_id, dropped_outcome)
        else:  # REJECTED
            self._metrics.record_rejected()
            diag_id = f"ERR-REJ-{uuid4().hex[:8].upper()}"
            rej_category = (
                "QueueFull"
                if isinstance(exc, QueueFullError)
                else "QueueClosed"
                if isinstance(exc, QueueClosedError)
                else "PublishRejected"
            )
            rejected_outcome = DeliveryOutcome.create(
                event_id=event_id_str,
                subscription_id=sub.subscription_id,
                state=DeliveryState.REJECTED,
                error_category=rej_category,
                diagnostic_id=diag_id,
            )
            outcomes.append(rejected_outcome)
            self._resolve_waiters(event_id_str, sub.subscription_id, rejected_outcome)

    async def publish(
        self,
        event: EventEnvelope[Any],
        priority: EventPriority = EventPriority.NORMAL,
    ) -> list[DeliveryOutcome]:
        """Publish an event to all matching subscribers asynchronously.

        Multi-Subscriber Fairness:
        When any matching subscriber is saturated under WAIT policy, enqueues concurrently
        using asyncio.gather to avoid head-of-line blocking for other subscribers.
        For unsaturated subscribers, enqueues synchronously without task scheduling latency.

        Returns immediate list of DeliveryOutcome records (QUEUED, REJECTED, or DROPPED).
        """
        start_ts = time.monotonic()

        if not isinstance(event, EventEnvelope):
            raise InvalidEventError(
                f"Expected EventEnvelope instance, received {type(event).__name__}."
            )

        if self._state != EventBusLifecycleState.RUNNING:
            self._metrics.record_rejected()
            raise EventBusNotRunningError(
                f"Cannot publish event while Event Bus is in state '{self._state.value}'."
            )

        self._metrics.record_published()
        event_id_str = str(event.event_id)

        # Snapshot-based routing
        subscribers = self._router.get_subscribers(event.event_type)

        if not subscribers:
            self._metrics.record_accepted()
            latency_ms = (time.monotonic() - start_ts) * 1000.0
            self._metrics.record_publish_latency(latency_ms)
            return [
                DeliveryOutcome.create(
                    event_id=event_id_str,
                    subscription_id=None,
                    state=DeliveryState.ACCEPTED,
                    duration_ms=latency_ms,
                )
            ]

        outcomes: list[DeliveryOutcome] = []
        has_waiting_sub = any(
            sub.queue.is_full() and sub.backpressure_policy == BackpressurePolicy.WAIT
            for sub in subscribers
        )

        if not has_waiting_sub:
            for sub in subscribers:
                try:
                    put_res = await sub.queue.put(
                        item=event,
                        priority=priority,
                        policy=sub.backpressure_policy,
                        timeout=self._config.publish_timeout_seconds,
                    )
                    self._record_publish_outcome(
                        event_id_str, sub, put_res.state, put_res.evicted_item, None, outcomes
                    )
                except Exception as pub_exc:
                    self._record_publish_outcome(
                        event_id_str, sub, DeliveryState.REJECTED, None, pub_exc, outcomes
                    )
        else:

            async def _enqueue_sub(
                sub: Subscription,
            ) -> tuple[Subscription, DeliveryState, Any | None, Exception | None]:
                try:
                    put_res = await sub.queue.put(
                        item=event,
                        priority=priority,
                        policy=sub.backpressure_policy,
                        timeout=self._config.publish_timeout_seconds,
                    )
                    return (sub, put_res.state, put_res.evicted_item, None)
                except Exception as e:
                    return (sub, DeliveryState.REJECTED, None, e)

            results = await asyncio.gather(*[_enqueue_sub(s) for s in subscribers])
            for sub, state, evicted, enqueue_exc in results:
                self._record_publish_outcome(
                    event_id_str, sub, state, evicted, enqueue_exc, outcomes
                )

        latency_ms = (time.monotonic() - start_ts) * 1000.0
        self._metrics.record_publish_latency(latency_ms)
        return outcomes

    async def publish_and_wait(
        self,
        event: EventEnvelope[Any],
        priority: EventPriority = EventPriority.NORMAL,
        timeout: float | None = None,
    ) -> list[DeliveryOutcome]:
        """Publish an event and wait for all matching subscribers to complete terminal delivery.

        Guarantees:
        - Creates dedicated completion futures per subscriber delivery.
        - Resolves waiters on all terminal outcomes (DELIVERED, FAILED, DROPPED, etc.).
        - Eliminates key collisions and indefinite hanging.
        - Returns actual subscriber-level terminal DeliveryOutcome records.
        """
        if not isinstance(event, EventEnvelope):
            raise InvalidEventError(
                f"Expected EventEnvelope instance, received {type(event).__name__}."
            )

        if self._state != EventBusLifecycleState.RUNNING:
            self._metrics.record_rejected()
            raise EventBusNotRunningError(
                f"Cannot publish event while Event Bus is in state '{self._state.value}'."
            )

        subscribers = self._router.get_subscribers(event.event_type)
        if not subscribers:
            return await self.publish(event, priority=priority)

        event_id_str = str(event.event_id)
        loop = asyncio.get_running_loop()
        futures: list[tuple[Subscription, asyncio.Future[DeliveryOutcome]]] = []

        for sub in subscribers:
            fut = loop.create_future()
            self._register_waiter(event_id_str, sub.subscription_id, fut)
            futures.append((sub, fut))

        # Start enqueuing
        await self.publish(event, priority=priority)

        # Wait for all subscriber delivery futures to resolve
        wait_timeout = timeout if timeout is not None else self._config.handler_timeout_seconds
        terminal_outcomes: list[DeliveryOutcome] = []

        for sub, fut in futures:
            try:
                if wait_timeout > 0:
                    outcome = await asyncio.wait_for(fut, timeout=wait_timeout)
                else:
                    outcome = await fut
                terminal_outcomes.append(outcome)
            except asyncio.TimeoutError:
                diag_id = f"ERR-TO-{uuid4().hex[:8].upper()}"
                terminal_outcomes.append(
                    DeliveryOutcome.create(
                        event_id=event_id_str,
                        subscription_id=sub.subscription_id,
                        state=DeliveryState.FAILED,
                        error_category="HandlerTimeout",
                        diagnostic_id=diag_id,
                    )
                )
            except asyncio.CancelledError:
                diag_id = f"ERR-CAN-{uuid4().hex[:8].upper()}"
                terminal_outcomes.append(
                    DeliveryOutcome.create(
                        event_id=event_id_str,
                        subscription_id=sub.subscription_id,
                        state=DeliveryState.CANCELLED,
                        error_category="HandlerCancelled",
                        diagnostic_id=diag_id,
                    )
                )
            finally:
                # Clean up future from waiter registry
                key = (event_id_str, sub.subscription_id)
                if key in self._delivery_waiters:
                    self._delivery_waiters[key] = [
                        f for f in self._delivery_waiters[key] if f is not fut
                    ]
                    if not self._delivery_waiters[key]:
                        del self._delivery_waiters[key]

        return terminal_outcomes

    def get_metrics(self) -> EventBusMetricsSnapshot:
        """Retrieve an immutable snapshot of operational metrics."""
        active_subs = self._router.subscription_count()
        active_workers = len([w for w in self._workers if not w.done()])

        total_queue_depth = sum(sub.queue.qsize() for sub in self._router.get_all_subscribers())

        return self._metrics.snapshot(
            active_subscriptions=active_subs,
            active_workers=active_workers,
            current_queue_depth=total_queue_depth,
        )
