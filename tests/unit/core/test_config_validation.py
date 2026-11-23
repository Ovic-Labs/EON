"""Tests for strict configuration validation rejecting zero and negative values."""

import pytest
from pydantic import ValidationError

from eon.core.event_bus import EventBus, EventBusConfig
from eon.core.queue_manager import SubscriberQueue
from eon.schemas.events import EventType


def test_event_bus_config_rejects_non_positive_fields() -> None:
    """Verify EventBusConfig rejects zero and negative values with validation errors."""
    with pytest.raises(ValidationError):
        EventBusConfig(default_queue_capacity=0)

    with pytest.raises(ValidationError):
        EventBusConfig(default_queue_capacity=-10)

    with pytest.raises(ValidationError):
        EventBusConfig(publish_timeout_seconds=0.0)

    with pytest.raises(ValidationError):
        EventBusConfig(handler_timeout_seconds=-1.0)

    with pytest.raises(ValidationError):
        EventBusConfig(shutdown_timeout_seconds=0.0)

    with pytest.raises(ValidationError):
        EventBusConfig(max_workers_per_subscription=0)

    with pytest.raises(ValidationError):
        EventBusConfig(sync_executor_workers=0)

    with pytest.raises(ValidationError):
        EventBusConfig(starvation_threshold=0)


def test_subscriber_queue_rejects_non_positive_parameters() -> None:
    """Verify SubscriberQueue rejects zero or negative capacity and starvation threshold."""
    with pytest.raises(ValueError, match="positive"):
        SubscriberQueue(capacity=0)

    with pytest.raises(ValueError, match="positive"):
        SubscriberQueue(capacity=-5)

    with pytest.raises(ValueError, match="positive"):
        SubscriberQueue(capacity=10, starvation_threshold=0)

    with pytest.raises(ValueError, match="positive"):
        SubscriberQueue(capacity=10, starvation_threshold=-1)


def test_event_bus_subscribe_rejects_non_positive_parameters() -> None:
    """Verify EventBus.subscribe rejects zero and negative overrides with ValueError."""
    bus = EventBus()

    async def dummy(_e: object) -> None:
        pass

    with pytest.raises(ValueError, match="queue_capacity must be positive"):
        bus.subscribe(EventType.OBSERVATION, dummy, queue_capacity=0)

    with pytest.raises(ValueError, match="queue_capacity must be positive"):
        bus.subscribe(EventType.OBSERVATION, dummy, queue_capacity=-5)

    with pytest.raises(ValueError, match="timeout_seconds must be positive"):
        bus.subscribe(EventType.OBSERVATION, dummy, timeout_seconds=0.0)

    with pytest.raises(ValueError, match="timeout_seconds must be positive"):
        bus.subscribe(EventType.OBSERVATION, dummy, timeout_seconds=-1.5)

    with pytest.raises(ValueError, match="max_concurrency must be positive"):
        bus.subscribe(EventType.OBSERVATION, dummy, max_concurrency=0)

    with pytest.raises(ValueError, match="max_concurrency must be positive"):
        bus.subscribe(EventType.OBSERVATION, dummy, max_concurrency=-2)
