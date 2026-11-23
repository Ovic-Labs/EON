"""Delivery tracking, outcome states, and diagnostic records for OVIC EON."""

import datetime
from dataclasses import dataclass
from enum import Enum


class DeliveryState(str, Enum):
    """Lifecycle states of an event delivery to a specific subscriber."""

    ACCEPTED = "accepted"
    QUEUED = "queued"
    DELIVERED = "delivered"
    FAILED = "failed"
    REJECTED = "rejected"
    DROPPED = "dropped"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class DeliveryOutcome:
    """Immutable diagnostic record of an event delivery outcome.

    Privacy Guarantee: Never contains raw observation frames, raw audio, or biometric
    embeddings. Error messages are sanitized and bounded.
    """

    event_id: str
    subscription_id: str | None
    state: DeliveryState
    timestamp: datetime.datetime
    duration_ms: float = 0.0
    error_message: str | None = None

    @classmethod
    def create(
        cls,
        event_id: str,
        subscription_id: str | None,
        state: DeliveryState,
        duration_ms: float = 0.0,
        error_message: str | None = None,
    ) -> "DeliveryOutcome":
        """Construct a delivery outcome with current UTC timestamp and sanitized error."""
        sanitized_error = None
        if error_message:
            # Bound error message length and strip potential raw dumps
            sanitized_error = error_message[:256].strip()
        return cls(
            event_id=event_id,
            subscription_id=subscription_id,
            state=state,
            timestamp=datetime.datetime.now(datetime.timezone.utc),
            duration_ms=round(duration_ms, 3),
            error_message=sanitized_error,
        )
