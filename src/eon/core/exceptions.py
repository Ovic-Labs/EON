"""Core exceptions for OVIC EON runtime and event bus."""


class EonCoreError(Exception):
    """Base exception for all OVIC EON Core Runtime errors."""


class EventBusError(EonCoreError):
    """Base exception for all Event Bus operational errors."""


class EventBusNotRunningError(EventBusError):
    """Raised when publishing or subscribing while the event bus is not in RUNNING state."""


class EventBusAlreadyRunningError(EventBusError):
    """Raised when attempting to start an already running event bus without idempotent guard."""


class InvalidLifecycleTransitionError(EventBusError):
    """Raised when an illegal lifecycle state transition is requested."""


class SubscriptionError(EventBusError):
    """Base exception for subscriber management errors."""


class DuplicateSubscriptionError(SubscriptionError):
    """Raised when registering an identical subscription or conflicting subscription ID."""


class SubscriptionNotFoundError(SubscriptionError):
    """Raised when attempting to unsubscribe or access a non-existent subscription ID."""


class QueueFullError(EventBusError):
    """Raised when an event cannot be enqueued under REJECT backpressure policy."""


class EventRejectedError(EventBusError):
    """Raised when an event is rejected during publishing or dispatch."""


class DeliveryTimeoutError(EventBusError):
    """Raised when a subscriber handler execution exceeds the configured timeout boundary."""


class HandlerExecutionError(EventBusError):
    """Raised when a subscriber handler raises an unhandled exception during dispatch."""


class InvalidEventError(EventBusError):
    """Raised when an object submitted to publish is not a valid EventEnvelope instance."""
