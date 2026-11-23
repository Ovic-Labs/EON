"""OVIC EON Core Runtime package.

Houses runtime lifecycle supervisors, monotonic in-memory event dispatching,
priority queue management, and execution context facilities.
"""

from typing import Final

from eon.core.backpressure import BackpressurePolicy
from eon.core.delivery import DeliveryOutcome, DeliveryState
from eon.core.event_bus import (
    DEFAULT_HANDLER_TIMEOUT,
    DEFAULT_PUBLISH_TIMEOUT,
    DEFAULT_QUEUE_CAPACITY,
    DEFAULT_SHUTDOWN_TIMEOUT,
    EventBus,
    EventBusConfig,
    EventBusLifecycleState,
)
from eon.core.event_router import WILDCARD_EVENT_TYPE, EventRouter
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
    QueueClosedError,
    QueueFullError,
    SubscriptionError,
    SubscriptionNotFoundError,
)
from eon.core.metrics import (
    MAX_LATENCY_SAMPLES,
    EventBusMetrics,
    EventBusMetricsSnapshot,
)
from eon.core.priority import EventPriority, PrioritizedItem
from eon.core.queue_manager import SubscriberQueue
from eon.core.subscription import (
    EventHandler,
    Subscription,
    SubscriptionId,
    generate_subscription_id,
)

__all__: Final[list[str]] = [
    # Event Bus
    "EventBus",
    "EventBusConfig",
    "EventBusLifecycleState",
    "DEFAULT_QUEUE_CAPACITY",
    "DEFAULT_PUBLISH_TIMEOUT",
    "DEFAULT_HANDLER_TIMEOUT",
    "DEFAULT_SHUTDOWN_TIMEOUT",
    # Priority
    "EventPriority",
    "PrioritizedItem",
    # Backpressure
    "BackpressurePolicy",
    # Delivery
    "DeliveryState",
    "DeliveryOutcome",
    # Subscription
    "Subscription",
    "SubscriptionId",
    "EventHandler",
    "generate_subscription_id",
    # Queue
    "SubscriberQueue",
    # Router
    "EventRouter",
    "WILDCARD_EVENT_TYPE",
    # Metrics
    "EventBusMetrics",
    "EventBusMetricsSnapshot",
    "MAX_LATENCY_SAMPLES",
    # Exceptions
    "EonCoreError",
    "EventBusError",
    "EventBusNotRunningError",
    "EventBusAlreadyRunningError",
    "InvalidLifecycleTransitionError",
    "SubscriptionError",
    "DuplicateSubscriptionError",
    "SubscriptionNotFoundError",
    "QueueFullError",
    "QueueClosedError",
    "EventRejectedError",
    "DeliveryTimeoutError",
    "HandlerExecutionError",
    "InvalidEventError",
]
