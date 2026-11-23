"""Unit tests for event routing and subscription matching."""

import pytest

from eon.core.backpressure import BackpressurePolicy
from eon.core.event_router import WILDCARD_EVENT_TYPE, EventRouter
from eon.core.exceptions import DuplicateSubscriptionError, SubscriptionNotFoundError
from eon.core.subscription import Subscription
from eon.schemas.events import EventType


def _make_sub(sub_id: str, event_type: str) -> Subscription:
    async def dummy(e: object) -> None:
        pass

    return Subscription(
        subscription_id=sub_id,
        event_type=event_type,
        handler=dummy,
        name=f"sub_{sub_id}",
        backpressure_policy=BackpressurePolicy.WAIT,
        queue_capacity=50,
        timeout_seconds=1.0,
    )


def test_event_router_exact_matching() -> None:
    """Verify router matches exact event type and isolates unrelated subscribers."""
    router = EventRouter()
    sub_obs = _make_sub("sub-1", "eon.observation")
    sub_emo = _make_sub("sub-2", "eon.emotion_estimate")

    router.register(sub_obs)
    router.register(sub_emo)

    # Route to observation
    obs_matches = router.get_subscribers(EventType.OBSERVATION)
    assert len(obs_matches) == 1
    assert obs_matches[0].subscription_id == "sub-1"

    # Route to emotion
    emo_matches = router.get_subscribers("eon.emotion_estimate")
    assert len(emo_matches) == 1
    assert emo_matches[0].subscription_id == "sub-2"

    # Route to unmatched event
    health_matches = router.get_subscribers("eon.component_health")
    assert len(health_matches) == 0


def test_event_router_wildcard_matching() -> None:
    """Verify wildcard '*' subscriber receives all event types."""
    router = EventRouter()
    sub_wildcard = _make_sub("sub-wild", WILDCARD_EVENT_TYPE)
    sub_obs = _make_sub("sub-obs", "eon.observation")

    router.register(sub_wildcard)
    router.register(sub_obs)

    # Observation matches both exact and wildcard
    obs_matches = router.get_subscribers("eon.observation")
    assert len(obs_matches) == 2
    matched_ids = {s.subscription_id for s in obs_matches}
    assert matched_ids == {"sub-wild", "sub-obs"}

    # Emotion matches wildcard only
    emo_matches = router.get_subscribers("eon.emotion_estimate")
    assert len(emo_matches) == 1
    assert emo_matches[0].subscription_id == "sub-wild"


def test_event_router_duplicate_and_not_found_errors() -> None:
    """Verify router raises appropriate exceptions on duplicate or missing subscriptions."""
    router = EventRouter()
    sub1 = _make_sub("sub-dup", "eon.observation")
    router.register(sub1)

    # Duplicate registration raises DuplicateSubscriptionError
    with pytest.raises(DuplicateSubscriptionError):
        router.register(sub1)

    # Unregister unknown ID raises SubscriptionNotFoundError
    with pytest.raises(SubscriptionNotFoundError):
        router.unregister("non-existent-id")

    # Successful unregister
    unregistered = router.unregister("sub-dup")
    assert unregistered.subscription_id == "sub-dup"
    assert not unregistered.is_active
    assert router.subscription_count() == 0


def test_event_router_clear_and_event_types_registered() -> None:
    """Verify clear() and event_types_registered() methods."""
    router = EventRouter()
    sub1 = _make_sub("sub-1", "eon.observation")
    sub2 = _make_sub("sub-2", "eon.emotion_estimate")
    router.register(sub1)
    router.register(sub2)

    registered = router.event_types_registered()
    assert "eon.observation" in registered
    assert "eon.emotion_estimate" in registered

    evacuated = router.clear()
    assert len(evacuated) == 2
    assert router.subscription_count() == 0
