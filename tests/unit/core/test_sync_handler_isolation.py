"""Tests for synchronous handler isolation in ThreadPoolExecutor."""

import asyncio
import time

import pytest

from eon.core.delivery import DeliveryState
from eon.core.event_bus import EventBus, EventBusConfig
from eon.schemas.common import ModalityType, Provenance
from eon.schemas.events import EventEnvelope, EventType
from eon.schemas.observations import ObservationPayload, TextObservationData


def _make_sample_event(text: str = "sync isolation test") -> EventEnvelope[ObservationPayload]:
    prov = Provenance(source_id="test.sync", engine_version="0.1.0")
    payload = ObservationPayload(
        source_id="test.sync",
        modality=ModalityType.TEXT,
        confidence=1.0,
        provenance=prov,
        data=TextObservationData(text=text),
    )
    return EventEnvelope(
        event_type=EventType.OBSERVATION,
        source="test.sync",
        payload=payload,
    )


@pytest.mark.asyncio
async def test_slow_sync_handler_does_not_block_async_handlers() -> None:
    """Verify that a slow synchronous handler runs in executor without blocking async loop."""
    config = EventBusConfig(sync_executor_workers=2)
    async with EventBus(config=config) as bus:
        sync_started = asyncio.Event()
        sync_finished = asyncio.Event()
        async_timestamps: list[float] = []

        def slow_sync_handler(_event: EventEnvelope[ObservationPayload]) -> None:
            # Synchronous sleep simulates blocking I/O or CPU computation
            sync_started.set()
            time.sleep(0.1)
            sync_finished.set()

        async def fast_async_handler(_event: EventEnvelope[ObservationPayload]) -> None:
            async_timestamps.append(time.monotonic())

        await bus.subscribe_async(EventType.OBSERVATION, slow_sync_handler, name="slow_sync")
        await bus.subscribe_async(EventType.OBSERVATION, fast_async_handler, name="fast_async")

        start_time = time.monotonic()
        event = _make_sample_event("test event")
        await bus.publish(event)

        # Wait for sync handler to signal it started
        await asyncio.wait_for(sync_started.wait(), timeout=1.0)

        # Fast async handler should have run immediately while sync handler is still sleeping
        assert len(async_timestamps) == 1
        elapsed_for_async = async_timestamps[0] - start_time
        assert elapsed_for_async < 0.08, f"Async handler was blocked for {elapsed_for_async}s!"

        # Await sync handler completion
        await asyncio.wait_for(sync_finished.wait(), timeout=1.0)


@pytest.mark.asyncio
async def test_sync_handler_exception_isolation() -> None:
    """Verify that an exception in a synchronous handler does not crash the bus."""
    async with EventBus() as bus:
        async_called = False

        def failing_sync_handler(_event: EventEnvelope[ObservationPayload]) -> None:
            raise RuntimeError("Synthetic synchronous failure")

        async def healthy_async_handler(_event: EventEnvelope[ObservationPayload]) -> None:
            nonlocal async_called
            async_called = True

        await bus.subscribe_async(EventType.OBSERVATION, failing_sync_handler, name="failing_sync")
        await bus.subscribe_async(
            EventType.OBSERVATION, healthy_async_handler, name="healthy_async"
        )

        event = _make_sample_event()
        outcomes = await bus.publish_and_wait(event)

        assert len(outcomes) == 2
        states = {o.state for o in outcomes}
        assert DeliveryState.FAILED in states
        assert DeliveryState.DELIVERED in states
        assert async_called is True


@pytest.mark.asyncio
async def test_sync_handler_timeout() -> None:
    """Verify that a slow sync handler exceeding timeout produces a sanitized FAILED outcome."""
    async with EventBus() as bus:

        def very_slow_sync(_event: EventEnvelope[ObservationPayload]) -> None:
            time.sleep(0.3)

        await bus.subscribe_async(
            EventType.OBSERVATION,
            very_slow_sync,
            name="timeout_sync",
            timeout_seconds=0.05,
        )

        event = _make_sample_event()
        outcomes = await bus.publish_and_wait(event, timeout=0.5)

        assert len(outcomes) == 1
        assert outcomes[0].state == DeliveryState.FAILED
        assert outcomes[0].error_message is not None
        assert "HandlerTimeout" in outcomes[0].error_message
