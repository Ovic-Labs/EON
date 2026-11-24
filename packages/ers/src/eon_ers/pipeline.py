"""Unified pipeline interface for ERS sensory analysis."""

from __future__ import annotations

from eon_ers.facial.pipeline import FacialPipeline
from eon_ers.fusion.multimodal import MultimodalFusionPipeline
from eon_ers.speech.pipeline import SpeechPipeline

__all__ = [
    "FacialPipeline",
    "MultimodalFusionPipeline",
    "SpeechPipeline",
]
