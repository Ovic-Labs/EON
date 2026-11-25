"""API transport schemas for ERS HTTP, WebSocket, ROS 2, and SDK bridges."""

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


class ConsentRegisterRequest(BaseModel):
    """Request to register explicit user consent for an interaction session."""

    model_config = ConfigDict(extra="forbid")

    session_id: str = Field(..., min_length=1, description="Unique session identifier.")
    consent_reference: str = Field(
        ..., min_length=1, description="Explicit consent reference token."
    )


class ConsentRevokeRequest(BaseModel):
    """Request to immediately revoke consent and block subsequent processing."""

    model_config = ConfigDict(extra="forbid")

    session_id: str = Field(..., min_length=1, description="Unique session identifier.")


class ConsentStatusResponse(BaseModel):
    """Response reporting current session consent status."""

    model_config = ConfigDict(extra="forbid")

    session_id: str = Field(...)
    has_active_consent: bool = Field(...)
    is_revoked: bool = Field(...)
    masked_reference: str | None = Field(default=None)


class ModelStatusDetail(BaseModel):
    """Detailed model lifecycle, provenance, and validation status report."""

    model_config = ConfigDict(extra="forbid")

    model_id: str = Field(...)
    modality: str = Field(...)
    version: str = Field(...)
    state: str = Field(...)
    is_validated: bool = Field(...)
    provenance: str = Field(...)
    license: str = Field(...)
    artifact_sha256: str | None = Field(default=None)
    known_limitations: list[str] = Field(default_factory=list)


class ModelStatusResponse(BaseModel):
    """System-wide model qualification catalog."""

    model_config = ConfigDict(extra="forbid")

    models: list[ModelStatusDetail] = Field(default_factory=list)
    overall_qualification: str = Field(...)
    timestamp: float = Field(...)


class DeviceStatusResponse(BaseModel):
    """Connected sensor hardware status."""

    model_config = ConfigDict(extra="forbid")

    camera_active: bool = Field(default=False)
    microphone_active: bool = Field(default=False)
    has_consent: bool = Field(default=False)
    session_id: str | None = Field(default=None)


class PerformanceTelemetryResponse(BaseModel):
    """Real-time performance metrics and percentiles."""

    model_config = ConfigDict(extra="forbid")

    session_id: str = Field(...)
    frame_latency_ms: float = Field(default=0.0)
    audio_latency_ms: float = Field(default=0.0)
    fusion_latency_ms: float = Field(default=0.0)
    p50_ms: float = Field(default=0.0)
    p95_ms: float = Field(default=0.0)
    p99_ms: float = Field(default=0.0)
    memory_rss_mb: float | None = Field(default=None)
    timestamp: float = Field(...)


class HealthResponse(BaseModel):
    """Component health and lifecycle status report."""

    model_config = ConfigDict(extra="forbid")

    component: str = Field(default="eon.ers")
    status: str = Field(...)
    state: str = Field(...)
    is_running: bool = Field(...)
    core_integration_status: str = Field(default="NOT_CONNECTED")
    missing_dependencies: list[str] = Field(default_factory=list)
    failure_reason: str | None = Field(default=None)


class LiveMultimodalMessage(BaseModel):
    """Payload for REST-based multimodal live sensory processing."""

    model_config = ConfigDict(extra="ignore")

    session_id: str = Field(..., description="Active session ID.")
    consent_reference: str | None = Field(default=None, description="User consent reference token.")
    image_base64: str | None = Field(default=None, description="Base64 encoded frame (JPEG/PNG).")
    audio_base64: str | None = Field(default=None, description="Base64 encoded audio (WAV).")
    sample_rate: int = Field(default=16000, description="Audio sample rate.")
    timestamp: float | None = Field(default=None, description="Epoch timestamp.")


class LiveStreamInboundMessage(BaseModel):
    """Inbound streaming message from live client over WebSocket."""

    model_config = ConfigDict(extra="ignore")

    type: str = Field(
        ..., description="Message type ('init', 'frame', 'audio', 'multimodal', 'revoke', 'stop')."
    )
    session_id: str = Field(..., description="Session identifier.")
    consent_reference: str | None = Field(default=None, description="Consent reference token.")
    image_base64: str | None = Field(default=None, description="Base64 encoded JPEG/PNG frame.")
    audio_base64: str | None = Field(
        default=None, description="Base64 encoded WAV/PCM audio chunk."
    )
    sample_rate: int = Field(default=16000, description="Audio sample rate in Hz.")
    timestamp: float | None = Field(default=None, description="Epoch timestamp of client capture.")


class LiveStreamOutboundMessage(BaseModel):
    """Outbound streaming event broadcasted to live client over WebSocket."""

    model_config = ConfigDict(extra="forbid")

    type: str = Field(..., description="Event type ('observation', 'fusion', 'status', 'error').")
    session_id: str = Field(...)
    timestamp: float = Field(...)
    modality: str | None = Field(default=None)
    data: dict[str, Any] = Field(default_factory=dict)
    latency_ms: float = Field(default=0.0)
    error: str | None = Field(default=None)


class TextAnalyzeRequest(BaseModel):
    """Request schema for UTF-8 textual sentiment and affect analysis."""

    model_config = ConfigDict(extra="forbid")

    session_id: str = Field(..., min_length=1)
    consent_reference: str = Field(..., min_length=1)
    text: str = Field(..., min_length=1, max_length=100000)


class VideoAnalyzeRequest(BaseModel):
    """Request schema for bounded base64-encoded video analysis."""

    model_config = ConfigDict(extra="forbid")

    session_id: str = Field(..., min_length=1)
    consent_reference: str = Field(..., min_length=1)
    video_base64: str = Field(..., min_length=1)
    sample_fps: float | None = Field(default=None, gt=0.05, le=60.0)


class MultimodalAnalyzeRequest(BaseModel):
    """Three-modality analysis request (any combination of facial, audio, and text)."""

    model_config = ConfigDict(extra="forbid")

    session_id: str = Field(..., min_length=1)
    consent_reference: str = Field(..., min_length=1)
    image_base64: str | None = Field(default=None)
    audio_base64: str | None = Field(default=None)
    sample_rate: int = Field(default=16000, ge=8000, le=192000)
    text: str | None = Field(default=None, max_length=100000)


class CreateLiveSessionRequest(BaseModel):
    """Request to initialize an isolated live ERS session."""

    model_config = ConfigDict(extra="forbid")

    session_id: str | None = Field(default=None, min_length=1)
    consent_reference: str | None = Field(default=None, min_length=1)
    consent_scope: list[str] = Field(default_factory=lambda: ["facial", "speech", "text"])
    history_opt_in: bool = Field(default=False)
    ttl_seconds: float | None = Field(default=3600.0, gt=10.0, le=86400.0)
