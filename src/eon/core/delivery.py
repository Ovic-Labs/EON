"""Delivery tracking, outcome states, and diagnostic records for OVIC EON."""

import datetime
from dataclasses import dataclass
from enum import Enum
from uuid import uuid4


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
    embeddings. Error messages are strictly sanitized into safe category descriptions
    with unique diagnostic IDs.
    """

    event_id: str
    subscription_id: str | None
    state: DeliveryState
    timestamp: datetime.datetime
    duration_ms: float = 0.0
    error_message: str | None = None
    diagnostic_id: str | None = None

    @classmethod
    def create(
        cls,
        event_id: str,
        subscription_id: str | None,
        state: DeliveryState,
        duration_ms: float = 0.0,
        error_category: str | None = None,
        diagnostic_id: str | None = None,
        error_message: str | None = None,
    ) -> "DeliveryOutcome":
        """Construct a delivery outcome with current UTC timestamp and sanitized error category."""
        diag_id = diagnostic_id
        effective_category = error_category
        if effective_category is None and error_message is not None:
            # Map legacy error_message to a safe category without leaking raw exception contents
            msg_lower = error_message.lower()
            if "timed out" in msg_lower:
                effective_category = "HandlerTimeout"
            elif "cancelled" in msg_lower:
                effective_category = "HandlerCancelled"
            elif "queue is full" in msg_lower or "rejected" in msg_lower:
                effective_category = "QueueFull"
            elif "dropped" in msg_lower:
                effective_category = "QueueDropped"
            else:
                effective_category = "HandlerException"

        sanitized_msg = None
        if effective_category:
            if diag_id is None:
                diag_id = f"ERR-{uuid4().hex[:8].upper()}"
            # Format sanitized diagnostic code and category without exposing raw exception text
            sanitized_msg = f"{effective_category} [diag_id={diag_id}]"

        return cls(
            event_id=event_id,
            subscription_id=subscription_id,
            state=state,
            timestamp=datetime.datetime.now(datetime.timezone.utc),
            duration_ms=round(duration_ms, 3),
            error_message=sanitized_msg,
            diagnostic_id=diag_id,
        )
