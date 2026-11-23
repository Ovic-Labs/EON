"""Common value objects, primitive types, and enumerations for EON schemas."""

from enum import Enum
from typing import Annotated

from pydantic import Field, field_validator

from eon.schemas.base import EonBaseModel

# Normalized confidence and uncertainty scalar bounds [0.0, 1.0]
ConfidenceScore = Annotated[
    float,
    Field(
        ge=0.0,
        le=1.0,
        description="Normalized confidence score within the closed interval [0.0, 1.0].",
    ),
]

UncertaintyScore = Annotated[
    float,
    Field(
        ge=0.0,
        le=1.0,
        description="Normalized epistemic or aleatoric uncertainty within [0.0, 1.0].",
    ),
]


class ModalityType(str, Enum):
    """Supported observation modalities within the EON perceptual architecture."""

    VISUAL = "visual"
    AUDIO = "audio"
    TEXT = "text"
    BEHAVIOURAL = "behavioural"
    ENVIRONMENTAL = "environmental"
    PHYSIOLOGICAL = "physiological"
    MULTIMODAL = "multimodal"


class DataClassification(str, Enum):
    """Data sensitivity classification levels adhering to EON Privacy Specifications."""

    PUBLIC = "public"
    INTERNAL = "internal"
    SENSITIVE_BEHAVIOURAL = "sensitive_behavioural"
    RESTRICTED_BIOMETRIC_DERIVED = "restricted_biometric_derived"


class QualityStatus(str, Enum):
    """Quality and freshness indicators for observations and data payloads."""

    GOOD = "good"
    DEGRADED = "degraded"
    STALE = "stale"
    UNRELIABLE = "unreliable"
    SIMULATED = "simulated"


class Provenance(EonBaseModel):
    """Audit and origin metadata tracking the pipeline stage producing a payload.

    Ensures zero raw biometric information (e.g., face embeddings, audio waveforms)
    is ever embedded in provenance metadata.
    """

    source_id: str = Field(
        ...,
        min_length=1,
        max_length=128,
        description="Originating sensor, engine, or adapter identifier.",
    )
    engine_version: str = Field(
        default="0.1.0",
        description="Version string of the engine generating this record.",
    )
    model_name: str | None = Field(
        default=None,
        description="Name of the model or heuristic algorithm utilized.",
    )
    model_version: str | None = Field(
        default=None,
        description="Version tag of the model or algorithm.",
    )
    capture_device: str | None = Field(
        default=None,
        description="Hardware device or simulation harness producing raw signals.",
    )
    processing_stage: str | None = Field(
        default=None,
        description="Pipeline step (e.g. 'filtering', 'fusion', 'inference').",
    )

    @field_validator("source_id", "model_name", "capture_device")
    @classmethod
    def validate_no_raw_biometrics(cls, value: str | None) -> str | None:
        """Guard against raw binary/biometric string tokens appearing in provenance."""
        if value is not None and ("base64," in value or len(value) > 256):
            raise ValueError("Provenance attributes must not contain raw binary or biometric data.")
        return value
