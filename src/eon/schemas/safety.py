"""Safety advisory and validation status contracts.

CRITICAL ARCHITECTURAL BOUNDARY:
OVIC EON is an affective intelligence and communication layer, NOT a certified
robot safety controller (ISO 13849 / ISO 10218). EON never exercises direct
motion authority, emergency stop control, or motor torque overrides.
"""

from enum import Enum

from pydantic import Field, field_validator

from eon.schemas.base import EonBaseModel
from eon.schemas.common import QualityStatus
from eon.schemas.identifiers import EventId, generate_event_id


class SafetyAdvisoryLevel(str, Enum):
    """Graduated advisory levels communicating social and contextual warnings.

    These are informational cues provided to the host platform. They are not
    direct motor cutoffs or PLC commands.
    """

    INFO = "info"
    ADVISORY_CAUTION = "advisory_caution"
    ADVISORY_PAUSE = "advisory_pause"
    ADVISORY_DISENGAGE = "advisory_disengage"


class SafetyAdvisoryPayload(EonBaseModel):
    """Safety and behavioral advisory cue provided to the host robotics controller."""

    advisory_id: EventId = Field(
        default_factory=generate_event_id,
        description="Unique UUID4 identifier for this advisory notification.",
    )
    level: SafetyAdvisoryLevel = Field(
        ...,
        description="Severity level of the advisory recommendation.",
    )
    advisory_code: str = Field(
        ...,
        min_length=1,
        max_length=64,
        description="Alphanumeric advisory category code (e.g. 'ADV_PROXIMITY_OVERRUN').",
    )
    human_readable_message: str = Field(
        ...,
        min_length=1,
        max_length=512,
        description="Human-readable explanation of the detected situation.",
    )
    reason: str = Field(
        ...,
        min_length=1,
        max_length=1024,
        description="Detailed causal explanation of the advisory trigger.",
    )
    recommended_action: str = Field(
        ...,
        min_length=1,
        max_length=512,
        description="Recommended behavioral adjustment (e.g. 'Cease conversational overtures').",
    )
    is_authoritative_stop: bool = Field(
        default=False,
        description="Must always be False. EON does not possess hardware E-stop authority.",
    )
    authority_boundary_disclaimer: str = Field(
        default=(
            "Informational advisory cue only. Host robot safety PLC and hardware "
            "emergency stop retain sole motion authority."
        ),
        description="Non-negotiable architectural authority boundary disclaimer.",
    )

    @field_validator("is_authoritative_stop")
    @classmethod
    def validate_no_authoritative_stop(cls, value: bool) -> bool:
        """Enforce that EON never claims authoritative motion or safety control."""
        if value is not False:
            raise ValueError(
                "EON cannot claim authoritative stop authority. "
                "is_authoritative_stop must always be False."
            )
        return value

    @field_validator("authority_boundary_disclaimer")
    @classmethod
    def validate_disclaimer_preserved(cls, value: str) -> str:
        """Ensure the safety authority boundary disclaimer is strictly preserved."""
        if not value or len(value.strip()) < 15:
            raise ValueError("Safety authority boundary disclaimer must be preserved.")
        return value


class ValidationResultPayload(EonBaseModel):
    """Result of schema or runtime payload validation."""

    target_id: str = Field(
        ...,
        min_length=1,
        max_length=128,
        description="Identifier of the payload, event, or schema evaluated.",
    )
    is_valid: bool = Field(
        ...,
        description="Whether the target conformed to all validation rules.",
    )
    rejection_reasons: list[str] = Field(
        default_factory=list,
        description="Collection of specific validation failure explanations.",
    )
    data_freshness_status: QualityStatus = Field(
        default=QualityStatus.GOOD,
        description="Quality and freshness evaluation of the validated payload.",
    )
