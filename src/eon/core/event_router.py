"""Event routing and snapshot-based subscription matching for OVIC EON."""

from typing import Final

from eon.core.exceptions import DuplicateSubscriptionError, SubscriptionNotFoundError
from eon.core.subscription import Subscription, SubscriptionId
from eon.schemas.events import EventType

WILDCARD_EVENT_TYPE: Final[str] = "*"


class EventRouter:
    """Thread-safe and asyncio-safe event router.

    Maintains subscription registries mapped by event type.
    Provides snapshot-based routing to ensure active dispatchers operate on an
    immutable list of subscribers even if subscriptions are added or removed during dispatch.
    """

    def __init__(self) -> None:
        # event_type -> {subscription_id: Subscription}
        self._routes: dict[str, dict[SubscriptionId, Subscription]] = {}
        # index: subscription_id -> (event_type, Subscription)
        self._index: dict[SubscriptionId, tuple[str, Subscription]] = {}

    def register(self, subscription: Subscription) -> None:
        """Register a new subscription under its declared event type.

        Raises DuplicateSubscriptionError if subscription_id already exists.
        """
        sub_id = subscription.subscription_id
        if sub_id in self._index:
            raise DuplicateSubscriptionError(f"Subscription ID '{sub_id}' is already registered.")

        etype = subscription.event_type
        if etype not in self._routes:
            self._routes[etype] = {}
        self._routes[etype][sub_id] = subscription
        self._index[sub_id] = (etype, subscription)

    def unregister(self, subscription_id: SubscriptionId) -> Subscription:
        """Unregister an existing subscription by ID.

        Raises SubscriptionNotFoundError if the subscription ID does not exist.
        """
        if subscription_id not in self._index:
            raise SubscriptionNotFoundError(f"Subscription ID '{subscription_id}' not found.")

        etype, sub = self._index.pop(subscription_id)
        if etype in self._routes and subscription_id in self._routes[etype]:
            del self._routes[etype][subscription_id]
            if not self._routes[etype]:
                del self._routes[etype]

        sub.is_active = False
        return sub

    def get_subscribers(self, event_type: str | EventType) -> list[Subscription]:
        """Return an immutable snapshot of subscribers matching the given event type.

        Matches exact event type plus any wildcard ('*') subscribers.
        Returns a shallow copy list so callers can safely iterate during dispatch.
        """
        key = event_type.value if isinstance(event_type, EventType) else str(event_type)
        matching: list[Subscription] = []

        # Exact match subscribers
        exact_map = self._routes.get(key)
        if exact_map:
            matching.extend(exact_map.values())

        # Wildcard match subscribers
        if key != WILDCARD_EVENT_TYPE:
            wildcard_map = self._routes.get(WILDCARD_EVENT_TYPE)
            if wildcard_map:
                matching.extend(wildcard_map.values())

        # Filter out deactivated subscriptions
        return [s for s in matching if s.is_active]

    def get_all_subscribers(self) -> list[Subscription]:
        """Return an immutable snapshot of all currently active subscribers."""
        return [sub for _, sub in self._index.values() if sub.is_active]

    def get_subscription(self, subscription_id: SubscriptionId) -> Subscription | None:
        """Retrieve a registered subscription by ID, or None if not found."""
        entry = self._index.get(subscription_id)
        return entry[1] if entry else None

    def subscription_count(self) -> int:
        """Total number of active subscriptions registered."""
        return len(self._index)

    def event_types_registered(self) -> list[str]:
        """List of all event types with at least one active subscription."""
        return list(self._routes.keys())

    def clear(self) -> list[Subscription]:
        """Clear all registered routes and return the evacuated subscriptions."""
        evacuated = [sub for _, sub in self._index.values()]
        for sub in evacuated:
            sub.is_active = False
        self._routes.clear()
        self._index.clear()
        return evacuated
