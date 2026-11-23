"""Bounded subscriber queue with priority scheduling, oldest eviction, and task accounting."""

import asyncio
import heapq
import time
from dataclasses import dataclass
from typing import Any

from eon.core.backpressure import BackpressurePolicy
from eon.core.delivery import DeliveryState
from eon.core.exceptions import QueueClosedError, QueueFullError
from eon.core.priority import EventPriority, PrioritizedItem


@dataclass(frozen=True)
class EnqueueResult:
    """Structured result of a SubscriberQueue.put() operation.

    Thread-safe and concurrency-safe: encapsulates the resulting DeliveryState
    and any evicted item directly from the originating put() call, avoiding
    shared mutable instance state.
    """

    state: DeliveryState
    evicted_item: Any | None = None

    def __eq__(self, other: object) -> bool:
        if isinstance(other, DeliveryState):
            return self.state == other
        if isinstance(other, EnqueueResult):
            return self.state == other.state and self.evicted_item == other.evicted_item
        return False

    def __iter__(self) -> Any:
        return iter((self.state, self.evicted_item))


class SubscriberQueue:
    """Asyncio-based bounded priority queue for an individual subscriber.

    Guarantees:
    - Bounded memory usage via configurable queue capacity.
    - True oldest-event eviction under DROP_OLDEST (evicts the item with lowest sequence number,
      not the highest priority item at the heap head).
    - Starvation prevention: dispatches lower-priority events after consecutive high-priority
      preemptions reach the starvation threshold.
    - Deterministic FIFO ordering among equal-priority events via monotonic sequence numbering.
    - Explicit queue closure semantics that immediately unblock waiting producers and consumers.
    - Deterministic task accounting via synchronous task_done() and non-blocking join() on closure.
    """

    def __init__(
        self,
        capacity: int,
        name: str = "default",
        starvation_threshold: int = 10,
    ) -> None:
        if capacity <= 0:
            raise ValueError(f"Queue capacity must be positive, got {capacity}")
        if starvation_threshold <= 0:
            raise ValueError(f"Starvation threshold must be positive, got {starvation_threshold}")

        self._capacity = capacity
        self._name = name
        self._starvation_threshold = starvation_threshold

        self._items: list[PrioritizedItem] = []
        self._cond = asyncio.Condition()
        self._finished = asyncio.Event()
        self._finished.set()  # Initial state: 0 unfinished tasks
        self._sequence = 0
        self._unfinished_tasks = 0
        self._is_closed = False
        self._consecutive_high_dispatches = 0

        # Telemetry counters
        self._total_enqueued = 0
        self._total_dequeued = 0
        self._total_dropped = 0
        self._total_rejected = 0
        self._max_observed_depth = 0

    @property
    def capacity(self) -> int:
        """Maximum items permitted in the bounded queue."""
        return self._capacity

    @property
    def name(self) -> str:
        """Subscriber or queue name identifier."""
        return self._name

    @property
    def is_closed(self) -> bool:
        """Check if queue has been closed for shutdown."""
        return self._is_closed

    def qsize(self) -> int:
        """Current number of items in the queue."""
        return len(self._items)

    def is_full(self) -> bool:
        """Check if queue is currently at capacity."""
        return len(self._items) >= self._capacity

    def is_empty(self) -> bool:
        """Check if queue is currently empty."""
        return len(self._items) == 0

    @property
    def max_observed_depth(self) -> int:
        """High-water mark of queue depth."""
        return self._max_observed_depth

    @property
    def total_enqueued(self) -> int:
        """Cumulative count of successfully enqueued items."""
        return self._total_enqueued

    @property
    def total_dequeued(self) -> int:
        """Cumulative count of successfully dequeued items."""
        return self._total_dequeued

    @property
    def total_dropped(self) -> int:
        """Cumulative count of dropped items (DROP_NEWEST or DROP_OLDEST)."""
        return self._total_dropped

    @property
    def total_rejected(self) -> int:
        """Cumulative count of rejected items (REJECT or closed)."""
        return self._total_rejected

    @property
    def unfinished_tasks(self) -> int:
        """Current count of unfinished queue tasks."""
        return self._unfinished_tasks

    async def put(
        self,
        item: Any,
        priority: EventPriority = EventPriority.NORMAL,
        policy: BackpressurePolicy = BackpressurePolicy.WAIT,
        timeout: float | None = None,
    ) -> EnqueueResult:
        """Enqueue an item according to priority and backpressure policy.

        Returns an EnqueueResult containing:
        - state: DeliveryState (QUEUED, REJECTED, or DROPPED)
        - evicted_item: The evicted item if DROP_OLDEST displaced an older event, else None.

        Raises:
        - QueueClosedError if queue is closed.
        - QueueFullError if queue is saturated under REJECT or timed-out WAIT policy.
        """
        async with self._cond:
            if self._is_closed:
                self._total_rejected += 1
                raise QueueClosedError(f"Cannot enqueue to closed queue '{self._name}'.")

            now_ts = time.monotonic()
            self._sequence += 1
            wrapped = PrioritizedItem.wrap(item, priority, self._sequence, now_ts)

            # Capacity available
            if len(self._items) < self._capacity:
                heapq.heappush(self._items, wrapped)
                self._total_enqueued += 1
                if self._unfinished_tasks == 0:
                    self._finished.clear()
                self._unfinished_tasks += 1
                curr_len = len(self._items)
                if curr_len > self._max_observed_depth:
                    self._max_observed_depth = curr_len
                self._cond.notify()
                return EnqueueResult(state=DeliveryState.QUEUED, evicted_item=None)

            # Queue is full: apply backpressure policy
            if policy == BackpressurePolicy.REJECT:
                self._total_rejected += 1
                raise QueueFullError(
                    f"Queue '{self._name}' is full ({self._capacity} items). "
                    "Event rejected under REJECT policy."
                )

            if policy == BackpressurePolicy.DROP_NEWEST:
                self._total_dropped += 1
                return EnqueueResult(state=DeliveryState.DROPPED, evicted_item=None)

            if policy == BackpressurePolicy.DROP_OLDEST:
                # True oldest eviction: evict item with smallest sequence number
                oldest_item = min(self._items, key=lambda x: x.sequence)
                self._items.remove(oldest_item)
                heapq.heapify(self._items)
                self._total_dropped += 1
                # Vacated slot is taken by new item: unfinished_tasks remains unchanged
                heapq.heappush(self._items, wrapped)
                self._total_enqueued += 1
                self._cond.notify()
                return EnqueueResult(state=DeliveryState.QUEUED, evicted_item=oldest_item.item)

            # Policy is WAIT: await capacity or closure
            wait_deadline = (time.monotonic() + timeout) if (timeout and timeout > 0) else None

            while len(self._items) >= self._capacity and not self._is_closed:
                if wait_deadline is not None:
                    remaining = wait_deadline - time.monotonic()
                    if remaining <= 0:
                        self._total_rejected += 1
                        raise QueueFullError(
                            f"Queue '{self._name}' saturated after {timeout}s under WAIT policy."
                        )
                    try:
                        await asyncio.wait_for(self._cond.wait(), timeout=remaining)
                    except asyncio.TimeoutError as e:
                        self._total_rejected += 1
                        raise QueueFullError(
                            f"Queue '{self._name}' saturated after {timeout}s under WAIT policy."
                        ) from e
                else:
                    await self._cond.wait()

            if self._is_closed:
                self._total_rejected += 1
                raise QueueClosedError(f"Queue '{self._name}' closed while publisher was waiting.")

            heapq.heappush(self._items, wrapped)
            self._total_enqueued += 1
            if self._unfinished_tasks == 0:
                self._finished.clear()
            self._unfinished_tasks += 1
            curr_len = len(self._items)
            if curr_len > self._max_observed_depth:
                self._max_observed_depth = curr_len
            self._cond.notify()
            return EnqueueResult(state=DeliveryState.QUEUED, evicted_item=None)

    async def get(self) -> tuple[EventPriority, Any]:
        """Dequeue the highest priority item (with starvation prevention for lower priorities).

        Raises QueueClosedError if queue is closed and empty.
        """
        async with self._cond:
            while len(self._items) == 0 and not self._is_closed:
                await self._cond.wait()

            if len(self._items) == 0 and self._is_closed:
                raise QueueClosedError(f"Queue '{self._name}' is closed and empty.")

            # Starvation prevention check
            if self._consecutive_high_dispatches >= self._starvation_threshold:
                lower_priority_items = [
                    x for x in self._items if -x.sort_priority < EventPriority.HIGH
                ]
                if lower_priority_items:
                    oldest_lower = min(lower_priority_items, key=lambda x: x.sequence)
                    self._items.remove(oldest_lower)
                    heapq.heapify(self._items)
                    self._consecutive_high_dispatches = 0
                    self._total_dequeued += 1
                    self._cond.notify()
                    return EventPriority(-oldest_lower.sort_priority), oldest_lower.item

            wrapped = heapq.heappop(self._items)
            self._total_dequeued += 1
            prio = EventPriority(-wrapped.sort_priority)
            if prio >= EventPriority.HIGH:
                self._consecutive_high_dispatches += 1
            else:
                self._consecutive_high_dispatches = 0

            self._cond.notify()
            return prio, wrapped.item

    def task_done(self) -> None:
        """Signal that a previously dequeued task is complete.

        Deterministic task accounting: directly decrements unfinished tasks
        and sets the finished event when the count reaches zero.
        Raises ValueError on underflow.
        """
        if self._unfinished_tasks <= 0:
            raise ValueError(
                f"task_done() called too many times: queue '{self._name}' has 0 unfinished tasks."
            )
        self._unfinished_tasks -= 1
        if self._unfinished_tasks == 0:
            self._finished.set()

    async def join(self) -> None:
        """Block until all items in the queue have been processed or queue is closed."""
        if self._unfinished_tasks > 0 and not self._is_closed:
            await self._finished.wait()

    def close(self) -> None:
        """Close the queue, immediately waking waiting producers, consumers, and joiners."""
        self._is_closed = True
        self._finished.set()  # Unblock any join() waiting on queue
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self._notify_close())
        except RuntimeError:
            pass

    async def _notify_close(self) -> None:
        async with self._cond:
            self._cond.notify_all()

    def drain(self) -> list[Any]:
        """Drain all pending items from the queue and balance unfinished tasks."""
        drained: list[Any] = []
        while self._items:
            wrapped = heapq.heappop(self._items)
            drained.append(wrapped.item)
            if self._unfinished_tasks > 0:
                self._unfinished_tasks -= 1
        if self._unfinished_tasks == 0:
            self._finished.set()
        return drained
