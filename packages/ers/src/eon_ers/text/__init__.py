"""Textual sentiment and affect analysis subsystem for ERS (distinct from facial/vocal cues)."""

from eon_ers.text.inference import (
    BaseTextModelAdapter,
    ExperimentalTextAffectAdapter,
    ONNXTextModelAdapter,
)
from eon_ers.text.normalization import NormalizedText, TextNormalizer
from eon_ers.text.postprocessing import TextPipeline
from eon_ers.text.tokenization import TextTokenizationResult, TextTokenizer

__all__ = [
    "BaseTextModelAdapter",
    "ExperimentalTextAffectAdapter",
    "NormalizedText",
    "ONNXTextModelAdapter",
    "TextNormalizer",
    "TextPipeline",
    "TextTokenizationResult",
    "TextTokenizer",
]
