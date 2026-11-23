"""Universal typed data contracts and event envelopes for OVIC EON.

Provides standardized Pydantic v2 data models for observations, emotion estimates,
interaction context, safety advisories, and component health monitoring.
"""

from typing import Final

from eon.schemas.base import EonBaseModel
from eon.schemas.common import (
    ConfidenceScore,
    DataClassification,
    ModalityType,
    Provenance,
    QualityStatus,
    UncertaintyScore,
)
from eon.schemas.context import (
    EnvironmentContext,
    InteractionContextPayload,
    InteractionStage,
    ParticipantContext,
)
from eon.schemas.emotions import (
    ArousalScore,
    DiscreteEmotionScore,
    DominanceScore,
    EmotionEstimatePayload,
    PrimaryEmotionCategory,
    ValenceScore,
)
from eon.schemas.events import (
    ComponentHealthEvent,
    ContextUpdateEvent,
    EmotionEstimateEvent,
    EventEnvelope,
    EventMetadata,
    EventType,
    ObservationEvent,
    SafetyAdvisoryEvent,
)
from eon.schemas.health import (
    ComponentHealthPayload,
    ComponentStatus,
    HealthState,
)
from eon.schemas.identifiers import (
    CausationId,
    CorrelationId,
    EventId,
    SchemaId,
    SessionId,
    SourceId,
    generate_causation_id,
    generate_correlation_id,
    generate_event_id,
    generate_session_id,
)
from eon.schemas.observations import (
    AudioObservationData,
    BehaviourObservationData,
    EnvironmentalObservationData,
    ObservationPayload,
    TextObservationData,
    VisualObservationData,
)
from eon.schemas.safety import (
    SafetyAdvisoryLevel,
    SafetyAdvisoryPayload,
    ValidationResultPayload,
)
from eon.schemas.serialization import (
    deserialize_event,
    deserialize_from_dict,
    deserialize_from_json,
    serialize_to_dict,
    serialize_to_json,
)
from eon.schemas.timestamps import (
    UtcTimestamp,
    ensure_utc_datetime,
    format_iso8601,
    utc_now,
)
from eon.schemas.versioning import (
    CURRENT_SCHEMA_VERSION,
    SUPPORTED_SCHEMA_VERSIONS,
    SchemaVersion,
    validate_schema_version,
)

__all__: Final[list[str]] = [
    # Base
    "EonBaseModel",
    # Common
    "ConfidenceScore",
    "UncertaintyScore",
    "ModalityType",
    "DataClassification",
    "QualityStatus",
    "Provenance",
    # Versioning
    "SchemaVersion",
    "CURRENT_SCHEMA_VERSION",
    "SUPPORTED_SCHEMA_VERSIONS",
    "validate_schema_version",
    # Identifiers
    "EventId",
    "CorrelationId",
    "CausationId",
    "SessionId",
    "SourceId",
    "SchemaId",
    "generate_event_id",
    "generate_correlation_id",
    "generate_causation_id",
    "generate_session_id",
    # Timestamps
    "UtcTimestamp",
    "utc_now",
    "ensure_utc_datetime",
    "format_iso8601",
    # Events
    "EventType",
    "EventMetadata",
    "EventEnvelope",
    "ObservationEvent",
    "EmotionEstimateEvent",
    "ContextUpdateEvent",
    "SafetyAdvisoryEvent",
    "ComponentHealthEvent",
    # Observations
    "ObservationPayload",
    "VisualObservationData",
    "AudioObservationData",
    "TextObservationData",
    "BehaviourObservationData",
    "EnvironmentalObservationData",
    # Emotions
    "EmotionEstimatePayload",
    "PrimaryEmotionCategory",
    "DiscreteEmotionScore",
    "ValenceScore",
    "ArousalScore",
    "DominanceScore",
    # Context
    "InteractionContextPayload",
    "ParticipantContext",
    "EnvironmentContext",
    "InteractionStage",
    # Safety
    "SafetyAdvisoryPayload",
    "SafetyAdvisoryLevel",
    "ValidationResultPayload",
    # Health
    "ComponentHealthPayload",
    "HealthState",
    "ComponentStatus",
    # Serialization
    "serialize_to_json",
    "serialize_to_dict",
    "deserialize_from_json",
    "deserialize_from_dict",
    "deserialize_event",
]
