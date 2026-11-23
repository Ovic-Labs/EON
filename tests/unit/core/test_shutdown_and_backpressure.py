"""Tests for queue closure, shutdown unblocking, and unsubscription lifecycle."""

import asyncio

import pytest

from eon.core.backpressure import BackpressurePolicy
from eon.core.event_bus import EventBus
from eon.core.exceptions import EventBusNotRunningError
from eon.schemas.common import ModalityType, Provenance
from eon.schemas.events import EventEnvelope, EventType
from eon.schemas.observations import ObservationPayload, TextObservationData


def _make_sample_event(text: str = "lifecycle test") -> EventEnvelope[ObservationPayload]:
    prov = Provenance(source_id="test.lifecycle", engine_version="0.1.0")
    payload = ObservationPayload(
        source_id="test.lifecycle",
        modality=ModalityType.TEXT,
        confidence=1.0,
        provenance=prov,
        data=TextObservationData(text=text),
    )
    return EventEnvelope(
        event_type=EventType.OBSERVATION,
        source="test.lifecycle",
        payload=payload,
    )


@pytest.mark.asyncio
async def test_shutdown_wakes_blocked_wait_publisher() -> None:
    """Verify that bus stop() immediately closes queues and wakes publishers blocked on WAIT."""
    bus = EventBus()
    await bus.start()

    async def blocking_handler(_e: EventEnvelope[ObservationPayload]) -> None:
        await asyncio.sleep(2.0)

    await bus.subscribe_async(
        EventType.OBSERVATION,
        blocking_handler,
        queue_capacity=1,
        backpressure_policy=BackpressurePolicy.WAIT,
    )

    ev1 = _make_sample_event("first")
    ev2 = _make_sample_event("second")
    ev3 = _make_sample_event("third")

    await bus.publish(ev1)
    await bus.publish(ev2)

    # Publisher for ev3 will block waiting on queue space
    publisher_completed = False
    publisher_outcomes: list[object] = []

    async def blocked_publisher() -> None:
        nonlocal publisher_completed, publisher_outcomes
        outcomes = await bus.publish(ev3)
        publisher_outcomes.extend(outcomes)
        publisher_completed = True

    pub_task = asyncio.create_task(blocked_publisher())
    await asyncio.sleep(0.02)
    assert not publisher_completed

    # Now stop the event bus with a short timeout
    # stop() MUST close queues and wake pub_task
    await bus.stop(timeout=0.1)

    await asyncio.wait_for(pub_task, timeout=0.5)
    assert publisher_completed is True


@pytest.mark.asyncio
async def test_publish_after_stop_raises_not_running() -> None:
    """Verify that publish() after stop raises EventBusNotRunningError."""
    bus = EventBus()
    await bus.start()
    await bus.stop()

    ev = _make_sample_event()
    with pytest.raises(EventBusNotRunningError):
        await bus.publish(ev)


@pytest.mark.asyncio
async def test_repeated_unsubscribe_returns_false() -> None:
    """Verify that repeated unsubscription returns False on the second call."""
    async with EventBus() as bus:

        async def dummy(_e: object) -> None:
            pass

        sub_id = await bus.subscribe_async(EventType.OBSERVATION, dummy)
        assert await bus.unsubscribe(sub_id) is True
        assert await bus.unsubscribe(sub_id) is False


@pytest.mark.asyncio
async def test_unsubscribe_drains_and_marks_cancelled() -> None:
    """Verify that unsubscription drains pending queue items and marks them cancelled."""
    async with EventBus() as bus:
        dispatched: list[str] = []

        async def slow_handler(e: EventEnvelope[ObservationPayload]) -> None:
            dispatched.append(str(e.event_id))
            await asyncio.sleep(0.5)

        sub_id = await bus.subscribe_async(
            EventType.OBSERVATION,
            slow_handler,
            queue_capacity=10,
        )

        ev1 = _make_sample_event("1")
        ev2 = _make_sample_event("2")
        ev3 = _make_sample_event("3")

        await bus.publish(ev1)
        await bus.publish(ev2)
        await bus.publish(ev3)

        # Unsubscribe while ev2 and ev3 are queued
        await bus.unsubscribe(sub_id)

        # Verify metrics recorded cancelled deliveries
        metrics = bus.get_metrics()
        assert metrics.cancelled_deliveries >= 1
