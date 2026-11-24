"""API transport schemas for ERS HTTP, ROS 2, and SDK bridges."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eon_ers.contracts import EmotionObservation, FusionResult
from eon_ers.types import Modality


class ProcessObservationRequest(BaseModel):
    """External request to ingest and analyze an observation."""

    model_config = ConfigDict(extra="forbid")

    session_id: str = Field(..., min_length=1, description="Active session ID.")
    consent_reference: str = Field(..., min_length=1, description="Consent reference token.")
    modality: Modality = Field(
        ..., description="Sensory modality ('facial', 'speech', 'multimodal')."
    )
    image_base64: str | None = Field(default=None, description="Base64 encoded JPEG/PNG.")
    audio_base64: str | None = Field(default=None, description="Base64 encoded audio bytes.")
    sample_rate: int | None = Field(default=16000, description="Sampling rate in Hz.")
    source_metadata: dict[str, Any] = Field(default_factory=dict)


class ProcessObservationResponse(BaseModel):
    """External response returning ERS emotional estimate."""

    model_config = ConfigDict(extra="forbid")

    status: str = Field(
        ..., description="Processing status ('ok', 'degraded', 'insufficient_evidence')."
    )
    observation: EmotionObservation | None = Field(default=None)
    fusion_result: FusionResult | None = Field(default=None)
    processing_latency_ms: float = Field(..., ge=0.0)
    error_message: str | None = Field(default=None)


class ResetSessionRequest(BaseModel):
    """Request to flush session history and reset temporal state."""

    model_config = ConfigDict(extra="forbid")

    session_id: str = Field(..., min_length=1)


class HealthResponse(BaseModel):
    """Component health status."""

    model_config = ConfigDict(extra="forbid")

    component: str = Field(default="eon.ers")
    status: str = Field(...)
    state: str = Field(...)
    failure_reason: str | None = Field(default=None)
