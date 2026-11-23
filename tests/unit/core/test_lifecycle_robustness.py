"""Tests for EventBus lifecycle robustness, terminal STOPPED state, and timeout boundaries."""

import asyncio
import time

import pytest

from eon.core.event_bus import EventBus, EventBusConfig, EventBusLifecycleState
from eon.core.exceptions import InvalidLifecycleTransitionError
from eon.schemas.common import ModalityType, Provenance
from eon.schemas.events import EventEnvelope, EventType
from eon.schemas.observations import ObservationPayload, TextObservationData


def _make_sample_event(text: str = "lifecycle test") -> EventEnvelope[ObservationPayload]:
    prov = Provenance(source_id="test.robust", engine_version="0.1.0")
    payload = ObservationPayload(
        source_id="test.robust",
        modality=ModalityType.TEXT,
        confidence=1.0,
        provenance=prov,
        data=TextObservationData(text=text),
    )
    return EventEnvelope(
        event_type=EventType.OBSERVATION,
        source="test.robust",
        payload=payload,
    )


@pytest.mark.asyncio
async def test_stop_negative_timeout_raises_value_error() -> None:
    """Verify stop() with negative timeout raises ValueError."""
    bus = EventBus()
    await bus.start()
    try:
        with pytest.raises(ValueError, match="timeout must be non-negative"):
            await bus.stop(timeout=-1.0)
    finally:
        await bus.stop()


@pytest.mark.asyncio
async def test_start_after_stopped_raises_invalid_lifecycle_transition() -> None:
    """Verify STOPPED state is terminal; calling start() after stop() raises error."""
    bus = EventBus()
    await bus.start()
    assert bus.lifecycle_state == EventBusLifecycleState.RUNNING

    await bus.stop()
    assert bus.lifecycle_state == EventBusLifecycleState.STOPPED

    with pytest.raises(InvalidLifecycleTransitionError, match="STOPPED state is terminal"):
        await bus.start()


@pytest.mark.asyncio
async def test_repeated_stop_is_safe_idempotent() -> None:
    """Verify calling stop() repeatedly on an already stopped bus is an idempotent no-op."""
    bus = EventBus()
    await bus.start()
    await bus.stop()
    assert bus.lifecycle_state == EventBusLifecycleState.STOPPED

    # Second and third stop calls must be safe no-ops
    await bus.stop()
    await bus.stop(timeout=1.0)
    assert bus.lifecycle_state == EventBusLifecycleState.STOPPED


@pytest.mark.asyncio
async def test_shutdown_respects_time_boundary_with_slow_sync_handler() -> None:
    """Verify stop(timeout=0.1) respects its documented time boundary with slow handler."""
    config = EventBusConfig(sync_executor_workers=2)
    bus = EventBus(config=config)
    await bus.start()

    sync_started = asyncio.Event()

    def very_slow_sync(_e: EventEnvelope[ObservationPayload]) -> None:
        sync_started.set()
        time.sleep(1.0)

    bus.subscribe(EventType.OBSERVATION, very_slow_sync, name="slow_sync_sub")
    event = _make_sample_event()
    await bus.publish(event)

    await asyncio.wait_for(sync_started.wait(), timeout=1.0)

    # Stop with 0.1s timeout boundary
    t0 = time.monotonic()
    await bus.stop(timeout=0.1)
    elapsed = time.monotonic() - t0

    assert bus.lifecycle_state == EventBusLifecycleState.STOPPED
    # Total shutdown elapsed time should strictly respect ~0.1s boundary
    assert elapsed < 0.35, f"Shutdown took {elapsed}s, exceeding time boundary!"


@pytest.mark.asyncio
async def test_shutdown_with_cancellation_during_drain() -> None:
    """Verify shutdown behavior when subscriber queues are drained and tasks cancelled."""
    bus = EventBus()
    await bus.start()

    received: list[str] = []

    async def normal_sub(e: EventEnvelope[ObservationPayload]) -> None:
        received.append(str(e.event_id))

    bus.subscribe(EventType.OBSERVATION, normal_sub)

    for i in range(10):
        ev = _make_sample_event(f"ev_{i}")
        await bus.publish(ev)

    await bus.stop()
    assert bus.lifecycle_state == EventBusLifecycleState.STOPPED
