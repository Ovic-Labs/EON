"""Interaction and session context data contracts."""

import datetime
from enum import Enum
from typing import Any

from pydantic import Field, field_validator

from eon.schemas.base import EonBaseModel
from eon.schemas.identifiers import EventId, SessionId, generate_event_id
from eon.schemas.timestamps import UtcTimestamp, utc_now


class InteractionStage(str, Enum):
    """Lifecycle stages of a human-robot social interaction."""

    INITIATION = "initiation"
    GREETING = "greeting"
    ACTIVE_DIALOGUE = "active_dialogue"
    TASK_COLLABORATION = "task_collaboration"
    PAUSE = "pause"
    TERMINATION = "termination"


class ParticipantContext(EonBaseModel):
    """Anonymized or pseudonymized participant information within the active session.

    Strictly forbids storing raw biometric features or direct personal identifiers.
    """

    participant_id: str = Field(
        ...,
        min_length=1,
        max_length=64,
        description="Pseudonymized or ephemeral session-specific participant identifier.",
    )
    role: str = Field(
        default="interactor",
        max_length=64,
        description="Role in interaction (e.g. 'primary_user', 'bystander', 'operator').",
    )
    interaction_count: int = Field(
        default=1,
        ge=0,
        description="Turn count or interaction occurrence counter within this session.",
    )


class EnvironmentContext(EonBaseModel):
    """Contextual representation of the surrounding physical and social environment."""

    location_type: str | None = Field(
        default=None,
        max_length=64,
        description="Type of environment (e.g. 'hospital_ward', 'classroom', 'domestic_living').",
    )
    noise_level: str | None = Field(
        default=None,
        max_length=32,
        description="Categorical ambient acoustic profile (e.g. 'quiet', 'moderate', 'loud').",
    )
    social_setting: str | None = Field(
        default=None,
        max_length=64,
        description="Contextual social dynamics (e.g. 'one_on_one', 'small_group', 'crowded').",
    )


class InteractionContextPayload(EonBaseModel):
    """Structured interaction context maintained across conversational and social turns."""

    context_id: EventId = Field(
        default_factory=generate_event_id,
        description="Unique UUID4 identifier for this context snapshot.",
    )
    session_id: SessionId = Field(
        ...,
        description="UUID or session slug identifying the persistent engagement session.",
    )
    participants: list[ParticipantContext] = Field(
        default_factory=list,
        description="Collection of pseudonymized participants involved in this interaction.",
    )
    environment: EnvironmentContext = Field(
        default_factory=EnvironmentContext,
        description="Current environmental context description.",
    )
    interaction_stage: InteractionStage = Field(
        default=InteractionStage.INITIATION,
        description="Current conversational stage.",
    )
    updated_at: UtcTimestamp = Field(
        default_factory=utc_now,
        description="Timezone-aware UTC timestamp when this context was last updated.",
    )
    expires_at: UtcTimestamp | None = Field(
        default=None,
        description="Optional UTC timestamp when this interaction context expires.",
    )
    metadata: dict[str, str] | None = Field(
        default=None,
        description="Optional key-value metadata strings (biometric tokens prohibited).",
    )

    @field_validator("expires_at")
    @classmethod
    def validate_expires_after_updated(
        cls, value: datetime.datetime | None, info: Any
    ) -> datetime.datetime | None:
        """Validate that expiration occurs after context update timestamp."""
        updated_at = info.data.get("updated_at")
        if value is not None and updated_at is not None and value <= updated_at:
            raise ValueError("expires_at must be chronologically after updated_at.")
        return value
