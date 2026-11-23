"""Unit tests for bounded subscriber queue and priority scheduling."""

import pytest

from eon.core.backpressure import BackpressurePolicy
from eon.core.delivery import DeliveryState
from eon.core.priority import EventPriority
from eon.core.queue_manager import SubscriberQueue


@pytest.mark.asyncio
async def test_queue_capacity_enforced() -> None:
    """Verify queue accepts items up to capacity and reports depth correctly."""
    q = SubscriberQueue(capacity=3, name="test_queue")
    assert q.capacity == 3
    assert q.qsize() == 0
    assert not q.is_full()

    # Enqueue 3 items
    for i in range(3):
        state = await q.put(
            f"item_{i}", priority=EventPriority.NORMAL, policy=BackpressurePolicy.REJECT
        )
        assert state == DeliveryState.QUEUED

    assert q.qsize() == 3
    assert q.is_full()
    assert q.max_observed_depth == 3


@pytest.mark.asyncio
async def test_queue_priority_and_fifo_order() -> None:
    """Verify queue dequeues higher priority first, with FIFO order for equal priority."""
    q = SubscriberQueue(capacity=10, name="priority_queue")

    # Enqueue mixed priorities
    await q.put("low_1", priority=EventPriority.LOW)
    await q.put("high_1", priority=EventPriority.HIGH)
    await q.put("norm_1", priority=EventPriority.NORMAL)
    await q.put("high_2", priority=EventPriority.HIGH)
    await q.put("crit_1", priority=EventPriority.CRITICAL)

    # Dequeue and verify order: crit_1, high_1, high_2, norm_1, low_1
    p1, item1 = await q.get()
    assert item1 == "crit_1"
    assert p1 == EventPriority.CRITICAL

    p2, item2 = await q.get()
    assert item2 == "high_1"
    assert p2 == EventPriority.HIGH

    p3, item3 = await q.get()
    assert item3 == "high_2"
    assert p3 == EventPriority.HIGH

    p4, item4 = await q.get()
    assert item4 == "norm_1"
    assert p4 == EventPriority.NORMAL

    p5, item5 = await q.get()
    assert item5 == "low_1"
    assert p5 == EventPriority.LOW


@pytest.mark.asyncio
async def test_queue_drain() -> None:
    """Verify drain() clears all pending items from queue."""
    q = SubscriberQueue(capacity=5, name="drain_queue")
    await q.put("a")
    await q.put("b")
    await q.put("c")

    drained = q.drain()
    assert len(drained) == 3
    assert q.is_empty()


def test_queue_invalid_capacity_raises_value_error() -> None:
    """Verify non-positive capacity raises ValueError."""
    with pytest.raises(ValueError):
        SubscriberQueue(capacity=0)

    with pytest.raises(ValueError):
        SubscriberQueue(capacity=-5)
