"""Unit tests for event priority and deterministic queue ordering."""

import time

from eon.core.priority import EventPriority, PrioritizedItem


def test_priority_enum_values() -> None:
    """Verify priority enum values are distinct and monotonically ordered."""
    assert EventPriority.LOW < EventPriority.NORMAL
    assert EventPriority.NORMAL < EventPriority.HIGH
    assert EventPriority.HIGH < EventPriority.CRITICAL


def test_prioritized_item_ordering_higher_priority_first() -> None:
    """Verify higher priority items sort before lower priority items in min-heap ordering."""
    now = time.monotonic()
    item_low = PrioritizedItem.wrap("low", EventPriority.LOW, sequence=1, timestamp=now)
    item_high = PrioritizedItem.wrap("high", EventPriority.HIGH, sequence=2, timestamp=now)
    item_critical = PrioritizedItem.wrap("crit", EventPriority.CRITICAL, sequence=3, timestamp=now)

    # In min-heap, smallest sort key is dequeued first.
    # CRITICAL (-40) < HIGH (-30) < LOW (-10)
    sorted_items = sorted([item_low, item_critical, item_high])
    assert sorted_items[0].item == "crit"
    assert sorted_items[1].item == "high"
    assert sorted_items[2].item == "low"


def test_equal_priority_fifo_sequence_ordering() -> None:
    """Verify equal priority items are ordered strictly by sequence number (FIFO)."""
    now = time.monotonic()
    item_first = PrioritizedItem.wrap("first", EventPriority.NORMAL, sequence=1, timestamp=now)
    item_second = PrioritizedItem.wrap("second", EventPriority.NORMAL, sequence=2, timestamp=now)
    item_third = PrioritizedItem.wrap("third", EventPriority.NORMAL, sequence=3, timestamp=now)

    # Shuffle and sort
    sorted_items = sorted([item_third, item_first, item_second])
    assert [i.item for i in sorted_items] == ["first", "second", "third"]
