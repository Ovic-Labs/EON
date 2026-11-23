"""Tests for starvation prevention in SubscriberQueue."""

import pytest

from eon.core.priority import EventPriority
from eon.core.queue_manager import SubscriberQueue


@pytest.mark.asyncio
async def test_starvation_prevention_dispatches_lower_priority() -> None:
    """Verify lower-priority events are dispatched after starvation threshold high dispatches."""
    threshold = 3
    q = SubscriberQueue(capacity=10, name="starve_test", starvation_threshold=threshold)

    # Put 1 LOW priority item
    await q.put("low_1", priority=EventPriority.LOW)

    # Put 5 HIGH priority items
    for i in range(5):
        await q.put(f"high_{i}", priority=EventPriority.HIGH)

    dispatched_items: list[str] = []

    # Get threshold (3) items -> should all be high
    for _ in range(threshold):
        _prio, item = await q.get()
        q.task_done()
        dispatched_items.append(item)

    assert dispatched_items == ["high_0", "high_1", "high_2"]

    # Next get: threshold was reached (3 consecutive high dispatches)
    # The lower-priority item "low_1" MUST be dispatched to prevent starvation!
    _prio, next_item = await q.get()
    q.task_done()
    assert next_item == "low_1", f"Expected 'low_1' to avoid starvation, got {next_item}"

    # After starvation relief, counter is reset, so remaining high items are dispatched
    _prio, high_rem_1 = await q.get()
    q.task_done()
    assert high_rem_1 == "high_3"


@pytest.mark.asyncio
async def test_sustained_critical_traffic_does_not_starve_normal() -> None:
    """Verify sustained CRITICAL traffic dispatches NORMAL items every threshold steps."""
    threshold = 2
    q = SubscriberQueue(capacity=20, name="sustained_crit", starvation_threshold=threshold)

    # 2 Normal items
    await q.put("norm_1", priority=EventPriority.NORMAL)
    await q.put("norm_2", priority=EventPriority.NORMAL)

    # 4 Critical items
    for i in range(4):
        await q.put(f"crit_{i}", priority=EventPriority.CRITICAL)

    results: list[str] = []
    for _ in range(6):
        _prio, item = await q.get()
        q.task_done()
        results.append(item)

    # Dispatches should be: crit_0, crit_1, norm_1 (threshold relief!), crit_2, crit_3, norm_2
    assert results == ["crit_0", "crit_1", "norm_1", "crit_2", "crit_3", "norm_2"]
