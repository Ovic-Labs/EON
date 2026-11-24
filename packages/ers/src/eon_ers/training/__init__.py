"""Reproducible model training, calibration, and validation pipeline for ERS."""

from __future__ import annotations

from eon_ers.training.calibration import CalibrationResult, TemperatureCalibrator
from eon_ers.training.export import ONNXExportMetadata, ONNXModelExporter
from eon_ers.training.features import FeatureConfig, FeatureExtractor, ZeroLeakageNormalizer
from eon_ers.training.pipeline import (
    ModelTrainingPipeline,
    PipelineStageResult,
    TrainingPipelineStage,
)
from eon_ers.training.preprocessing import PreprocessingConfig, SamplePreprocessor
from eon_ers.training.trainer import (
    CPUModelTrainer,
    TrainedModelArtifact,
    TrainingConfig,
    TrainingHistory,
    TrainingMode,
)

__all__ = [
    "CalibrationResult",
    "CPUModelTrainer",
    "FeatureConfig",
    "FeatureExtractor",
    "ModelTrainingPipeline",
    "ONNXExportMetadata",
    "ONNXModelExporter",
    "PipelineStageResult",
    "PreprocessingConfig",
    "SamplePreprocessor",
    "TemperatureCalibrator",
    "TrainedModelArtifact",
    "TrainingConfig",
    "TrainingHistory",
    "TrainingMode",
    "TrainingPipelineStage",
    "ZeroLeakageNormalizer",
]
