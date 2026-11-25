"""Domain exception hierarchy and structured error envelopes for ERS."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from eon_ers.types import ErrorCode


class ERSError(Exception):
    """Base structured exception for all ERS runtime and domain errors."""

    default_error_code: ErrorCode = ErrorCode.INTERNAL_ERROR
    default_retryable: bool = False

    def __init__(
        self,
        message: str = "",
        *,
        error_code: ErrorCode | str | None = None,
        retryable: bool | None = None,
        context: dict[str, Any] | None = None,
        correlation_id: str | None = None,
    ) -> None:
        super().__init__(message)
        from eon_ers.privacy.media_handling import SensitiveDataRedactor

        code_val = (
            error_code.value
            if isinstance(error_code, ErrorCode)
            else (str(error_code) if error_code else self.default_error_code.value)
        )
        self.error_code: str = code_val
        self.message: str = SensitiveDataRedactor.redact_string(message)
        self.retryable: bool = self.default_retryable if retryable is None else bool(retryable)
        self.context: dict[str, Any] = SensitiveDataRedactor.sanitize_dict(context or {})
        self.timestamp: str = datetime.now(timezone.utc).isoformat()
        self.correlation_id: str | None = correlation_id

    def to_error_payload(self, correlation_id: str | None = None) -> dict[str, Any]:
        """Serialize error safely for API and WebSocket responses without stack traces or secrets."""
        return {
            "error": {
                "code": self.error_code,
                "message": self.message,
                "retryable": self.retryable,
                "context": self.context,
                "timestamp": self.timestamp,
                "correlation_id": correlation_id or self.correlation_id,
            }
        }


class ERSConfigurationError(ERSError):
    """Raised when engine configuration parameters are invalid or contradictory."""

    default_error_code = ErrorCode.CONFIGURATION_ERROR


class ERSValidationError(ERSError):
    """Raised when input data violates contract constraints, dimensions, or formats."""

    default_error_code = ErrorCode.VALIDATION_ERROR


class ERSInvalidMediaError(ERSValidationError):
    """Raised when image, audio, or video payloads are malformed or invalid."""

    default_error_code = ErrorCode.INVALID_MEDIA


class ERSCorruptedMediaError(ERSInvalidMediaError):
    """Raised when media container bytes are corrupted or undecodable."""

    default_error_code = ErrorCode.CORRUPTED_MEDIA


class ERSUnsupportedCodecError(ERSValidationError):
    """Raised when media uses an unsupported container or codec."""

    default_error_code = ErrorCode.UNSUPPORTED_CODEC


class ERSModelUnavailableError(ERSError):
    """Raised when a requested model adapter or weights file is uninstalled or unavailable."""

    default_error_code = ErrorCode.MISSING_MODEL
    default_retryable = True


class ERSModelExecutionError(ERSError):
    """Raised when model inference execution fails unexpectedly."""

    default_error_code = ErrorCode.MODEL_EXECUTION_ERROR
    default_retryable = True


class ERSModelIntegrityError(ERSError):
    """Raised when model artifact checksum, tensor contract, or manifest verification fails."""

    default_error_code = ErrorCode.INVALID_MODEL


class ERSModelSignatureError(ERSModelIntegrityError):
    """Raised when cryptographic Ed25519 signature or trust registry verification fails."""

    default_error_code = ErrorCode.MODEL_SIGNATURE_FAILURE


class ERSQualityRejectionError(ERSError):
    """Raised when input signal quality falls below the minimum usable threshold."""

    default_error_code = ErrorCode.QUALITY_REJECTION


class ERSInsufficientEvidenceError(ERSError):
    """Raised when evidence is insufficient to produce an affective estimate."""

    default_error_code = ErrorCode.INSUFFICIENT_EVIDENCE


class ERSAlignmentError(ERSError):
    """Raised when sensory observations cannot be aligned within the multimodal temporal window."""

    default_error_code = ErrorCode.ALIGNMENT_ERROR


class ERSDatasetIntegrityError(ERSError):
    """Raised when dataset archive digest, extraction safety, or provenance verification fails."""

    default_error_code = ErrorCode.DATASET_INTEGRITY_FAILURE


class ERSPrivacyConsentError(ERSError):
    """Raised when processing is attempted without valid user consent or after consent revocation."""

    default_error_code = ErrorCode.CONSENT_REVOKED


class ERSCameraPermissionError(ERSPrivacyConsentError):
    """Raised when camera permission was denied or revoked."""

    default_error_code = ErrorCode.CAMERA_PERMISSION_DENIED


class ERSMicrophonePermissionError(ERSPrivacyConsentError):
    """Raised when microphone permission was denied or revoked."""

    default_error_code = ErrorCode.MICROPHONE_PERMISSION_DENIED


class ERSAuthenticationError(ERSError):
    """Raised when API key or bearer token authentication fails."""

    default_error_code = ErrorCode.AUTHENTICATION_FAILURE


class ERSAuthorizationError(ERSError):
    """Raised when caller lacks RBAC permission or session ownership."""

    default_error_code = ErrorCode.AUTHORIZATION_FAILURE


class ERSRateLimitError(ERSError):
    """Raised when client exceeds configured request or WebSocket message rate limits."""

    default_error_code = ErrorCode.RATE_LIMIT_EXCEEDED
    default_retryable = True


class ERSDeviceDisconnectedError(ERSError):
    """Raised when a live capture device disconnects during streaming."""

    default_error_code = ErrorCode.DEVICE_DISCONNECTED
    default_retryable = True


class ERSResourceExhaustedError(ERSError):
    """Raised when internal memory, buffer limits, or compute budgets are exceeded."""

    default_error_code = ErrorCode.RESOURCE_EXHAUSTION
    default_retryable = True


class ERSProcessingTimeoutError(ERSResourceExhaustedError):
    """Raised when inference or media processing exceeds its configured timeout budget."""

    default_error_code = ErrorCode.PROCESSING_TIMEOUT
    default_retryable = True


class ERSWorkerError(ERSError):
    """Raised when an internal worker task fails unexpectedly."""

    default_error_code = ErrorCode.WORKER_FAILURE
    default_retryable = True


class ERSLifecycleError(ERSError):
    """Raised when an illegal lifecycle transition is invoked."""

    default_error_code = ErrorCode.LIFECYCLE_ERROR


class ERSSafetyViolationError(ERSError, RuntimeError):
    """Raised when an output payload attempts robot actuation or violates safety policy."""

    default_error_code = ErrorCode.SAFETY_VIOLATION
