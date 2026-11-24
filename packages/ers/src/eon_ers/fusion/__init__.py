"""Multimodal fusion module for ERS."""

from eon_ers.fusion.alignment import ObservationAligner
from eon_ers.fusion.confidence import DivergenceCalculator
from eon_ers.fusion.multimodal import MultimodalFusionPipeline
from eon_ers.fusion.weighting import ReliabilityWeighter

__all__ = [
    "DivergenceCalculator",
    "MultimodalFusionPipeline",
    "ObservationAligner",
    "ReliabilityWeighter",
]
