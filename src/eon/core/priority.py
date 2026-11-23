"""Priority handling and priority-based queue ordering for OVIC EON."""

from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any


class EventPriority(IntEnum):
    """Priority levels for event scheduling within the EON Core Event Bus.

    NOTE: Priority dictates scheduling precedence inside the Python runtime event loop.
    Priority does NOT confer robot motion authority, actuator control, or emergency-stop
    release. All affective and behavioral events remain strictly advisory.
    """

    LOW = 10
    NORMAL = 20
    HIGH = 30
    CRITICAL = 40


@dataclass(order=True)
class PrioritizedItem:
    """Heap-compatible wrapper ensuring deterministic priority and FIFO order.

    Python's asyncio.PriorityQueue (and heapq) is a min-heap.
    To ensure higher priority items are dequeued first, the sort key uses negative priority.
    To ensure deterministic FIFO ordering among equal-priority events and prevent
    unstable comparisons on payloads, a monotonic sequence number is included.
    """

    sort_priority: int
    sequence: int
    timestamp: float
    item: Any = field(compare=False)

    @classmethod
    def wrap(
        cls, item: Any, priority: EventPriority, sequence: int, timestamp: float
    ) -> "PrioritizedItem":
        """Wrap an arbitrary item with negative priority and sequence for min-heap dispatch."""
        return cls(
            sort_priority=-priority.value,
            sequence=sequence,
            timestamp=timestamp,
            item=item,
        )
