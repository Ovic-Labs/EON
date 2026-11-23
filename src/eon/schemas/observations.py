"""Structured perceptual observation contracts for OVIC EON."""

import datetime
from typing import Annotated, Any

from pydantic import Field, field_validator

from eon.schemas.base import EonBaseModel
from eon.schemas.common import ConfidenceScore, ModalityType, Provenance, QualityStatus
from eon.schemas.identifiers import EventId, SourceId, generate_event_id
from eon.schemas.timestamps import UtcTimestamp, utc_now


class VisualObservationData(EonBaseModel):
    """Derived facial and visual features extracted by perceptual pipelines.

    Strictly stores geometric, kinematic, and action unit indicators.
    Never stores raw pixel buffers or biometric identification embeddings.
    """

    face_detected: bool = Field(
        ...,
        description="Whether at least one human face was detected in the frame.",
    )
    face_bounding_box: tuple[float, float, float, float] | None = Field(
        default=None,
        description="Normalized bounding box (x_min, y_min, x_max, y_max) within [0.0, 1.0].",
    )
    head_pose_yaw: float | None = Field(
        default=None,
        ge=-180.0,
        le=180.0,
        description="Estimated head pose yaw angle in degrees.",
    )
    head_pose_pitch: float | None = Field(
        default=None,
        ge=-90.0,
        le=90.0,
        description="Estimated head pose pitch angle in degrees.",
    )
    facial_action_units: dict[str, float] | None = Field(
        default=None,
        description="FACS Action Unit activations normalized in [0.0, 1.0].",
    )


class AudioObservationData(EonBaseModel):
    """Derived prosodic and acoustic descriptors extracted from speech signals.

    Never stores raw audio PCM waveforms or voiceprint identification tokens.
    """

    speech_detected: bool = Field(
        ...,
        description="Whether human speech activity was detected in the acoustic window.",
    )
    snr_db: float | None = Field(
        default=None,
        description="Signal-to-noise ratio in decibels.",
    )
    pitch_hz: float | None = Field(
        default=None,
        ge=0.0,
        le=2000.0,
        description="Fundamental frequency (F0) estimation in Hertz.",
    )
    energy: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Normalized root-mean-square energy of the acoustic frame.",
    )
    duration_seconds: float | None = Field(
        default=None,
        gt=0.0,
        le=300.0,
        description="Duration of the analyzed audio window in seconds.",
    )


class TextObservationData(EonBaseModel):
    """Transcription or text input metadata and linguistic hints."""

    text: str = Field(
        ...,
        min_length=1,
        max_length=4096,
        description="Recognized spoken text or direct text input.",
    )
    language: str | None = Field(
        default=None,
        max_length=16,
        description="ISO 639-1 language code (e.g. 'en', 'de', 'ja').",
    )
    sentiment_hint: float | None = Field(
        default=None,
        ge=-1.0,
        le=1.0,
        description="Normalized linguistic sentiment polarity in [-1.0, 1.0].",
    )


class BehaviourObservationData(EonBaseModel):
    """Observed physical or gestural behavior descriptors."""

    action_label: str = Field(
        ...,
        min_length=1,
        max_length=128,
        description="Descriptive behavioral or gestural classification.",
    )
    movement_intensity: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Normalized kinetic energy or movement speed score [0.0, 1.0].",
    )
    gaze_direction: str | None = Field(
        default=None,
        max_length=64,
        description="Direction of gaze relative to the robot (e.g. 'direct', 'averted').",
    )
    proximity_zone: str | None = Field(
        default=None,
        max_length=64,
        description="Hall proximity zone (e.g. 'intimate', 'personal', 'social', 'public').",
    )


class EnvironmentalObservationData(EonBaseModel):
    """Ambient environmental sensor metrics."""

    ambient_noise_db: float | None = Field(
        default=None,
        ge=0.0,
        le=180.0,
        description="Ambient acoustic pressure level in decibels.",
    )
    ambient_lux: float | None = Field(
        default=None,
        ge=0.0,
        le=200000.0,
        description="Illuminance measurement in lux.",
    )
    temperature_celsius: float | None = Field(
        default=None,
        ge=-50.0,
        le=100.0,
        description="Ambient temperature in degrees Celsius.",
    )
    occupancy_count: int | None = Field(
        default=None,
        ge=0,
        le=1000,
        description="Estimated count of human participants in the immediate environment.",
    )


ObservationDataUnion = Annotated[
    VisualObservationData
    | AudioObservationData
    | TextObservationData
    | BehaviourObservationData
    | EnvironmentalObservationData,
    Field(discriminator=None),
]


class ObservationPayload(EonBaseModel):
    """Universal structured observation contract for all perceptual streams."""

    observation_id: EventId = Field(
        default_factory=generate_event_id,
        description="Unique UUID4 identifier for this observation record.",
    )
    source_id: SourceId = Field(
        ...,
        description="Originating sensor or perceptual pipeline identifier.",
    )
    observed_at: UtcTimestamp = Field(
        default_factory=utc_now,
        description="Timezone-aware UTC timestamp when raw data was observed.",
    )
    received_at: UtcTimestamp | None = Field(
        default=None,
        description="Timezone-aware UTC timestamp when ingestion recorded the observation.",
    )
    modality: ModalityType = Field(
        ...,
        description="Sensor or perceptual modality classification.",
    )
    confidence: ConfidenceScore = Field(
        ...,
        description="Normalized confidence score [0.0, 1.0] of this observation.",
    )
    provenance: Provenance = Field(
        ...,
        description="Provenance record tracking algorithm and pipeline origin.",
    )
    quality: QualityStatus = Field(
        default=QualityStatus.GOOD,
        description="Quality and integrity indicator for the observation.",
    )
    expires_at: UtcTimestamp | None = Field(
        default=None,
        description="Optional UTC timestamp after which this observation is considered stale.",
    )
    data: ObservationDataUnion = Field(
        ...,
        description="Modality-specific observation feature payload.",
    )

    @field_validator("expires_at")
    @classmethod
    def validate_expires_after_observed(
        cls, value: datetime.datetime | None, info: Any
    ) -> datetime.datetime | None:
        """Validate that expiration occurs strictly chronologically after observation."""
        observed_at = info.data.get("observed_at")
        if value is not None and observed_at is not None and value <= observed_at:
            raise ValueError("expires_at must be chronologically after observed_at.")
        return value

    def is_stale(
        self,
        current_time: datetime.datetime | None = None,
        max_age_seconds: float = 5.0,
    ) -> bool:
        """Evaluate whether this observation is stale relative to a given point in time."""
        now = current_time or utc_now()
        if self.expires_at is not None:
            return now >= self.expires_at
        age_seconds = (now - self.observed_at).total_seconds()
        return age_seconds > max_age_seconds
