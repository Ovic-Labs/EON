"""Emotion Recognition System API for the unified EON SDK."""

from eon_ers import EmotionObservation, ERSConfig, ERSEngine, ERSError, ERSInput, FusionResult
from eon_ers.sdk import ERSClient

__all__ = [
    "ERSClient",
    "ERSConfig",
    "ERSEngine",
    "ERSError",
    "ERSInput",
    "EmotionObservation",
    "FusionResult",
]
