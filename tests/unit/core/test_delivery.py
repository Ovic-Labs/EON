"""Unit tests for delivery state tracking and outcome records."""

import datetime

from eon.core.delivery import DeliveryOutcome, DeliveryState


def test_delivery_state_enum_values() -> None:
    """Verify all delivery states exist as documented."""
    expected = {"accepted", "queued", "delivered", "failed", "rejected", "dropped", "cancelled"}
    actual = {s.value for s in DeliveryState}
    assert actual == expected


def test_delivery_outcome_creation_and_immutability() -> None:
    """Verify DeliveryOutcome creates valid immutable records with UTC timestamps."""
    outcome = DeliveryOutcome.create(
        event_id="evt-12345",
        subscription_id="sub-67890",
        state=DeliveryState.DELIVERED,
        duration_ms=1.234,
    )
    assert outcome.event_id == "evt-12345"
    assert outcome.subscription_id == "sub-67890"
    assert outcome.state == DeliveryState.DELIVERED
    assert outcome.duration_ms == 1.234
    assert outcome.timestamp.tzinfo == datetime.timezone.utc
    assert outcome.error_message is None


def test_delivery_outcome_error_sanitization() -> None:
    """Verify delivery outcome bounds error messages and does not crash on None."""
    long_error = "X" * 500
    outcome = DeliveryOutcome.create(
        event_id="evt-err",
        subscription_id="sub-err",
        state=DeliveryState.FAILED,
        duration_ms=5.0,
        error_message=long_error,
    )
    assert outcome.error_message is not None
    assert len(outcome.error_message) <= 256
