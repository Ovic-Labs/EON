"""Scientific model evaluation and qualification framework for ERS."""

from __future__ import annotations

from eon_ers.evaluation.evaluator import ModelEvaluator
from eon_ers.evaluation.metrics import (
    compute_calibration_metrics,
    compute_classification_metrics,
    compute_confidence_distribution,
    compute_confusion_matrix,
)

__all__ = [
    "ModelEvaluator",
    "compute_calibration_metrics",
    "compute_classification_metrics",
    "compute_confidence_distribution",
    "compute_confusion_matrix",
]
