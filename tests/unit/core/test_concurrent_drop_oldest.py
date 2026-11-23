"""Tests for concurrent publishers with DROP_OLDEST, structured EnqueueResult, and metrics."""

import asyncio

import pytest

from eon.core.backpressure import BackpressurePolicy
from eon.core.delivery import DeliveryState
from eon.core.event_bus import EventBus
from eon.core.queue_manager import EnqueueResult, SubscriberQueue
from eon.schemas.common import ModalityType, Provenance
from eon.schemas.events import EventEnvelope, EventType
from eon.schemas.observations import ObservationPayload, TextObservationData


def _make_event(index: int) -> EventEnvelope[ObservationPayload]:
    prov = Provenance(source_id="test.evict", engine_version="0.1.0")
    payload = ObservationPayload(
        source_id="test.evict",
        modality=ModalityType.TEXT,
        confidence=1.0,
        provenance=prov,
        data=TextObservationData(text=f"event_{index}"),
    )
    return EventEnvelope(
        event_type=EventType.OBSERVATION,
        source="test.evict",
        payload=payload,
    )


@pytest.mark.asyncio
async def test_enqueue_result_structure_and_equality() -> None:
    """Verify EnqueueResult encapsulates state, evicted item, equality, and unpacking."""
    res1 = EnqueueResult(state=DeliveryState.QUEUED, evicted_item=None)
    assert res1.state == DeliveryState.QUEUED
    assert res1.evicted_item is None
    assert res1 == DeliveryState.QUEUED

    # Test unpacking
    state, evicted = res1
    assert state == DeliveryState.QUEUED
    assert evicted is None

    res2 = EnqueueResult(state=DeliveryState.QUEUED, evicted_item="old_item")
    assert res2.state == DeliveryState.QUEUED
    assert res2.evicted_item == "old_item"
    assert res2 == DeliveryState.QUEUED


@pytest.mark.asyncio
async def test_subscriber_queue_put_returns_enqueue_result() -> None:
    """Verify SubscriberQueue.put() returns structured EnqueueResult with evicted item."""
    q = SubscriberQueue(capacity=2, name="res_test")

    r1 = await q.put("item1", policy=BackpressurePolicy.DROP_OLDEST)
    assert isinstance(r1, EnqueueResult)
    assert r1.state == DeliveryState.QUEUED
    assert r1.evicted_item is None

    r2 = await q.put("item2", policy=BackpressurePolicy.DROP_OLDEST)
    assert r2.state == DeliveryState.QUEUED
    assert r2.evicted_item is None

    # Third put: triggers eviction of item1
    r3 = await q.put("item3", policy=BackpressurePolicy.DROP_OLDEST)
    assert r3.state == DeliveryState.QUEUED
    assert r3.evicted_item == "item1"


@pytest.mark.asyncio
async def test_concurrent_publishers_drop_oldest_eviction_and_metrics() -> None:
    """Verify concurrent publishers under DROP_OLDEST produce exact DROPPED outcomes."""
    capacity = 10
    n_publishers = 5
    events_per_pub = 20
    total_events = n_publishers * events_per_pub

    async with EventBus() as bus:
        # Slow handler to force queue saturation and evictions
        async def slow_consumer(_e: EventEnvelope[ObservationPayload]) -> None:
            await asyncio.sleep(0.01)

        await bus.subscribe_async(
            EventType.OBSERVATION,
            slow_consumer,
            name="slow_evict_sub",
            queue_capacity=capacity,
            backpressure_policy=BackpressurePolicy.DROP_OLDEST,
        )

        async def publisher(pub_idx: int) -> None:
            for i in range(events_per_pub):
                ev = _make_event(pub_idx * 100 + i)
                await bus.publish(ev)

        # Launch concurrent publishers
        await asyncio.gather(*[publisher(p) for p in range(n_publishers)])

        # Allow consumer to finish queued items
        await asyncio.sleep(0.3)

        metrics = bus.get_metrics()
        assert metrics.total_published == total_events
        assert metrics.accepted_events == total_events
        assert metrics.dropped_events > 0, "Expected evictions under heavy concurrent load!"
        assert (
            metrics.delivered_events + metrics.dropped_events + metrics.current_queue_depth
            == total_events
        )
