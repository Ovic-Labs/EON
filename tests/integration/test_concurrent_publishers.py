"""Integration tests for concurrent event publishers."""

import asyncio

import pytest

from eon.core.event_bus import EventBus
from eon.core.priority import EventPriority
from eon.schemas.common import ModalityType, Provenance
from eon.schemas.events import EventEnvelope, EventType
from eon.schemas.observations import (
    ObservationPayload,
    TextObservationData,
)


@pytest.mark.asyncio
async def test_concurrent_publishers_high_load() -> None:
    """AC-1.3-12: Verify concurrent publishers with high load without data loss."""
    async with EventBus() as bus:
        received_count = 0
        lock = asyncio.Lock()

        async def fast_handler(_e: EventEnvelope[ObservationPayload]) -> None:
            nonlocal received_count
            async with lock:
                received_count += 1

        await bus.subscribe_async(EventType.OBSERVATION, fast_handler, queue_capacity=5000)

        num_publishers = 10
        events_per_publisher = 50
        total_events = num_publishers * events_per_publisher

        async def publisher_task(pub_id: int) -> None:
            prov = Provenance(
                source_id=f"pub.{pub_id}",
                engine_version="0.1.0",
                capture_device="synthetic",
            )
            for i in range(events_per_publisher):
                payload = ObservationPayload(
                    source_id=f"pub.{pub_id}",
                    modality=ModalityType.TEXT,
                    confidence=0.9,
                    provenance=prov,
                    data=TextObservationData(text=f"event-{pub_id}-{i}"),
                )
                ev = EventEnvelope(
                    event_type=EventType.OBSERVATION,
                    source=f"pub.{pub_id}",
                    payload=payload,
                )
                await bus.publish(ev, priority=EventPriority.NORMAL)

        # Launch all concurrent publishers
        tasks = [asyncio.create_task(publisher_task(p)) for p in range(num_publishers)]
        await asyncio.gather(*tasks)

        # Await worker completion
        timeout = 5.0
        start = asyncio.get_running_loop().time()
        while received_count < total_events and (
            (asyncio.get_running_loop().time() - start) < timeout
        ):
            await asyncio.sleep(0.02)

        assert received_count == total_events
        metrics = bus.get_metrics()
        assert metrics.total_published == total_events
        assert metrics.delivered_events == total_events
        assert metrics.rejected_events == 0
        assert metrics.dropped_events == 0
