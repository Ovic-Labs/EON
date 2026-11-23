"""Unit tests for subscriber definition and handler invocation."""

import pytest

from eon.core.backpressure import BackpressurePolicy
from eon.core.subscription import Subscription, generate_subscription_id
from eon.schemas.common import ModalityType, Provenance
from eon.schemas.events import EventEnvelope, EventType
from eon.schemas.observations import (
    ObservationPayload,
    TextObservationData,
)


def _make_dummy_event() -> EventEnvelope[ObservationPayload]:
    prov = Provenance(
        source_id="sensor.text",
        engine_version="0.1.0",
        capture_device="test_keyboard",
    )
    return EventEnvelope(
        event_type=EventType.OBSERVATION,
        source="sensor.text",
        payload=ObservationPayload(
            source_id="sensor.text",
            modality=ModalityType.TEXT,
            confidence=0.95,
            provenance=prov,
            data=TextObservationData(text="hello test"),
        ),
    )


@pytest.mark.asyncio
async def test_subscription_creation_and_async_handler_invoke() -> None:
    """Verify Subscription invokes async coroutine handlers properly."""
    invoked: list[str] = []

    async def my_handler(event: EventEnvelope[ObservationPayload]) -> None:
        invoked.append(event.source)

    sub = Subscription(
        subscription_id=generate_subscription_id(),
        event_type="eon.observation",
        handler=my_handler,
        name="test_async_sub",
        backpressure_policy=BackpressurePolicy.WAIT,
        queue_capacity=100,
        timeout_seconds=2.0,
    )

    ev = _make_dummy_event()
    await sub.invoke_handler(ev)
    assert invoked == ["sensor.text"]


@pytest.mark.asyncio
async def test_subscription_sync_handler_invoke() -> None:
    """Verify Subscription also handles synchronous callable handlers cleanly."""
    invoked: list[str] = []

    def sync_handler(event: EventEnvelope[ObservationPayload]) -> None:
        invoked.append(event.source)

    sub = Subscription(
        subscription_id=generate_subscription_id(),
        event_type="eon.observation",
        handler=sync_handler,
        name="test_sync_sub",
        backpressure_policy=BackpressurePolicy.WAIT,
        queue_capacity=100,
        timeout_seconds=2.0,
    )

    ev = _make_dummy_event()
    await sub.invoke_handler(ev)
    assert invoked == ["sensor.text"]
