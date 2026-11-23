"""Tests for publish_and_wait terminal outcomes and failure robustness."""

import asyncio

import pytest

from eon.core.backpressure import BackpressurePolicy
from eon.core.delivery import DeliveryState
from eon.core.event_bus import EventBus
from eon.schemas.common import ModalityType, Provenance
from eon.schemas.events import EventEnvelope, EventType
from eon.schemas.observations import ObservationPayload, TextObservationData


def _make_sample_event(text: str = "terminal outcome test") -> EventEnvelope[ObservationPayload]:
    prov = Provenance(source_id="test.terminal", engine_version="0.1.0")
    payload = ObservationPayload(
        source_id="test.terminal",
        modality=ModalityType.TEXT,
        confidence=1.0,
        provenance=prov,
        data=TextObservationData(text=text),
    )
    return EventEnvelope(
        event_type=EventType.OBSERVATION,
        source="test.terminal",
        payload=payload,
    )


@pytest.mark.asyncio
async def test_publish_and_wait_returns_delivered_outcome() -> None:
    """Verify publish_and_wait returns DELIVERED outcome on successful handler completion."""
    async with EventBus() as bus:
        received = False

        async def handler(_e: EventEnvelope[ObservationPayload]) -> None:
            nonlocal received
            await asyncio.sleep(0.01)
            received = True

        await bus.subscribe_async(EventType.OBSERVATION, handler)

        event = _make_sample_event()
        outcomes = await bus.publish_and_wait(event)

        assert received is True
        assert len(outcomes) == 1
        assert outcomes[0].state == DeliveryState.DELIVERED
        assert outcomes[0].duration_ms > 0


@pytest.mark.asyncio
async def test_publish_and_wait_returns_failed_on_exception() -> None:
    """Verify publish_and_wait resolves to FAILED when handler raises exception."""
    async with EventBus() as bus:

        async def failing_handler(_e: EventEnvelope[ObservationPayload]) -> None:
            raise ValueError("Deliberate failure")

        await bus.subscribe_async(EventType.OBSERVATION, failing_handler)

        event = _make_sample_event()
        outcomes = await bus.publish_and_wait(event)

        assert len(outcomes) == 1
        assert outcomes[0].state == DeliveryState.FAILED
        assert outcomes[0].error_message is not None
        assert "HandlerException[ValueError]" in outcomes[0].error_message


@pytest.mark.asyncio
async def test_publish_and_wait_returns_failed_on_handler_timeout() -> None:
    """Verify publish_and_wait resolves to FAILED when handler times out."""
    async with EventBus() as bus:

        async def slow_handler(_e: EventEnvelope[ObservationPayload]) -> None:
            await asyncio.sleep(0.2)

        await bus.subscribe_async(
            EventType.OBSERVATION,
            slow_handler,
            timeout_seconds=0.03,
        )

        event = _make_sample_event()
        outcomes = await bus.publish_and_wait(event)

        assert len(outcomes) == 1
        assert outcomes[0].state == DeliveryState.FAILED
        assert outcomes[0].error_message is not None
        assert "HandlerTimeout" in outcomes[0].error_message


@pytest.mark.asyncio
async def test_publish_and_wait_returns_rejected_on_full_queue() -> None:
    """Verify publish_and_wait resolves to REJECTED when queue rejects event."""
    async with EventBus() as bus:

        async def slow_handler(_e: EventEnvelope[ObservationPayload]) -> None:
            await asyncio.sleep(0.5)

        await bus.subscribe_async(
            EventType.OBSERVATION,
            slow_handler,
            queue_capacity=1,
            backpressure_policy=BackpressurePolicy.REJECT,
        )

        ev1 = _make_sample_event("ev1")
        ev2 = _make_sample_event("ev2")
        ev3 = _make_sample_event("ev3")

        # Fill queue
        await bus.publish(ev1)
        await bus.publish(ev2)

        # Now publish_and_wait for ev3: should immediately resolve to REJECTED
        outcomes = await bus.publish_and_wait(ev3)
        assert len(outcomes) == 1
        assert outcomes[0].state == DeliveryState.REJECTED
