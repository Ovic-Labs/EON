"""Tests for true oldest-event eviction in SubscriberQueue under DROP_OLDEST."""

import pytest

from eon.core.backpressure import BackpressurePolicy
from eon.core.delivery import DeliveryState
from eon.core.priority import EventPriority
from eon.core.queue_manager import SubscriberQueue


@pytest.mark.asyncio
async def test_true_oldest_eviction_mixed_priorities() -> None:
    """Verify DROP_OLDEST evicts oldest sequence item, NOT highest priority item at heap head."""
    # Capacity 3
    q = SubscriberQueue(capacity=3, name="evict_test")

    # Item 1: HIGH priority (seq 1, timestamp 1)
    await q.put("item1_high", priority=EventPriority.HIGH, policy=BackpressurePolicy.DROP_OLDEST)
    # Item 2: LOW priority (seq 2, timestamp 2)
    await q.put("item2_low", priority=EventPriority.LOW, policy=BackpressurePolicy.DROP_OLDEST)
    # Item 3: CRITICAL priority (seq 3, timestamp 3)
    await q.put(
        "item3_critical", priority=EventPriority.CRITICAL, policy=BackpressurePolicy.DROP_OLDEST
    )

    assert q.qsize() == 3
    assert q.is_full()

    # Now enqueue Item 4 under DROP_OLDEST
    # Oldest item is Item 1 ("item1_high", seq 1)
    # Even though "item3_critical" or "item1_high" has higher priority than "item2_low",
    # the OLDEST sequence is "item1_high"!
    state = await q.put(
        "item4_normal", priority=EventPriority.NORMAL, policy=BackpressurePolicy.DROP_OLDEST
    )
    assert state == DeliveryState.QUEUED

    # Pop last evicted item
    evicted = q.pop_last_evicted()
    assert evicted == "item1_high", f"Expected oldest item 'item1_high' evicted, got {evicted}"

    # Verify task accounting is balanced
    assert q.unfinished_tasks == 3
    assert q.qsize() == 3

    # Now dequeue all items and verify order
    p1, it1 = await q.get()
    q.task_done()
    p2, it2 = await q.get()
    q.task_done()
    p3, it3 = await q.get()
    q.task_done()

    # Remaining in queue: item3_critical (CRITICAL), item4_normal (NORMAL), item2_low (LOW)
    assert it1 == "item3_critical"
    assert it2 == "item4_normal"
    assert it3 == "item2_low"
