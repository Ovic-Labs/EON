"""Core domain types and enumerations for the Emotion Recognition System (ERS)."""

from enum import Enum

EMPTY_BYTES_SHA256 = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
KNOWN_PLACEHOLDER_CHECKSUMS: frozenset[str] = frozenset(
    {
        EMPTY_BYTES_SHA256,
        "0" * 64,
        "f" * 64,
        "a" * 64,
        "1" * 64,
    }
)


def is_valid_sha256_digest(digest: str) -> bool:
    """Validate that a string is a 64-character hex SHA-256 digest and not a known placeholder."""
    if not isinstance(digest, str) or not digest:
        return False
    c = digest.strip().lower()
    if len(c) != 64:
        return False
    if not all(ch in "0123456789abcdef" for ch in c):
        return False
    if c in KNOWN_PLACEHOLDER_CHECKSUMS:
        return False
    return True


class Modality(str, Enum):
    """Supported input sensory modalities."""

    FACIAL = "facial"
    SPEECH = "speech"
    TEXT = "text"
    VIDEO = "video"
    MULTIMODAL = "multimodal"


class TextSentiment(str, Enum):
    """Distinct textual sentiment polarities (separate from facial/vocal affect)."""

    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    MIXED = "mixed"
    UNKNOWN = "unknown"


class ErrorCode(str, Enum):
    """Stable machine-readable domain error codes across ERS APIs and runtime."""

    CONFIGURATION_ERROR = "ERS_CONFIGURATION_ERROR"
    VALIDATION_ERROR = "ERS_VALIDATION_ERROR"
    CAMERA_PERMISSION_DENIED = "ERS_CAMERA_PERMISSION_DENIED"
    MICROPHONE_PERMISSION_DENIED = "ERS_MICROPHONE_PERMISSION_DENIED"
    DEVICE_DISCONNECTED = "ERS_DEVICE_DISCONNECTED"
    INVALID_MEDIA = "ERS_INVALID_MEDIA"
    CORRUPTED_MEDIA = "ERS_CORRUPTED_MEDIA"
    UNSUPPORTED_CODEC = "ERS_UNSUPPORTED_CODEC"
    MISSING_MODEL = "ERS_MISSING_MODEL"
    INVALID_MODEL = "ERS_INVALID_MODEL"
    MODEL_SIGNATURE_FAILURE = "ERS_MODEL_SIGNATURE_FAILURE"
    MODEL_EXECUTION_ERROR = "ERS_MODEL_EXECUTION_ERROR"
    QUALITY_REJECTION = "ERS_QUALITY_REJECTION"
    ALIGNMENT_ERROR = "ERS_ALIGNMENT_ERROR"
    INSUFFICIENT_EVIDENCE = "ERS_INSUFFICIENT_EVIDENCE"
    DATASET_INTEGRITY_FAILURE = "ERS_DATASET_INTEGRITY_FAILURE"
    CONSENT_REVOKED = "ERS_CONSENT_REVOKED"
    AUTHENTICATION_FAILURE = "ERS_AUTHENTICATION_FAILURE"
    AUTHORIZATION_FAILURE = "ERS_AUTHORIZATION_FAILURE"
    RATE_LIMIT_EXCEEDED = "ERS_RATE_LIMIT_EXCEEDED"
    WEBSOCKET_DISCONNECT = "ERS_WEBSOCKET_DISCONNECT"
    WORKER_FAILURE = "ERS_WORKER_FAILURE"
    RESOURCE_EXHAUSTION = "ERS_RESOURCE_EXHAUSTION"
    PROCESSING_TIMEOUT = "ERS_PROCESSING_TIMEOUT"
    LIFECYCLE_ERROR = "ERS_LIFECYCLE_ERROR"
    SERVER_SHUTDOWN = "ERS_SERVER_SHUTDOWN"
    SAFETY_VIOLATION = "ERS_SAFETY_VIOLATION"
    INTERNAL_ERROR = "ERS_INTERNAL_ERROR"


class QualityGrade(str, Enum):
    """Signal quality classification for input observations."""

    EXCELLENT = "excellent"
    ACCEPTABLE = "acceptable"
    DEGRADED = "degraded"
    UNUSABLE = "unusable"


class InputQualityStatus(str, Enum):
    """Independent sensory input quality status separated from model qualification."""

    ACCEPTABLE = "acceptable"
    DEGRADED = "degraded"
    UNUSABLE = "unusable"


class ModalityEligibilityStatus(str, Enum):
    """Eligibility classification of a sensory stream for multimodal fusion."""

    CLASSIFICATION_ELIGIBLE = "classification_eligible"
    DIAGNOSTIC_ONLY = "diagnostic_only"
    UNVALIDATED = "unvalidated"
    STALE = "stale"
    QUALITY_UNUSABLE = "quality_unusable"
    FAILED = "failed"
    MISSING = "missing"


class EngineState(str, Enum):
    """Lifecycle state of the ERS engine following EON lifecycle architecture."""

    UNINITIALIZED = "UNINITIALIZED"
    INITIALIZING = "INITIALIZING"
    INITIALIZED = "INITIALIZED"
    STARTING = "STARTING"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    DEGRADED = "DEGRADED"
    STOPPING = "STOPPING"
    STOPPED = "STOPPED"
    FAILED = "FAILED"


class EmotionCategory(str, Enum):
    """Supported discrete emotion categories for affective estimation.

    Note: These represent observable behavioural classifications,
    NOT immutable ground-truth psychological states.
    """

    NEUTRAL = "neutral"
    HAPPINESS = "happiness"
    SADNESS = "sadness"
    ANGER = "anger"
    FEAR = "fear"
    SURPRISE = "surprise"
    DISGUST = "disgust"
    UNCERTAINTY = "uncertainty"
    UNKNOWN = "unknown"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


class ObservationStatus(str, Enum):
    """Processing and validation status of an observation."""

    OK = "ok"
    DEGRADED = "degraded"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    MODEL_UNAVAILABLE = "model_unavailable"
    MODEL_UNVALIDATED = "model_unvalidated"
    FAILED = "failed"


class ModelState(str, Enum):
    """Explicit lifecycle and scientific qualification states of a model."""

    MODEL_MISSING = "MODEL_MISSING"
    MODEL_LOADING = "MODEL_LOADING"
    MODEL_LOADED_UNVERIFIED = "MODEL_LOADED_UNVERIFIED"
    MODEL_LOADED_VALIDATED = "MODEL_LOADED_VALIDATED"
    MODEL_UNAVAILABLE = "MODEL_UNAVAILABLE"
    MODEL_INFERENCE_FAILED = "MODEL_INFERENCE_FAILED"
    MODEL_EXPERIMENTAL = "MODEL_EXPERIMENTAL"


class ModelQualificationState(str, Enum):
    """Governance and registry qualification lifecycle states for artifact promotion."""

    MODEL_DISCOVERED = "MODEL_DISCOVERED"
    MODEL_LOADED_UNVALIDATED = "MODEL_LOADED_UNVALIDATED"
    MODEL_VALIDATED = "MODEL_VALIDATED"
    MODEL_REJECTED = "MODEL_REJECTED"
    MODEL_REVOKED = "MODEL_REVOKED"


class DeviceType(str, Enum):
    """Compute execution devices."""

    CPU = "cpu"
    CUDA = "cuda"
    OPENVINO = "openvino"
