"""Core domain types and enumerations for the Emotion Recognition System (ERS)."""

from enum import Enum


class Modality(str, Enum):
    """Supported input sensory modalities."""

    FACIAL = "facial"
    SPEECH = "speech"
    MULTIMODAL = "multimodal"


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


class DeviceType(str, Enum):
    """Compute execution devices."""

    CPU = "cpu"
    CUDA = "cuda"
    OPENVINO = "openvino"
