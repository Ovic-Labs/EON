"""Bounded subscriber queue with priority ordering and backpressure management."""

import asyncio
import time
from typing import Any

from eon.core.backpressure import BackpressurePolicy
from eon.core.delivery import DeliveryState
from eon.core.exceptions import QueueFullError
from eon.core.priority import EventPriority, PrioritizedItem


class SubscriberQueue:
    """Asyncio-based bounded priority queue for an individual subscriber.

    Enforces:
    - Bounded memory usage via configurable queue capacity.
    - Deterministic FIFO ordering among equal-priority events via monotonic sequence numbering.
    - Priority-based scheduling (higher priority events dispatched before lower priority).
    - Explicit backpressure policies (WAIT, REJECT, DROP_NEWEST, DROP_OLDEST).
    - Queue-depth tracking and saturation metrics.
    """

    def __init__(self, capacity: int, name: str = "default") -> None:
        if capacity <= 0:
            raise ValueError(f"Queue capacity must be positive, got {capacity}")
        self._capacity = capacity
        self._name = name
        self._queue: asyncio.PriorityQueue[PrioritizedItem] = asyncio.PriorityQueue(
            maxsize=capacity
        )
        self._sequence = 0
        self._lock = asyncio.Lock()

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

    def qsize(self) -> int:
        """Current number of items in the queue."""
        return self._queue.qsize()

    def is_full(self) -> bool:
        """Check if queue is currently at capacity."""
        return self._queue.full()

    def is_empty(self) -> bool:
        """Check if queue is currently empty."""
        return self._queue.empty()

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
        """Cumulative count of rejected items (REJECT)."""
        return self._total_rejected

    async def put(
        self,
        item: Any,
        priority: EventPriority = EventPriority.NORMAL,
        policy: BackpressurePolicy = BackpressurePolicy.WAIT,
        timeout: float | None = None,
    ) -> DeliveryState:
        """Enqueue an item according to priority and backpressure policy.

        Returns the resulting DeliveryState (QUEUED, REJECTED, or DROPPED).
        """
        async with self._lock:
            now_ts = time.monotonic()
            self._sequence += 1
            wrapped = PrioritizedItem.wrap(item, priority, self._sequence, now_ts)

            # Check if queue has capacity
            if not self._queue.full():
                self._queue.put_nowait(wrapped)
                self._total_enqueued += 1
                current_size = self._queue.qsize()
                if current_size > self._max_observed_depth:
                    self._max_observed_depth = current_size
                return DeliveryState.QUEUED

            # Queue is full — apply configured backpressure policy
            if policy == BackpressurePolicy.REJECT:
                self._total_rejected += 1
                raise QueueFullError(
                    f"Queue '{self._name}' is full ({self._capacity} items). "
                    "Event rejected under REJECT policy."
                )

            if policy == BackpressurePolicy.DROP_NEWEST:
                self._total_dropped += 1
                return DeliveryState.DROPPED

            if policy == BackpressurePolicy.DROP_OLDEST:
                # Evict the lowest-priority or oldest item currently in queue
                try:
                    _evicted = self._queue.get_nowait()
                    self._queue.task_done()
                    self._total_dropped += 1
                except (asyncio.QueueEmpty, ValueError):
                    pass
                self._queue.put_nowait(wrapped)
                self._total_enqueued += 1
                return DeliveryState.QUEUED

            # policy == BackpressurePolicy.WAIT
            # Release lock before awaiting to avoid blocking other operations
            pass

        # BackpressurePolicy.WAIT: Wait asynchronously for queue space
        try:
            if timeout is not None and timeout > 0:
                await asyncio.wait_for(self._queue.put(wrapped), timeout=timeout)
            else:
                await self._queue.put(wrapped)
            async with self._lock:
                self._total_enqueued += 1
                current_size = self._queue.qsize()
                if current_size > self._max_observed_depth:
                    self._max_observed_depth = current_size
            return DeliveryState.QUEUED
        except asyncio.TimeoutError as e:
            async with self._lock:
                self._total_rejected += 1
            raise QueueFullError(
                f"Queue '{self._name}' saturated after {timeout}s timeout under WAIT policy."
            ) from e

    async def get(self) -> tuple[EventPriority, Any]:
        """Dequeue the highest priority item (and oldest among equal priority)."""
        wrapped = await self._queue.get()
        async with self._lock:
            self._total_dequeued += 1
        # Reconstruct original priority from sort key
        priority = EventPriority(-wrapped.sort_priority)
        return priority, wrapped.item

    def task_done(self) -> None:
        """Signal that a previously dequeued task is complete."""
        self._queue.task_done()

    def drain(self) -> list[Any]:
        """Drain all pending items from the queue (used during shutdown)."""
        drained: list[Any] = []
        while not self._queue.empty():
            try:
                wrapped = self._queue.get_nowait()
                self._queue.task_done()
                drained.append(wrapped.item)
            except (asyncio.QueueEmpty, ValueError):
                break
        return drained
