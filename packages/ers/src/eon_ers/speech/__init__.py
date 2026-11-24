"""Speech processing module for ERS."""

from eon_ers.speech.adapters import (
    AcousticFeatureProsodyAdapter,
    BaseSpeechModelAdapter,
    DeterministicTestSpeechAdapter,
    ONNXSpeechModelAdapter,
)
from eon_ers.speech.features import AcousticFeatureExtractor
from eon_ers.speech.pipeline import SpeechPipeline
from eon_ers.speech.preprocessing import SpeechPreprocessor

__all__ = [
    "AcousticFeatureExtractor",
    "AcousticFeatureProsodyAdapter",
    "BaseSpeechModelAdapter",
    "DeterministicTestSpeechAdapter",
    "ONNXSpeechModelAdapter",
    "SpeechPipeline",
    "SpeechPreprocessor",
]
