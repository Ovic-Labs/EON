"""Configuration models and defaults for the Emotion Recognition System (ERS)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eon_ers.types import DeviceType


class ERSConfig(BaseModel):
    """Runtime configuration for the ERS engine, tuned for Intel Core Ultra 5 / edge CPU."""

    model_config = ConfigDict(extra="forbid")

    # Engine pipeline enables
    enable_facial: bool = Field(
        default=True,
        description="Enable visual facial expression recognition pipeline.",
    )
    enable_speech: bool = Field(
        default=True,
        description="Enable speech acoustic prosody recognition pipeline.",
    )
    enable_text: bool = Field(
        default=True,
        description="Enable textual sentiment and affect analysis pipeline.",
    )
    enable_video: bool = Field(
        default=True,
        description="Enable bounded video decoding and facial frame analysis pipeline.",
    )
    enable_multimodal_fusion: bool = Field(
        default=True,
        description="Enable multimodal alignment and probability fusion.",
    )

    # Compute execution target
    device: DeviceType = Field(
        default=DeviceType.CPU,
        description="Target compute device ('cpu', 'cuda', 'openvino').",
    )
    num_threads: int = Field(
        default=4,
        ge=1,
        le=32,
        description="Worker thread count for ONNX runtime or CPU feature extraction.",
    )

    # Model identifiers and optional custom file paths
    facial_model_id: str = Field(
        default="ers-facial-onnx-cpu-v1",
        description="Registered identifier for the facial emotion model.",
    )
    facial_model_path: str | None = Field(
        default=None,
        description="Optional local filesystem path to custom facial ONNX model weights.",
    )
    speech_model_id: str = Field(
        default="ers-speech-onnx-cpu-v1",
        description="Registered identifier for the speech emotion model.",
    )
    speech_model_path: str | None = Field(
        default=None,
        description="Optional local filesystem path to custom speech ONNX model weights.",
    )
    text_model_id: str = Field(
        default="ers-text-affect-cpu-v1",
        description="Registered identifier for the text affect model.",
    )
    text_model_path: str | None = Field(
        default=None,
        description="Optional local filesystem path to custom text affect ONNX model weights.",
    )

    # Payload, resource, and video bounds
    max_image_bytes: int = Field(
        default=10 * 1024 * 1024,
        ge=1024,
        le=100 * 1024 * 1024,
        description="Maximum accepted decoded image payload size in bytes.",
    )
    max_audio_bytes: int = Field(
        default=20 * 1024 * 1024,
        ge=1024,
        le=200 * 1024 * 1024,
        description="Maximum accepted decoded audio payload size in bytes.",
    )
    max_text_length: int = Field(
        default=8192,
        ge=1,
        le=100000,
        description="Maximum accepted UTF-8 text length in characters.",
    )
    video_max_bytes: int = Field(
        default=50 * 1024 * 1024,
        ge=1024,
        le=500 * 1024 * 1024,
        description="Maximum accepted video upload payload size in bytes.",
    )
    video_max_frames: int = Field(
        default=120,
        ge=1,
        le=5000,
        description="Maximum decoded frames sampled per video analysis request.",
    )
    video_sample_fps: float = Field(
        default=2.0,
        gt=0.05,
        le=60.0,
        description="Target frame sampling rate for bounded video processing.",
    )
    processing_timeout_seconds: float = Field(
        default=10.0,
        gt=0.1,
        le=300.0,
        description="Per-operation processing timeout budget in seconds.",
    )
    correlated_agreement_dampening: float = Field(
        default=0.85,
        ge=0.5,
        le=1.0,
        description="Confidence cap factor preventing over-confidence when correlated modalities agree.",
    )
    max_ws_queue_size: int = Field(
        default=32,
        ge=1,
        le=1024,
        description="Bounded live WebSocket processing queue capacity before dropping stale frames.",
    )
    ws_max_messages_per_second: float = Field(
        default=30.0,
        gt=0.1,
        le=500.0,
        description="Per-connection WebSocket inbound message rate limit.",
    )
    require_api_auth: bool = Field(
        default=False,
        description="Enforce API key authentication and RBAC authorization across REST and WS endpoints.",
    )
    rate_limit_requests_per_minute: int = Field(
        default=600,
        ge=10,
        le=100000,
        description="Sliding-window API rate limit per client principal or IP per minute.",
    )
    enable_session_history: bool = Field(
        default=False,
        description="Whether opted-in session observation summaries are retained in volatile memory.",
    )

    # Image processing thresholds
    min_face_resolution: tuple[int, int] = Field(
        default=(48, 48),
        description="Minimum (width, height) in pixels required for facial analysis.",
    )
    max_image_dimension: int = Field(
        default=1920,
        ge=128,
        le=7680,
        description="Maximum image width or height permitted before automatic downscaling.",
    )
    blur_threshold: float = Field(
        default=30.0,
        ge=0.0,
        description="Minimum Laplacian variance threshold to reject motion blurred images.",
    )
    min_brightness: float = Field(
        default=15.0,
        ge=0.0,
        le=255.0,
        description="Minimum mean pixel luminance to reject severely underexposed frames.",
    )

    # Audio processing parameters
    audio_sample_rate: int = Field(
        default=16000,
        ge=8000,
        le=48000,
        description="Expected audio sampling frequency in Hertz.",
    )
    audio_window_duration_seconds: float = Field(
        default=2.0,
        gt=0.1,
        le=10.0,
        description="Target sliding analysis window duration in seconds.",
    )
    max_audio_duration_seconds: float = Field(
        default=10.0,
        gt=0.1,
        le=60.0,
        description="Maximum accepted audio window duration in seconds.",
    )
    min_audio_snr_db: float = Field(
        default=3.0,
        description="Minimum signal-to-noise ratio in dB to accept speech audio.",
    )
    silence_threshold_db: float = Field(
        default=-45.0,
        description="RMS energy threshold in dB below which frames are classified as silence.",
    )

    # Multimodal alignment & fusion parameters
    alignment_window_seconds: float = Field(
        default=0.5,
        gt=0.01,
        le=5.0,
        description="Maximum temporal divergence between facial and speech observations for fusion.",
    )
    conflict_threshold: float = Field(
        default=0.45,
        ge=0.0,
        le=1.0,
        description="Jensen-Shannon distance above which observations are flagged conflicting.",
    )

    # Confidence, uncertainty & abstention thresholds
    confidence_threshold: float = Field(
        default=0.35,
        ge=0.0,
        le=1.0,
        description="Confidence score below which observation is marked insufficient evidence.",
    )
    uncertainty_threshold: float = Field(
        default=0.65,
        ge=0.0,
        le=1.0,
        description="Entropy/margin uncertainty score above which observation is marked uncertain.",
    )

    # Temporal smoothing
    temporal_smoothing_alpha: float = Field(
        default=0.35,
        ge=0.0,
        le=1.0,
        description="Exponential moving average factor (higher = faster response, lower = smoother).",
    )
    temporal_half_life_seconds: float = Field(
        default=3.0,
        gt=0.1,
        le=60.0,
        description="Decay half-life in seconds for historical emotion observations.",
    )

    # In-memory bounds & privacy
    max_buffer_size: int = Field(
        default=100,
        ge=1,
        le=1000,
        description="Maximum queue and ring-buffer depth to bound memory footprint.",
    )
    require_explicit_consent: bool = Field(
        default=True,
        description="Enforce valid cryptographic or session consent reference before processing.",
    )
    zero_disk_retention: bool = Field(
        default=True,
        description="Enforce zero non-volatile disk writes for raw sensory media buffers.",
    )
    anonymize_logs: bool = Field(
        default=True,
        description="Strictly redact any biometric identifiers, raw tokens, or media in logs.",
    )

    # Core Event Bus integration
    event_bus: Any | None = Field(
        default=None,
        description="Optional EventBus instance to publish engine events.",
    )
