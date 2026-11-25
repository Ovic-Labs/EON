"""Data contracts for the Emotion Recognition System (ERS).

Adheres strictly to OVIC EON responsible AI principles:
Emotion outputs are probabilistic estimates derived from observable behavioural features.
They are never definitive claims about a human's internal subjective truth.
"""

from __future__ import annotations

import time
import uuid
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from eon_ers.types import InputQualityStatus, Modality, ModelState, ObservationStatus, QualityGrade


class QualityAssessment(BaseModel):
    """Quality evaluation report for a sensory observation."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    modality: Modality = Field(..., description="Sensory modality assessed.")
    grade: QualityGrade = Field(..., description="Categorical quality grade.")
    score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Normalized quality score between 0.0 (unusable) and 1.0 (perfect).",
    )
    metrics: dict[str, float] = Field(
        default_factory=dict,
        description="Individual quality metrics (e.g., snr_db, blur_variance, brightness).",
    )
    is_acceptable: bool = Field(
        ...,
        description="Whether the quality meets minimum processing criteria.",
    )
    reasons: list[str] = Field(
        default_factory=list,
        description="Explanatory diagnostic messages for degraded or unusable status.",
    )


class ERSInput(BaseModel):
    """Universal raw sensory observation input envelope for ERS processing.

    Raw media payloads are stored purely in volatile memory and are discarded
    immediately after feature extraction to uphold the zero-disk-retention invariant.
    """

    model_config = ConfigDict(extra="forbid")

    observation_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique identifier for this observation.",
    )
    session_id: str = Field(
        ...,
        min_length=1,
        description="Active interaction session identifier.",
    )
    timestamp: float = Field(
        default_factory=time.time,
        description="Unix timestamp (epoch seconds) when observation occurred.",
    )
    modality: Modality = Field(
        ...,
        description="Sensory modality of this observation.",
    )
    consent_reference: str = Field(
        ...,
        min_length=1,
        description="Cryptographic or UUID reference proving active user consent.",
    )
    image_payload: bytes | None = Field(
        default=None,
        repr=False,
        description="In-memory raw image bytes (JPEG, PNG). Never logged or written to disk.",
    )
    audio_payload: bytes | None = Field(
        default=None,
        repr=False,
        description="In-memory raw audio PCM/WAV bytes. Never logged or written to disk.",
    )
    video_payload: bytes | None = Field(
        default=None,
        repr=False,
        description="In-memory bounded video container bytes. Never logged or written to disk.",
    )
    text_payload: str | None = Field(
        default=None,
        repr=False,
        description="In-memory UTF-8 text payload for sentiment/affect analysis.",
    )
    sample_rate: int | None = Field(
        default=None,
        ge=8000,
        le=192000,
        description="Audio sampling rate in Hertz.",
    )
    image_dimensions: tuple[int, int] | None = Field(
        default=None,
        description="Image dimensions as (width, height) in pixels.",
    )
    source_metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Originating sensor hardware parameters and routing metadata.",
    )
    quality_metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Upstream sensor health or preprocessing indicators.",
    )

    def scrub_media_payload(self) -> None:
        """Securely clear in-memory raw image, audio, video, and text buffers."""
        self.image_payload = None
        self.audio_payload = None
        self.video_payload = None
        self.text_payload = None


class EmotionObservation(BaseModel):
    """Structured uncertainty-aware observation generated from a single modality.

    CRITICAL RESPONSIBLE AI REQUIREMENT:
    is_definitive_claim is strictly FALSE. This is an algorithmic observation of
    expressed signals, not a certified psychological diagnosis or inner truth claim.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    observation_id: str = Field(..., description="Identifier of the source observation.")
    timestamp: float = Field(..., description="Timestamp of the observation in epoch seconds.")
    modality: Modality = Field(..., description="Modality used for this observation.")
    expression_observations: dict[str, Any] = Field(
        default_factory=dict,
        description="Observable behavioural features (e.g. Action Units, pitch F0, speech energy).",
    )
    emotion_probabilities: dict[str, float] = Field(
        ...,
        description="Probability distribution across supported emotion categories.",
    )
    dominant_estimate: str = Field(
        ...,
        description="Dominant estimated emotion category based on observable evidence.",
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Estimated confidence score in [0.0, 1.0].",
    )
    uncertainty: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Estimated epistemic/aleatoric uncertainty in [0.0, 1.0].",
    )
    quality_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Signal quality score of the source sensory input in [0.0, 1.0].",
    )
    model_id: str = Field(
        ..., description="Identifier of the executing model or heuristic adapter."
    )
    model_version: str = Field(..., description="Version of the model or adapter.")
    processing_latency_ms: float = Field(
        ...,
        ge=0.0,
        description="Total processing latency in milliseconds.",
    )
    limitations: list[str] = Field(
        default_factory=list,
        description="Documented operational boundaries and caveats for this estimate.",
    )
    status: ObservationStatus = Field(
        default=ObservationStatus.OK,
        description="Status indicator ('ok', 'degraded', 'insufficient_evidence', 'model_unavailable', 'model_unvalidated', 'failed').",
    )
    input_quality: InputQualityStatus = Field(
        default=InputQualityStatus.ACCEPTABLE,
        description="Independent sensory input quality status separated from model qualification.",
    )
    is_calibrated: bool = Field(
        default=False,
        description="Whether the confidence score has been verified against empirical calibration evidence.",
    )
    raw_confidence: float | None = Field(
        default=None,
        description="Raw uncalibrated confidence score prior to calibration mapping.",
    )
    model_state: ModelState = Field(
        default=ModelState.MODEL_LOADED_UNVERIFIED,
        description="Scientific validation and lifecycle state of the executing model.",
    )
    is_validated: bool = Field(
        default=False,
        description="Whether this observation was generated by an empirically validated model.",
    )
    face_id: str | None = Field(
        default=None,
        description="Ephemeral session-only face tracking identifier (never a permanent biometric identity).",
    )
    face_bbox: dict[str, float] | None = Field(
        default=None,
        description="Normalized primary face bounding box coordinates when facial detection ran.",
    )
    face_count: int | None = Field(
        default=None,
        ge=0,
        description="Number of detected faces in the visual frame.",
    )
    voice_activity: bool | None = Field(
        default=None,
        description="Whether human voice activity was detected in the speech segment.",
    )
    speech_ratio: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Proportion of audio frames exhibiting voice activity.",
    )
    insufficient_evidence_reason: str | None = Field(
        default=None,
        description="Explicit diagnostic reason when evidence is insufficient or abstained.",
    )
    is_definitive_claim: bool = Field(
        default=False,
        frozen=True,
        description="Strict non-negotiable invariant: emotional observations are never definitive claims.",
    )

    @field_validator("is_definitive_claim")
    @classmethod
    def validate_non_definitive(cls, v: bool) -> bool:
        """Enforce that emotion observations can never be asserted as definitive claims."""
        if v is not False:
            raise ValueError(
                "is_definitive_claim must always be False in adherence to Responsible AI principles."
            )
        return v


class FusionResult(BaseModel):
    """Multimodal fused emotion estimate combining aligned sensory observations."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str = Field(
        default="1.0",
        description="Fusion output contract schema version.",
    )
    result_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique identifier for this fused estimate.",
    )
    session_id: str | None = Field(
        default=None,
        description="Session correlation identifier when generated inside a session.",
    )
    timestamp: float = Field(..., description="Timestamp of the fused estimate in epoch seconds.")
    facial_observation: EmotionObservation | None = Field(
        default=None,
        description="Contributing facial expression observation if available.",
    )
    speech_observation: EmotionObservation | None = Field(
        default=None,
        description="Contributing speech acoustic observation if available.",
    )
    text_observation: EmotionObservation | None = Field(
        default=None,
        description="Contributing text affect observation if available.",
    )
    fused_probabilities: dict[str, float] = Field(
        ...,
        description="Fused probability distribution across emotion categories.",
    )
    dominant_estimate: str = Field(
        ...,
        description="Dominant estimated emotion category after multimodal weighting.",
    )
    modality_weights: dict[str, float] = Field(
        ...,
        description="Quality-attenuated weights applied to each contributing modality.",
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Fused confidence score in [0.0, 1.0].",
    )
    uncertainty: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Fused uncertainty score in [0.0, 1.0].",
    )
    conflicting_evidence: bool = Field(
        default=False,
        description="Whether modality observations provide statistically conflicting predictions.",
    )
    conflict_metric: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Statistical divergence (e.g. Jensen-Shannon divergence) between modalities.",
    )
    missing_modalities: list[Modality] = Field(
        default_factory=list,
        description="Expected modalities that were absent or rejected during alignment.",
    )
    quality_summary: dict[str, float] = Field(
        default_factory=dict,
        description="Quality summary scores for all evaluated modalities.",
    )
    limitations: list[str] = Field(
        default_factory=list,
        description="Operational caveats, environmental noise notes, and boundary conditions.",
    )
    contributing_model_states: dict[str, str] = Field(
        default_factory=dict,
        description="Scientific model validation state of each contributing modality.",
    )
    classification_eligible_modalities: list[str] = Field(
        default_factory=list,
        description="Modalities strictly validated and eligible for affective classification.",
    )
    diagnostic_modalities: list[str] = Field(
        default_factory=list,
        description="Modalities presented for diagnostic/observability only, isolated from classification probabilities.",
    )
    fusion_status: str = Field(
        default="ok",
        description="Overall multimodal fusion and eligibility status ('ok', 'unvalidated_only', 'conflict_attenuated', 'insufficient_evidence').",
    )
    contributing_artifact_hashes: dict[str, str] = Field(
        default_factory=dict,
        description="Cryptographic SHA-256 digest of each contributing model artifact.",
    )
    contributing_validation_records: dict[str, str] = Field(
        default_factory=dict,
        description="Validation record ID of each contributing model.",
    )
    is_validated: bool = Field(
        default=False,
        description="Whether this fused estimate is grounded in empirically validated models.",
    )
    fusion_algorithm: str = Field(
        default="quality_reliability_bayesian_v2",
        description="Documented multimodal fusion algorithm identifier.",
    )
    excluded_modalities: list[str] = Field(
        default_factory=list,
        description="Modalities excluded from fusion due to staleness, missing input, failure, or unvalidated state.",
    )
    processing_latency_ms: float = Field(
        default=0.0,
        ge=0.0,
        description="Total fusion computation latency in milliseconds.",
    )
    is_definitive_claim: bool = Field(
        default=False,
        frozen=True,
        description="Strict non-negotiable invariant: emotional estimates are never definitive truth claims.",
    )

    @field_validator("is_definitive_claim")
    @classmethod
    def validate_non_definitive(cls, v: bool) -> bool:
        """Enforce that fusion results can never be asserted as definitive claims."""
        if v is not False:
            raise ValueError(
                "is_definitive_claim must always be False in adherence to Responsible AI principles."
            )
        return v
