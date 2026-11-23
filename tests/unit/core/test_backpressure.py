"""Unit tests for backpressure management policies."""

import pytest

from eon.core.backpressure import BackpressurePolicy
from eon.core.delivery import DeliveryState
from eon.core.exceptions import QueueFullError
from eon.core.queue_manager import SubscriberQueue


@pytest.mark.asyncio
async def test_backpressure_reject_policy() -> None:
    """Verify REJECT policy raises QueueFullError and updates rejected count."""
    q = SubscriberQueue(capacity=2, name="reject_q")
    await q.put("item1", policy=BackpressurePolicy.REJECT)
    await q.put("item2", policy=BackpressurePolicy.REJECT)

    with pytest.raises(QueueFullError) as exc:
        await q.put("item3", policy=BackpressurePolicy.REJECT)

    assert "is full" in str(exc.value)
    assert q.total_rejected == 1
    assert q.qsize() == 2


@pytest.mark.asyncio
async def test_backpressure_drop_newest_policy() -> None:
    """Verify DROP_NEWEST drops incoming item without raising exception."""
    q = SubscriberQueue(capacity=2, name="drop_new_q")
    await q.put("item1", policy=BackpressurePolicy.DROP_NEWEST)
    await q.put("item2", policy=BackpressurePolicy.DROP_NEWEST)

    state = await q.put("item3", policy=BackpressurePolicy.DROP_NEWEST)
    assert state == DeliveryState.DROPPED
    assert q.total_dropped == 1
    assert q.qsize() == 2

    # Verify contents remain item1 and item2
    _, first = await q.get()
    _, second = await q.get()
    assert first == "item1"
    assert second == "item2"


@pytest.mark.asyncio
async def test_backpressure_drop_oldest_policy() -> None:
    """Verify DROP_OLDEST evicts oldest queued item and inserts new item."""
    q = SubscriberQueue(capacity=2, name="drop_old_q")
    await q.put("item1", policy=BackpressurePolicy.DROP_OLDEST)
    await q.put("item2", policy=BackpressurePolicy.DROP_OLDEST)

    state = await q.put("item3", policy=BackpressurePolicy.DROP_OLDEST)
    assert state == DeliveryState.QUEUED
    assert q.total_dropped == 1
    assert q.qsize() == 2

    # Verify item1 was evicted; remaining are item2 and item3
    _, first = await q.get()
    _, second = await q.get()
    assert first == "item2"
    assert second == "item3"


@pytest.mark.asyncio
async def test_backpressure_wait_policy_timeout() -> None:
    """Verify WAIT policy raises QueueFullError when timeout expires."""
    q = SubscriberQueue(capacity=1, name="wait_q")
    await q.put("item1", policy=BackpressurePolicy.WAIT)

    with pytest.raises(QueueFullError) as exc:
        await q.put("item2", policy=BackpressurePolicy.WAIT, timeout=0.05)

    assert "saturated after" in str(exc.value)
    assert q.total_rejected == 1
