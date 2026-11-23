"""Unit tests for core event bus exceptions."""

from eon.core.exceptions import (
    DeliveryTimeoutError,
    DuplicateSubscriptionError,
    EonCoreError,
    EventBusAlreadyRunningError,
    EventBusError,
    EventBusNotRunningError,
    EventRejectedError,
    HandlerExecutionError,
    InvalidEventError,
    InvalidLifecycleTransitionError,
    QueueFullError,
    SubscriptionError,
    SubscriptionNotFoundError,
)


def test_exception_inheritance_hierarchy() -> None:
    """Verify all event bus exceptions inherit from EonCoreError and EventBusError."""
    assert issubclass(EventBusError, EonCoreError)
    assert issubclass(EventBusNotRunningError, EventBusError)
    assert issubclass(EventBusAlreadyRunningError, EventBusError)
    assert issubclass(InvalidLifecycleTransitionError, EventBusError)
    assert issubclass(SubscriptionError, EventBusError)
    assert issubclass(DuplicateSubscriptionError, SubscriptionError)
    assert issubclass(SubscriptionNotFoundError, SubscriptionError)
    assert issubclass(QueueFullError, EventBusError)
    assert issubclass(EventRejectedError, EventBusError)
    assert issubclass(DeliveryTimeoutError, EventBusError)
    assert issubclass(HandlerExecutionError, EventBusError)
    assert issubclass(InvalidEventError, EventBusError)


def test_exception_messages_preserved() -> None:
    """Verify exception messages are cleanly represented."""
    err = QueueFullError("Queue capacity exceeded 500 items")
    assert "Queue capacity exceeded 500 items" in str(err)
