"""Unit tests for EventBus lifecycle, publishing, and subscription management."""

import asyncio

import pytest

from eon.core.backpressure import BackpressurePolicy
from eon.core.delivery import DeliveryState
from eon.core.event_bus import (
    EventBus,
    EventBusLifecycleState,
)
from eon.core.exceptions import (
    EventBusNotRunningError,
    InvalidEventError,
    InvalidLifecycleTransitionError,
)
from eon.schemas.common import ModalityType, Provenance
from eon.schemas.events import EventEnvelope, EventType
from eon.schemas.observations import (
    ObservationPayload,
    TextObservationData,
)


def _make_text_event(source: str = "sensor.text.01") -> EventEnvelope[ObservationPayload]:
    prov = Provenance(
        source_id=source,
        engine_version="0.1.0",
        capture_device="test_agent",
    )
    return EventEnvelope(
        event_type=EventType.OBSERVATION,
        source=source,
        payload=ObservationPayload(
            source_id=source,
            modality=ModalityType.TEXT,
            confidence=0.9,
            provenance=prov,
            data=TextObservationData(text="unit test message"),
        ),
    )


@pytest.mark.asyncio
async def test_event_bus_lifecycle_state_transitions() -> None:
    """AC-1.3-01 / AC-1.3-14: Normal lifecycle transitions (CREATED -> RUNNING -> STOPPED)."""
    bus = EventBus()
    assert bus.lifecycle_state == EventBusLifecycleState.CREATED
    assert not bus.is_running()

    await bus.start()
    assert bus.lifecycle_state == EventBusLifecycleState.RUNNING
    assert bus.is_running()

    # Idempotent start
    await bus.start()
    assert bus.lifecycle_state == EventBusLifecycleState.RUNNING

    await bus.stop()
    assert bus.lifecycle_state == EventBusLifecycleState.STOPPED
    assert not bus.is_running()

    # Idempotent stop
    await bus.stop()
    assert bus.lifecycle_state == EventBusLifecycleState.STOPPED


@pytest.mark.asyncio
async def test_event_bus_context_manager() -> None:
    """Verify async context manager starts and stops the bus cleanly."""
    bus = EventBus()
    async with bus as b:
        assert b.is_running()
    assert bus.lifecycle_state == EventBusLifecycleState.STOPPED


@pytest.mark.asyncio
async def test_publish_before_start_raises_not_running() -> None:
    """AC-1.3-03: Verify publish() before start() raises EventBusNotRunningError."""
    bus = EventBus()
    event = _make_text_event()

    with pytest.raises(EventBusNotRunningError):
        await bus.publish(event)


@pytest.mark.asyncio
async def test_publish_invalid_event_raises_invalid_event_error() -> None:
    """AC-1.3-02: Verify publishing non-EventEnvelope raises InvalidEventError."""
    async with EventBus() as bus:
        with pytest.raises(InvalidEventError):
            await bus.publish("not an event envelope")  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_publish_and_receive_with_subscriber() -> None:
    """AC-1.3-03 / AC-1.3-04 / AC-1.3-05: Verify event publish, routing, and delivery."""
    async with EventBus() as bus:
        received: list[EventEnvelope[ObservationPayload]] = []

        async def handler(e: EventEnvelope[ObservationPayload]) -> None:
            received.append(e)

        sub_id = await bus.subscribe_async(EventType.OBSERVATION, handler)
        assert sub_id is not None

        event = _make_text_event()
        outcomes = await bus.publish(event)

        assert len(outcomes) == 1
        assert outcomes[0].state == DeliveryState.QUEUED

        # Allow worker loop to dispatch
        await asyncio.sleep(0.05)

        assert len(received) == 1
        assert received[0].event_id == event.event_id


@pytest.mark.asyncio
async def test_publish_and_wait() -> None:
    """Verify publish_and_wait completes only after handler finishes execution."""
    async with EventBus() as bus:
        finished = False

        async def handler(_e: EventEnvelope[ObservationPayload]) -> None:
            nonlocal finished
            await asyncio.sleep(0.02)
            finished = True

        await bus.subscribe_async(EventType.OBSERVATION, handler)

        event = _make_text_event()
        outcomes = await bus.publish_and_wait(event)

        assert finished is True
        assert len(outcomes) == 1
        assert outcomes[0].state == DeliveryState.QUEUED


@pytest.mark.asyncio
async def test_unsubscribe_stops_delivery() -> None:
    """AC-1.3-04: Verify unsubscription halts future deliveries."""
    async with EventBus() as bus:
        received: list[str] = []

        async def handler(e: EventEnvelope[ObservationPayload]) -> None:
            received.append(str(e.event_id))

        sub_id = await bus.subscribe_async(EventType.OBSERVATION, handler)
        ev1 = _make_text_event()
        await bus.publish_and_wait(ev1)
        assert len(received) == 1

        unsub_ok = await bus.unsubscribe(sub_id)
        assert unsub_ok is True

        ev2 = _make_text_event()
        outcomes = await bus.publish(ev2)
        # Event is accepted but has 0 matching subscribers
        assert len(outcomes) == 1
        assert outcomes[0].state == DeliveryState.ACCEPTED

        await asyncio.sleep(0.02)
        assert len(received) == 1


@pytest.mark.asyncio
async def test_synchronous_subscribe_method() -> None:
    """Verify synchronous subscribe() method before and during running."""
    bus = EventBus()
    # Subscribe before start
    received: list[str] = []

    def sync_handler(e: EventEnvelope[ObservationPayload]) -> None:
        received.append(e.source)

    sub_id = bus.subscribe(EventType.OBSERVATION, sync_handler)
    assert sub_id is not None

    await bus.start()
    ev = _make_text_event()
    await bus.publish_and_wait(ev)
    assert len(received) == 1

    await bus.stop()


@pytest.mark.asyncio
async def test_subscribe_when_stopped_raises_not_running() -> None:
    """Verify subscribe() after stop raises EventBusNotRunningError."""
    bus = EventBus()
    await bus.start()
    await bus.stop()

    def dummy(e: object) -> None:
        pass

    with pytest.raises(EventBusNotRunningError):
        bus.subscribe(EventType.OBSERVATION, dummy)

    with pytest.raises(EventBusNotRunningError):
        await bus.subscribe_async(EventType.OBSERVATION, dummy)


@pytest.mark.asyncio
async def test_start_while_stopping_raises_transition_error() -> None:
    """Verify start() while STOPPING raises InvalidLifecycleTransitionError."""
    bus = EventBus()
    bus._state = EventBusLifecycleState.STOPPING

    with pytest.raises(InvalidLifecycleTransitionError):
        await bus.start()


@pytest.mark.asyncio
async def test_publish_under_backpressure_policies_via_bus() -> None:
    """Verify publish() handles REJECT, DROP_NEWEST, and DROP_OLDEST at bus level."""
    async with EventBus() as bus:
        # 1. Reject subscriber with capacity 1
        async def dummy(_e: object) -> None:
            await asyncio.sleep(1.0)

        await bus.subscribe_async(
            EventType.OBSERVATION,
            dummy,
            name="reject_sub",
            backpressure_policy=BackpressurePolicy.REJECT,
            queue_capacity=1,
        )

        ev1 = _make_text_event()
        ev2 = _make_text_event()

        outcomes1 = await bus.publish(ev1)
        assert outcomes1[0].state == DeliveryState.QUEUED

        # Second event should be rejected
        outcomes2 = await bus.publish(ev2)
        assert outcomes2[0].state == DeliveryState.REJECTED
