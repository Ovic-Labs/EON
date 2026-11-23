"""Universal event envelope specification for OVIC EON."""

from enum import Enum
from typing import Generic, TypeVar

from pydantic import Field, field_validator

from eon.schemas.base import EonBaseModel
from eon.schemas.common import DataClassification
from eon.schemas.context import InteractionContextPayload
from eon.schemas.emotions import EmotionEstimatePayload
from eon.schemas.health import ComponentHealthPayload
from eon.schemas.identifiers import (
    CausationId,
    CorrelationId,
    EventId,
    SessionId,
    SourceId,
    generate_event_id,
)
from eon.schemas.observations import ObservationPayload
from eon.schemas.safety import SafetyAdvisoryPayload
from eon.schemas.timestamps import UtcTimestamp, utc_now
from eon.schemas.versioning import CURRENT_SCHEMA_VERSION, validate_schema_version

PayloadT = TypeVar("PayloadT", bound=EonBaseModel)


class EventType(str, Enum):
    """Well-known event types flowing through the EON event infrastructure."""

    OBSERVATION = "eon.observation"
    EMOTION_ESTIMATE = "eon.emotion_estimate"
    CONTEXT_UPDATE = "eon.context_update"
    SAFETY_ADVISORY = "eon.safety_advisory"
    COMPONENT_HEALTH = "eon.component_health"
    CUSTOM = "eon.custom"


class EventMetadata(EonBaseModel):
    """Tracing, causality, and correlation metadata attached to every event envelope."""

    correlation_id: CorrelationId | None = Field(
        default=None,
        description="Trace identifier connecting events belonging to an end-to-end transaction.",
    )
    causation_id: CausationId | None = Field(
        default=None,
        description="Event ID of the immediate parent event that triggered this event.",
    )
    session_id: SessionId | None = Field(
        default=None,
        description="Session identifier linking events within an ongoing user engagement.",
    )
    trace_id: str | None = Field(
        default=None,
        max_length=128,
        description="OpenTelemetry or distributed tracing span identifier.",
    )
    classification: DataClassification = Field(
        default=DataClassification.INTERNAL,
        description="Privacy sensitivity classification of the event payload.",
    )


class EventEnvelope(EonBaseModel, Generic[PayloadT]):
    """Universal typed event envelope wrapping all inter-engine and external communications."""

    event_id: EventId = Field(
        default_factory=generate_event_id,
        description="Globally unique UUID4 identifier for this event instance.",
    )
    event_type: EventType = Field(
        ...,
        description="Explicit event type enumeration classifying the payload.",
    )
    schema_version: str = Field(
        default=CURRENT_SCHEMA_VERSION,
        description="Semantic version string (SemVer 2.0.0) of the schema contract.",
    )
    source: SourceId = Field(
        ...,
        description="Dot-delimited source identifier of the producing engine or sensor.",
    )
    timestamp: UtcTimestamp = Field(
        default_factory=utc_now,
        description="Timezone-aware UTC timestamp when the event envelope was constructed.",
    )
    metadata: EventMetadata = Field(
        default_factory=EventMetadata,
        description="Tracing, correlation, and classification metadata.",
    )
    payload: PayloadT = Field(
        ...,
        description="Strongly typed payload validated against its specific model contract.",
    )

    @field_validator("schema_version")
    @classmethod
    def validate_version(cls, value: str) -> str:
        """Validate that declared schema version is recognized and supported."""
        validate_schema_version(value)
        return value


# Specific concrete event types bound to their respective payloads
ObservationEvent = EventEnvelope[ObservationPayload]
EmotionEstimateEvent = EventEnvelope[EmotionEstimatePayload]
ContextUpdateEvent = EventEnvelope[InteractionContextPayload]
SafetyAdvisoryEvent = EventEnvelope[SafetyAdvisoryPayload]
ComponentHealthEvent = EventEnvelope[ComponentHealthPayload]
