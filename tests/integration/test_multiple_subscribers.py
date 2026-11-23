"""Integration tests for multiple subscribers and routing isolation."""

import pytest

from eon.core.event_bus import EventBus
from eon.schemas.common import ModalityType, Provenance
from eon.schemas.events import EventEnvelope, EventType
from eon.schemas.observations import (
    ObservationPayload,
    TextObservationData,
)


@pytest.mark.asyncio
async def test_multiple_subscribers_independent_queues() -> None:
    """AC-1.3-06: Verify multiple subscribers receive matching events on isolated queues."""
    async with EventBus() as bus:
        sub1_events: list[str] = []
        sub2_events: list[str] = []
        sub_wild_events: list[str] = []

        async def sub1_handler(e: EventEnvelope[ObservationPayload]) -> None:
            sub1_events.append(e.source)

        async def sub2_handler(e: EventEnvelope[ObservationPayload]) -> None:
            sub2_events.append(e.source)

        async def wildcard_handler(e: EventEnvelope[ObservationPayload]) -> None:
            sub_wild_events.append(e.source)

        await bus.subscribe_async(EventType.OBSERVATION, sub1_handler, name="sub1")
        await bus.subscribe_async(EventType.OBSERVATION, sub2_handler, name="sub2")
        await bus.subscribe_async("*", wildcard_handler, name="sub_wild")

        prov = Provenance(
            source_id="multi.test",
            engine_version="0.1.0",
            capture_device="test",
        )
        payload = ObservationPayload(
            source_id="multi.test",
            modality=ModalityType.TEXT,
            confidence=0.88,
            provenance=prov,
            data=TextObservationData(text="test multiple subscribers"),
        )
        event = EventEnvelope(
            event_type=EventType.OBSERVATION,
            source="multi.test",
            payload=payload,
        )

        outcomes = await bus.publish_and_wait(event)
        # 3 subscribers matched (sub1, sub2, sub_wild)
        assert len(outcomes) == 3

        assert len(sub1_events) == 1
        assert len(sub2_events) == 1
        assert len(sub_wild_events) == 1
        assert sub1_events[0] == "multi.test"
        assert sub2_events[0] == "multi.test"
        assert sub_wild_events[0] == "multi.test"
