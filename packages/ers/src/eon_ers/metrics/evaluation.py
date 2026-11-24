"""Reproducible evaluation framework for ERS emotion models."""

from __future__ import annotations

from typing import Any

import numpy as np


class ModelEvaluationFramework:
    """Computes rigorous machine-learning evaluation metrics for affective models."""

    @staticmethod
    def evaluate(
        y_true: list[str],
        y_pred: list[str],
        probabilities: list[dict[str, float]],
        classes: list[str] | None = None,
        num_calibration_bins: int = 10,
    ) -> dict[str, Any]:
        """Compute comprehensive multiclass classification and calibration metrics."""
        n = len(y_true)
        if n == 0 or len(y_pred) != n or len(probabilities) != n:
            raise ValueError("Mismatched sample counts in evaluation inputs")

        if classes is None:
            classes = sorted(set(y_true) | set(y_pred))

        class_to_idx = {c: i for i, c in enumerate(classes)}
        k = len(classes)

        # 1. Confusion Matrix
        conf_matrix = np.zeros((k, k), dtype=int)
        for yt, yp in zip(y_true, y_pred):
            if yt in class_to_idx and yp in class_to_idx:
                conf_matrix[class_to_idx[yt], class_to_idx[yp]] += 1

        # 2. Per-class Precision, Recall, F1
        per_class: dict[str, dict[str, float]] = {}
        f1_scores: list[float] = []

        for i, c in enumerate(classes):
            tp = float(conf_matrix[i, i])
            fp = float(np.sum(conf_matrix[:, i]) - tp)
            fn = float(np.sum(conf_matrix[i, :]) - tp)

            precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            f1 = (
                (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
            )
            f1_scores.append(f1)

            per_class[c] = {
                "precision": round(precision, 4),
                "recall": round(recall, 4),
                "f1_score": round(f1, 4),
                "support": int(np.sum(conf_matrix[i, :])),
            }

        macro_f1 = float(np.mean(f1_scores)) if f1_scores else 0.0
        accuracy = float(np.trace(conf_matrix)) / float(n) if n > 0 else 0.0

        # 3. Brier Score: Mean squared error between one-hot labels and predicted probabilities
        brier_sum = 0.0
        confidences: list[float] = []
        corrects: list[bool] = []

        for yt, yp, probs in zip(y_true, y_pred, probabilities):
            y_onehot = np.zeros(k, dtype=np.float64)
            if yt in class_to_idx:
                y_onehot[class_to_idx[yt]] = 1.0

            p_vec = np.array([probs.get(c, 0.0) for c in classes], dtype=np.float64)
            brier_sum += np.sum((p_vec - y_onehot) ** 2)

            top_conf = max(probs.values()) if probs else 0.0
            confidences.append(top_conf)
            corrects.append(yt == yp)

        brier_score = float(brier_sum / n) if n > 0 else 0.0

        # 4. Expected Calibration Error (ECE)
        conf_arr = np.array(confidences, dtype=np.float64)
        corr_arr = np.array(corrects, dtype=np.float64)
        bins = np.linspace(0.0, 1.0, num_calibration_bins + 1)
        ece = 0.0

        for b in range(num_calibration_bins):
            bin_lower = bins[b]
            bin_upper = bins[b + 1]
            in_bin = (conf_arr > bin_lower) & (conf_arr <= bin_upper)
            prop_in_bin = np.mean(in_bin)
            if prop_in_bin > 0:
                acc_in_bin = np.mean(corr_arr[in_bin])
                avg_conf_in_bin = np.mean(conf_arr[in_bin])
                ece += np.abs(acc_in_bin - avg_conf_in_bin) * prop_in_bin

        # 5. Abstention rate
        abstentions = sum(1 for yp in y_pred if yp in ("insufficient_evidence", "unknown"))
        abstention_rate = float(abstentions / n) if n > 0 else 0.0

        return {
            "total_samples": n,
            "accuracy": round(accuracy, 4),
            "macro_f1": round(macro_f1, 4),
            "brier_score": round(brier_score, 4),
            "expected_calibration_error": round(float(ece), 4),
            "abstention_rate": round(abstention_rate, 4),
            "classes": classes,
            "per_class": per_class,
            "confusion_matrix": conf_matrix.tolist(),
        }
