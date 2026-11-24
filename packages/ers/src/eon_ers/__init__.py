"""Emotion Recognition System (ERS) package root."""

from eon_ers.config import ERSConfig
from eon_ers.contracts import EmotionObservation, ERSInput, FusionResult, QualityAssessment
from eon_ers.engine import ERSEngine
from eon_ers.exceptions import (
    ERSAlignmentError,
    ERSConfigurationError,
    ERSError,
    ERSLifecycleError,
    ERSModelExecutionError,
    ERSModelUnavailableError,
    ERSPrivacyConsentError,
    ERSQualityRejectionError,
    ERSResourceExhaustedError,
    ERSValidationError,
)
from eon_ers.types import (
    DeviceType,
    EmotionCategory,
    EngineState,
    Modality,
    ObservationStatus,
    QualityGrade,
)

__version__ = "0.1.0"
__title__ = "eon-ers"
__author__ = "OVIC Labs"
__license__ = "Apache-2.0"

__all__ = [
    "DeviceType",
    "ERSAlignmentError",
    "ERSConfig",
    "ERSConfigurationError",
    "ERSEngine",
    "ERSError",
    "ERSInput",
    "ERSLifecycleError",
    "ERSModelExecutionError",
    "ERSModelUnavailableError",
    "ERSPrivacyConsentError",
    "ERSQualityRejectionError",
    "ERSResourceExhaustedError",
    "ERSValidationError",
    "EmotionCategory",
    "EmotionObservation",
    "EngineState",
    "FusionResult",
    "Modality",
    "ObservationStatus",
    "QualityAssessment",
    "QualityGrade",
    "__author__",
    "__license__",
    "__title__",
    "__version__",
]
