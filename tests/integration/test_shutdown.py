"""Integration tests for graceful shutdown and task leak prevention."""

import asyncio

import pytest

from eon.core.event_bus import EventBus
from eon.core.exceptions import EventBusNotRunningError
from eon.schemas.common import ModalityType, Provenance
from eon.schemas.events import EventEnvelope, EventType
from eon.schemas.observations import (
    ObservationPayload,
    TextObservationData,
)


@pytest.mark.asyncio
async def test_shutdown_drains_queues_and_cleans_tasks() -> None:
    """AC-1.3-14: Verify stop() cleanly drains active queues without leaking worker tasks."""
    bus = EventBus()
    await bus.start()

    processed: list[str] = []

    async def slow_handler(e: EventEnvelope[ObservationPayload]) -> None:
        await asyncio.sleep(0.01)
        processed.append(e.source)

    await bus.subscribe_async(EventType.OBSERVATION, slow_handler)

    # Publish several events
    prov = Provenance(
        source_id="shutdown.test",
        engine_version="0.1.0",
        capture_device="synthetic",
    )
    for i in range(5):
        payload = ObservationPayload(
            source_id=f"shutdown.{i}",
            modality=ModalityType.TEXT,
            confidence=0.9,
            provenance=prov,
            data=TextObservationData(text=f"msg {i}"),
        )
        ev = EventEnvelope(
            event_type=EventType.OBSERVATION,
            source=f"shutdown.{i}",
            payload=payload,
        )
        await bus.publish(ev)

    # Trigger graceful shutdown
    await bus.stop(timeout=2.0)

    # Verify all 5 were processed during graceful drain
    assert len(processed) == 5

    # Verify publishing after stop is rejected
    payload = ObservationPayload(
        source_id="after.stop",
        modality=ModalityType.TEXT,
        confidence=0.9,
        provenance=prov,
        data=TextObservationData(text="should fail"),
    )
    ev_after = EventEnvelope(
        event_type=EventType.OBSERVATION,
        source="after.stop",
        payload=payload,
    )
    with pytest.raises(EventBusNotRunningError):
        await bus.publish(ev_after)

    # Verify 0 lingering active worker tasks
    assert len(bus._workers) == 0
