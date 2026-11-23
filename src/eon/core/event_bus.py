"""High-performance, CPU-first, in-memory asynchronous Event Bus for OVIC EON."""

import asyncio
import time
from enum import Enum
from typing import Any, Final

from pydantic import Field

from eon.core.backpressure import BackpressurePolicy
from eon.core.delivery import DeliveryOutcome, DeliveryState
from eon.core.event_router import EventRouter
from eon.core.exceptions import (
    EventBusNotRunningError,
    InvalidEventError,
    InvalidLifecycleTransitionError,
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


class EventBus:
    """CPU-first, in-memory, asynchronous Event Bus for OVIC EON.

    Provides:
    - Typed event publishing accepting validated EventEnvelope data contracts.
    - Snapshot-based event routing with exact event-type and wildcard matching.
    - Isolated, bounded priority queues per subscriber with deterministic FIFO ordering.
    - Explicit backpressure policies (WAIT, REJECT, DROP_NEWEST, DROP_OLDEST).
    - Failure isolation: handler errors and timeouts never crash the bus or other subscribers.
    - Graceful lifecycle shutdown with queue draining and zero task leaks.
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
        self._completion_waiters: dict[str, asyncio.Event] = {}
        self._waiter_lock = asyncio.Lock()

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

            self._state = EventBusLifecycleState.RUNNING

            # Start workers for any existing subscriptions
            for sub in self._router.get_all_subscribers():
                self._ensure_workers(sub)

    async def stop(self, timeout: float | None = None) -> None:
        """Gracefully shut down the event bus, draining queues and stopping workers.

        Idempotent: Calling stop() on an already STOPPED bus is a safe no-op.
        """
        async with self._state_lock:
            if self._state == EventBusLifecycleState.STOPPED:
                return
            if self._state == EventBusLifecycleState.CREATED:
                self._state = EventBusLifecycleState.STOPPED
                return

            self._state = EventBusLifecycleState.STOPPING

        shutdown_timeout = timeout if timeout is not None else self._config.shutdown_timeout_seconds

        # Drain queues and wait for active handlers to complete up to timeout boundary
        all_subs = self._router.get_all_subscribers()
        if all_subs:
            drain_tasks = [sub.queue._queue.join() for sub in all_subs]
            try:
                if shutdown_timeout > 0:
                    await asyncio.wait_for(
                        asyncio.gather(*drain_tasks, return_exceptions=True),
                        timeout=shutdown_timeout,
                    )
                else:
                    await asyncio.gather(*drain_tasks, return_exceptions=True)
            except asyncio.TimeoutError:
                pass

        # Cancel all remaining worker tasks
        for worker in self._workers:
            if not worker.done():
                worker.cancel()

        if self._workers:
            await asyncio.gather(*self._workers, return_exceptions=True)
        self._workers.clear()

        # Evacuate any remaining items in queues and mark them cancelled
        for sub in all_subs:
            drained_items = sub.queue.drain()
            for _ in drained_items:
                self._metrics.record_cancelled()

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
        Returns unique SubscriptionId.
        """
        if self._state in (EventBusLifecycleState.STOPPING, EventBusLifecycleState.STOPPED):
            raise EventBusNotRunningError(
                f"Cannot subscribe when Event Bus is in state {self._state.value}."
            )

        sub_id = generate_subscription_id()
        etype_str = event_type.value if isinstance(event_type, EventType) else str(event_type)
        sub_name = name or f"sub_{etype_str}_{sub_id[:8]}"

        sub = Subscription(
            subscription_id=sub_id,
            event_type=etype_str,
            handler=handler,
            name=sub_name,
            backpressure_policy=backpressure_policy or self._config.default_backpressure_policy,
            queue_capacity=queue_capacity or self._config.default_queue_capacity,
            timeout_seconds=timeout_seconds or self._config.handler_timeout_seconds,
            max_concurrency=max_concurrency or self._config.max_workers_per_subscription,
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
        """Unregister a subscription and terminate its worker tasks."""
        try:
            sub = self._router.unregister(subscription_id)
            for w in sub.workers:
                if not w.done():
                    w.cancel()
            sub.workers.clear()
            return True
        except Exception:
            return False

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

    async def _dispatch_worker(self, sub: Subscription) -> None:
        """Isolated background worker consuming events from a subscriber queue."""
        while self._state in (EventBusLifecycleState.RUNNING, EventBusLifecycleState.STOPPING):
            try:
                # Wait for next prioritized event
                priority, event = await sub.queue.get()
            except asyncio.CancelledError:
                break

            start_time = time.monotonic()
            is_timeout = False
            error_msg: str | None = None
            try:
                # Execute subscriber handler with timeout
                await asyncio.wait_for(sub.invoke_handler(event), timeout=sub.timeout_seconds)
                delivery_state = DeliveryState.DELIVERED
            except asyncio.TimeoutError:
                is_timeout = True
                delivery_state = DeliveryState.FAILED
                error_msg = f"Handler execution timed out after {sub.timeout_seconds}s"
            except asyncio.CancelledError:
                delivery_state = DeliveryState.CANCELLED
                error_msg = "Handler task cancelled during dispatch"
                break
            except Exception as exc:
                delivery_state = DeliveryState.FAILED
                # Failure isolation: format error message without leaking sensitive payloads
                error_msg = f"Handler exception: {type(exc).__name__}: {str(exc)}"
            finally:
                duration_ms = (time.monotonic() - start_time) * 1000.0
                sub.queue.task_done()
                _outcome = DeliveryOutcome.create(
                    event_id=str(event.event_id),
                    subscription_id=sub.subscription_id,
                    state=delivery_state,
                    duration_ms=duration_ms,
                    error_message=error_msg,
                )

                # Update metrics
                if delivery_state == DeliveryState.DELIVERED:
                    self._metrics.record_delivered(duration_ms)
                elif delivery_state == DeliveryState.FAILED:
                    self._metrics.record_failed(is_timeout=is_timeout)
                elif delivery_state == DeliveryState.CANCELLED:
                    self._metrics.record_cancelled()

                # Notify any completion waiter
                waiter_key = f"{event.event_id}:{sub.subscription_id}"
                async with self._waiter_lock:
                    waiter = self._completion_waiters.get(waiter_key)
                    if waiter:
                        waiter.set()

    async def publish(
        self,
        event: EventEnvelope[Any],
        priority: EventPriority = EventPriority.NORMAL,
    ) -> list[DeliveryOutcome]:
        """Publish an event to all matching subscribers asynchronously.

        Requirements:
        - Validates that event is an instance of EventEnvelope.
        - Enforces RUNNING lifecycle state.
        - Applies configured subscriber backpressure policies.
        - Returns immediate list of DeliveryOutcome records (QUEUED, REJECTED, or DROPPED).
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
        for sub in subscribers:
            try:
                state = await sub.queue.put(
                    item=event,
                    priority=priority,
                    policy=sub.backpressure_policy,
                    timeout=self._config.publish_timeout_seconds,
                )
                if state == DeliveryState.QUEUED:
                    self._metrics.record_accepted()
                    outcomes.append(
                        DeliveryOutcome.create(
                            event_id=event_id_str,
                            subscription_id=sub.subscription_id,
                            state=DeliveryState.QUEUED,
                        )
                    )
                elif state == DeliveryState.DROPPED:
                    self._metrics.record_dropped()
                    outcomes.append(
                        DeliveryOutcome.create(
                            event_id=event_id_str,
                            subscription_id=sub.subscription_id,
                            state=DeliveryState.DROPPED,
                            error_message=(
                                f"Event dropped under {sub.backpressure_policy.value} policy"
                            ),
                        )
                    )
            except QueueFullError as e:
                self._metrics.record_rejected()
                outcomes.append(
                    DeliveryOutcome.create(
                        event_id=event_id_str,
                        subscription_id=sub.subscription_id,
                        state=DeliveryState.REJECTED,
                        error_message=str(e),
                    )
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
        """Publish an event and wait for all matching subscribers to finish processing."""
        subscribers = self._router.get_subscribers(event.event_type)
        if not subscribers:
            return await self.publish(event, priority=priority)

        event_id_str = str(event.event_id)
        waiters: list[tuple[Subscription, asyncio.Event]] = []

        async with self._waiter_lock:
            for sub in subscribers:
                ev = asyncio.Event()
                self._completion_waiters[f"{event_id_str}:{sub.subscription_id}"] = ev
                waiters.append((sub, ev))

        try:
            outcomes = await self.publish(event, priority=priority)

            # Wait for all queued subscribers to finish
            wait_timeout = timeout if timeout is not None else self._config.handler_timeout_seconds
            wait_tasks = [ev.wait() for sub, ev in waiters]

            if wait_tasks:
                if wait_timeout > 0:
                    await asyncio.wait_for(
                        asyncio.gather(*wait_tasks),
                        timeout=wait_timeout,
                    )
                else:
                    await asyncio.gather(*wait_tasks)

            return outcomes
        finally:
            async with self._waiter_lock:
                for sub, _ in waiters:
                    self._completion_waiters.pop(f"{event_id_str}:{sub.subscription_id}", None)

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
