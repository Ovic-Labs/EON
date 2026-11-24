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
    FAILED = "failed"


class DeviceType(str, Enum):
    """Compute execution devices."""

    CPU = "cpu"
    CUDA = "cuda"
    OPENVINO = "openvino"
