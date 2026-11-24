"""Scientific model evaluation and qualification framework for ERS."""

from __future__ import annotations

from eon_ers.evaluation.dataset import (
    AFFECTNET_METADATA,
    CREMA_D_METADATA,
    RAF_DB_METADATA,
    RAVDESS_METADATA,
    DatasetMetadata,
    EvaluationPartition,
    EvaluationSample,
    create_subject_independent_partition,
)
from eon_ers.evaluation.evaluator import ModelEvaluator
from eon_ers.evaluation.metrics import (
    compute_calibration_metrics,
    compute_classification_metrics,
    compute_confidence_distribution,
    compute_confusion_matrix,
)

__all__ = [
    "AFFECTNET_METADATA",
    "CREMA_D_METADATA",
    "RAF_DB_METADATA",
    "RAVDESS_METADATA",
    "DatasetMetadata",
    "EvaluationPartition",
    "EvaluationSample",
    "ModelEvaluator",
    "compute_calibration_metrics",
    "compute_classification_metrics",
    "compute_confidence_distribution",
    "compute_confusion_matrix",
    "create_subject_independent_partition",
]
