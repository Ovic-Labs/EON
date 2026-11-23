"""Integration tests for subscriber failure isolation and timeout boundaries."""

import asyncio

import pytest

from eon.core.event_bus import EventBus
from eon.schemas.common import ModalityType, Provenance
from eon.schemas.events import EventEnvelope, EventType
from eon.schemas.observations import (
    ObservationPayload,
    TextObservationData,
)


@pytest.mark.asyncio
async def test_subscriber_failure_isolation() -> None:
    """AC-1.3-11: Verify subscriber exceptions and timeouts do not crash the bus."""
    async with EventBus() as bus:
        healthy_processed: list[str] = []

        # Crashing subscriber
        async def failing_handler(_e: EventEnvelope[ObservationPayload]) -> None:
            raise RuntimeError("Deliberate subscriber crash simulation")

        # Timing out subscriber
        async def slow_handler(_e: EventEnvelope[ObservationPayload]) -> None:
            await asyncio.sleep(1.0)  # Exceeds 0.05s timeout

        # Healthy subscriber
        async def healthy_handler(e: EventEnvelope[ObservationPayload]) -> None:
            healthy_processed.append(e.source)

        await bus.subscribe_async(EventType.OBSERVATION, failing_handler, name="failing_sub")
        await bus.subscribe_async(
            EventType.OBSERVATION,
            slow_handler,
            name="slow_sub",
            timeout_seconds=0.05,
        )
        await bus.subscribe_async(EventType.OBSERVATION, healthy_handler, name="healthy_sub")

        prov = Provenance(
            source_id="failure.isolation.test",
            engine_version="0.1.0",
            capture_device="test",
        )
        payload = ObservationPayload(
            source_id="failure.isolation.test",
            modality=ModalityType.TEXT,
            confidence=0.9,
            provenance=prov,
            data=TextObservationData(text="testing failure isolation"),
        )
        event = EventEnvelope(
            event_type=EventType.OBSERVATION,
            source="failure.isolation.test",
            payload=payload,
        )

        # Publish event
        await bus.publish(event)

        # Wait for workers to process and timeout to trigger
        await asyncio.sleep(0.15)

        # Healthy subscriber MUST have succeeded
        assert len(healthy_processed) == 1
        assert healthy_processed[0] == "failure.isolation.test"

        # Event bus must remain alive and RUNNING
        assert bus.is_running()

        # Telemetry should reflect 1 delivered, 2 failed (1 exception + 1 timeout)
        metrics = bus.get_metrics()
        assert metrics.delivered_events == 1
        assert metrics.failed_deliveries == 2
        assert metrics.handler_timeout_count == 1
