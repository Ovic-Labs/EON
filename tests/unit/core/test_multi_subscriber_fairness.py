"""Tests for multi-subscriber fairness and concurrent enqueuing."""

import asyncio
import time

import pytest

from eon.core.backpressure import BackpressurePolicy
from eon.core.event_bus import EventBus
from eon.schemas.common import ModalityType, Provenance
from eon.schemas.events import EventEnvelope, EventType
from eon.schemas.observations import ObservationPayload, TextObservationData


def _make_sample_event(text: str = "fairness test") -> EventEnvelope[ObservationPayload]:
    prov = Provenance(source_id="test.fairness", engine_version="0.1.0")
    payload = ObservationPayload(
        source_id="test.fairness",
        modality=ModalityType.TEXT,
        confidence=1.0,
        provenance=prov,
        data=TextObservationData(text=text),
    )
    return EventEnvelope(
        event_type=EventType.OBSERVATION,
        source="test.fairness",
        payload=payload,
    )


@pytest.mark.asyncio
async def test_saturated_wait_subscriber_does_not_block_fast_subscriber() -> None:
    """Verify that a saturated subscriber in WAIT does not delay delivery to a healthy
    subscriber.
    """
    async with EventBus() as bus:
        fast_received: list[str] = []

        # Subscriber A: Saturated, capacity 1, WAIT policy, slow handler
        async def slow_handler(_e: EventEnvelope[ObservationPayload]) -> None:
            await asyncio.sleep(0.5)

        # Subscriber B: Healthy, capacity 10, fast handler
        async def fast_handler(e: EventEnvelope[ObservationPayload]) -> None:
            fast_received.append(str(e.event_id))

        await bus.subscribe_async(
            EventType.OBSERVATION,
            slow_handler,
            name="sub_slow",
            backpressure_policy=BackpressurePolicy.WAIT,
            queue_capacity=1,
        )
        await bus.subscribe_async(
            EventType.OBSERVATION,
            fast_handler,
            name="sub_fast",
            backpressure_policy=BackpressurePolicy.WAIT,
            queue_capacity=10,
        )

        # Publish ev1: enqueued to both, slow_handler starts processing
        ev1 = _make_sample_event("first")
        await bus.publish(ev1)

        # Publish ev2: sub_slow queue has capacity 1, takes ev2
        ev2 = _make_sample_event("second")
        await bus.publish(ev2)

        # Now sub_slow has 1 in processing and 1 in queue (saturated).
        # Publish ev3: sub_slow is full and will wait up to publish_timeout.
        # But sub_fast has ample capacity! sub_fast MUST receive ev3 immediately without waiting!
        ev3 = _make_sample_event("third")
        t0 = time.monotonic()

        # In a background task, publish ev3
        pub_task = asyncio.create_task(bus.publish(ev3))

        # Check that fast_handler received ev3 well before slow handler finishes
        await asyncio.sleep(0.05)
        assert str(ev3.event_id) in fast_received, "Fast subscriber was blocked by slow subscriber!"

        elapsed = time.monotonic() - t0
        assert elapsed < 0.2, f"Delivery to fast subscriber took too long ({elapsed}s)!"

        # Await publish completion
        await pub_task
