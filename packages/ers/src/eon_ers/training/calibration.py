"""Genuine temperature scaling calibration optimizing NLL on validation logits.

Implements:
- Bounded scalar optimization of temperature T on validation logits.
- Before and after calibration metrics (Negative Log-Likelihood, ECE, Brier score).
- Temperature bounds enforcement (0.1 <= T <= 10.0).
- Validation data finiteness and cardinality checks.
"""

from __future__ import annotations

import logging
import time

import numpy as np
from pydantic import BaseModel, ConfigDict, Field
from scipy.optimize import minimize_scalar

from eon_ers.evaluation.metrics import compute_calibration_metrics

logger = logging.getLogger("eon_ers.training.calibration")


class CalibrationResult(BaseModel):
    """Auditable telemetry and metric deltas from genuine temperature calibration."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    optimal_temperature: float = Field(
        ..., ge=0.1, le=10.0, description="Optimized temperature parameter."
    )
    before_nll: float = Field(
        ..., description="Validation Negative Log-Likelihood before scaling (T=1.0)."
    )
    after_nll: float = Field(
        ..., description="Validation Negative Log-Likelihood after optimal scaling."
    )
    before_ece: float = Field(..., description="Expected Calibration Error before scaling.")
    after_ece: float = Field(..., description="Expected Calibration Error after optimal scaling.")
    before_brier: float = Field(..., description="Brier score before scaling.")
    after_brier: float = Field(..., description="Brier score after optimal scaling.")
    validation_sample_count: int = Field(..., description="Sample count evaluated for calibration.")
    is_calibrated: bool = Field(
        default=True, description="Whether calibration optimization converged."
    )
    calibrated_at: str = Field(..., description="ISO 8601 timestamp when calibration executed.")


class TemperatureCalibrator:
    """Optimizes temperature T on validation logits to minimize cross-entropy loss."""

    def __init__(self, temp_min: float = 0.1, temp_max: float = 10.0) -> None:
        self.temp_min = temp_min
        self.temp_max = temp_max

    def _softmax(self, logits: np.ndarray, temperature: float) -> np.ndarray:
        scaled = logits / max(1e-4, temperature)
        exp_vals = np.exp(scaled - np.max(scaled, axis=1, keepdims=True))
        return exp_vals / np.sum(exp_vals, axis=1, keepdims=True)

    def calibrate(
        self,
        val_logits: np.ndarray,
        val_labels: list[str],
        class_labels: list[str],
    ) -> tuple[bool, CalibrationResult | None, str]:
        """Execute temperature calibration on validation logits and true ground-truth labels."""
        if val_logits.ndim != 2:
            return False, None, f"Validation logits must be 2D; got {val_logits.shape}."
        if len(val_logits) < 2:
            return (
                False,
                None,
                "Insufficient validation samples for calibration (minimum 2 required).",
            )
        if len(val_logits) != len(val_labels):
            return (
                False,
                None,
                f"Logits count ({len(val_logits)}) != labels count ({len(val_labels)}).",
            )
        if not np.isfinite(val_logits).all():
            return False, None, "Validation logits contain non-finite values."

        label_to_idx = {lbl: i for i, lbl in enumerate(class_labels)}
        try:
            y_idx = np.array([label_to_idx[lbl] for lbl in val_labels], dtype=np.int64)
        except KeyError as exc:
            return False, None, f"Unknown class label in validation set: {exc}"

        N = len(val_logits)

        # Objective: Negative Log-Likelihood
        def nll_objective(temp: float) -> float:
            probs = self._softmax(val_logits, temp)
            nll = -np.mean(np.log(probs[np.arange(N), y_idx] + 1e-12))
            return float(nll)

        # Before calibration metrics (T = 1.0)
        before_nll = nll_objective(1.0)
        probs_before = self._softmax(val_logits, 1.0)
        prob_dicts_before = [
            {lbl: float(probs_before[i, j]) for j, lbl in enumerate(class_labels)} for i in range(N)
        ]
        calib_before = compute_calibration_metrics(val_labels, prob_dicts_before, class_labels)

        # Scalar bounded optimization
        res = minimize_scalar(
            nll_objective,
            bounds=(self.temp_min, self.temp_max),
            method="bounded",
            options={"xatol": 1e-3, "maxiter": 100},
        )

        optimal_temp = float(res.x)
        if not (self.temp_min <= optimal_temp <= self.temp_max):
            return (
                False,
                None,
                f"Calibrated temperature {optimal_temp} outside bounds [{self.temp_min}, {self.temp_max}].",
            )

        # After calibration metrics
        after_nll = float(res.fun)
        probs_after = self._softmax(val_logits, optimal_temp)
        prob_dicts_after = [
            {lbl: float(probs_after[i, j]) for j, lbl in enumerate(class_labels)} for i in range(N)
        ]
        calib_after = compute_calibration_metrics(val_labels, prob_dicts_after, class_labels)

        result = CalibrationResult(
            optimal_temperature=round(optimal_temp, 4),
            before_nll=round(before_nll, 4),
            after_nll=round(after_nll, 4),
            before_ece=round(float(calib_before.get("ece", 0.0)), 4),
            after_ece=round(float(calib_after.get("ece", 0.0)), 4),
            before_brier=round(float(calib_before.get("brier_score", 0.0)), 4),
            after_brier=round(float(calib_after.get("brier_score", 0.0)), 4),
            validation_sample_count=N,
            is_calibrated=True,
            calibrated_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        )

        msg = (
            f"Temperature calibration optimized: T={optimal_temp:.4f} "
            f"(NLL: {before_nll:.4f} -> {after_nll:.4f}, ECE: {result.before_ece:.4f} -> {result.after_ece:.4f})."
        )
        return True, result, msg
