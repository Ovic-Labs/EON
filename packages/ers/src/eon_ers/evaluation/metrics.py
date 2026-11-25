"""Empirical evaluation metrics and calibration calculations for emotion models.

Computes accuracy, balanced accuracy, macro precision/recall/F1, per-class metrics,
confusion matrix, Brier score, Expected Calibration Error (ECE), and abstention rates.
Rejects empty datasets, mismatched sample counts, unsupported labels, and non-finite inputs.
"""

from __future__ import annotations

import math

import numpy as np

from eon_ers.types import EmotionCategory

ABSTENTION_LABELS: frozenset[str] = frozenset(
    {
        EmotionCategory.UNKNOWN.value,
        EmotionCategory.INSUFFICIENT_EVIDENCE.value,
    }
)


def _validate_labels_list(labels: list[str]) -> dict[str, int]:
    if not labels:
        raise ValueError("Evaluation label list cannot be empty.")
    seen: dict[str, int] = {}
    for idx, lbl in enumerate(labels):
        if not isinstance(lbl, str) or not lbl.strip():
            raise ValueError(f"Evaluation label at index {idx} must be a non-empty string.")
        if lbl in seen:
            raise ValueError(f"Duplicate label '{lbl}' found in evaluation label list.")
        seen[lbl] = idx
    return seen


def compute_confusion_matrix(
    y_true: list[str], y_pred: list[str], labels: list[str]
) -> list[list[int]]:
    """Compute 2D confusion matrix with fixed class ordering and strict length/label checks."""
    label_to_idx = _validate_labels_list(labels)
    if len(y_true) == 0:
        raise ValueError("y_true cannot be empty.")
    if len(y_true) != len(y_pred):
        raise ValueError(
            f"Mismatched sample counts: len(y_true)={len(y_true)} != len(y_pred)={len(y_pred)}."
        )

    k = len(labels)
    cm = [[0 for _ in range(k)] for _ in range(k)]

    for idx, (t, p) in enumerate(zip(y_true, y_pred, strict=True)):
        if t not in label_to_idx:
            raise ValueError(
                f"Unsupported ground-truth label '{t}' at index {idx}; expected one of {labels}."
            )
        if p not in label_to_idx and p not in ABSTENTION_LABELS:
            raise ValueError(
                f"Unsupported predicted label '{p}' at index {idx}; expected one of {labels} or abstention."
            )
        if p in label_to_idx:
            cm[label_to_idx[t]][label_to_idx[p]] += 1

    return cm


def compute_classification_metrics(
    y_true: list[str],
    y_pred: list[str],
    labels: list[str],
) -> tuple[dict[str, float], dict[str, dict[str, float]], list[list[int]]]:
    """Compute macro and per-class precision, recall, and F1 scores."""
    cm = compute_confusion_matrix(y_true, y_pred, labels)
    cm_arr = np.array(cm, dtype=np.int64)

    total_samples = len(y_true)
    correct_samples = int(np.trace(cm_arr))
    accuracy = float(correct_samples / total_samples) if total_samples > 0 else 0.0

    per_class: dict[str, dict[str, float]] = {}
    recalls: list[float] = []
    precisions: list[float] = []
    f1s: list[float] = []

    for i, label in enumerate(labels):
        tp = float(cm_arr[i, i])
        fp = float(np.sum(cm_arr[:, i]) - tp)
        fn = float(np.sum(cm_arr[i, :]) - tp)
        support = int(np.sum(cm_arr[i, :]))

        prec = float(tp / (tp + fp)) if (tp + fp) > 0 else 0.0
        rec = float(tp / (tp + fn)) if (tp + fn) > 0 else 0.0
        f1 = float((2 * prec * rec) / (prec + rec)) if (prec + rec) > 0 else 0.0

        per_class[label] = {
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "f1": round(f1, 4),
            "support": float(support),
        }
        precisions.append(prec)
        recalls.append(rec)
        f1s.append(f1)

    balanced_accuracy = float(np.mean(recalls)) if recalls else 0.0
    macro_precision = float(np.mean(precisions)) if precisions else 0.0
    macro_recall = float(np.mean(recalls)) if recalls else 0.0
    macro_f1 = float(np.mean(f1s)) if f1s else 0.0

    macro_summary = {
        "accuracy": round(accuracy, 4),
        "balanced_accuracy": round(balanced_accuracy, 4),
        "macro_precision": round(macro_precision, 4),
        "macro_recall": round(macro_recall, 4),
        "macro_f1": round(macro_f1, 4),
        "total_samples": float(total_samples),
    }

    return macro_summary, per_class, cm


def compute_calibration_metrics(
    y_true: list[str],
    predicted_probs: list[dict[str, float]],
    labels: list[str],
    n_bins: int = 10,
) -> dict[str, float]:
    """Compute Expected Calibration Error (ECE) and Brier Score with strict validation."""
    label_to_idx = _validate_labels_list(labels)
    if len(y_true) == 0:
        raise ValueError("Cannot compute calibration metrics on an empty dataset.")
    if len(y_true) != len(predicted_probs):
        raise ValueError(
            f"Mismatched sample counts: len(y_true)={len(y_true)} != len(predicted_probs)={len(predicted_probs)}."
        )
    if n_bins < 1:
        raise ValueError(f"n_bins must be >= 1, got {n_bins}.")

    k = len(labels)
    n = len(y_true)

    brier_sum = 0.0
    confidences: list[float] = []
    correct_flags: list[bool] = []

    for idx, (t, p_dict) in enumerate(zip(y_true, predicted_probs, strict=True)):
        if t not in label_to_idx:
            raise ValueError(
                f"Unsupported ground-truth label '{t}' at index {idx}; expected one of {labels}."
            )
        if not isinstance(p_dict, dict) or not p_dict:
            raise ValueError(f"Invalid empty or non-dict probability map at index {idx}.")

        for key, val in p_dict.items():
            if key not in label_to_idx:
                raise ValueError(
                    f"Unsupported emotion key '{key}' in prediction at index {idx}; expected subset of {labels}."
                )
            if isinstance(val, bool) or not isinstance(val, (int, float)) or not math.isfinite(val):
                raise ValueError(
                    f"Non-finite or invalid probability value {val!r} for '{key}' at index {idx}."
                )
            if val < 0.0 or val > 1.0:
                raise ValueError(
                    f"Probability out of bounds [0, 1] for '{key}' at index {idx}: {val}."
                )

        p_vec = np.array([float(p_dict.get(lbl, 0.0)) for lbl in labels], dtype=np.float64)
        p_sum = float(np.sum(p_vec))
        if p_sum <= 0.0:
            raise ValueError(f"Probability distribution sums to non-positive value at index {idx}.")
        p_vec = p_vec / p_sum

        t_idx = label_to_idx[t]
        y_vec = np.zeros(k, dtype=np.float64)
        y_vec[t_idx] = 1.0

        brier_sum += float(np.sum((p_vec - y_vec) ** 2))

        top_pred_idx = int(np.argmax(p_vec))
        top_conf = float(p_vec[top_pred_idx])
        confidences.append(top_conf)
        correct_flags.append(top_pred_idx == t_idx)

    brier_score = float(brier_sum / n)

    bins = np.linspace(0.0, 1.0, n_bins + 1)
    ece = 0.0

    conf_arr = np.array(confidences)
    corr_arr = np.array(correct_flags)

    for b in range(n_bins):
        bin_lower = bins[b]
        bin_upper = bins[b + 1]

        in_bin = (
            (conf_arr > bin_lower) & (conf_arr <= bin_upper)
            if b > 0
            else (conf_arr >= bin_lower) & (conf_arr <= bin_upper)
        )
        bin_size = int(np.sum(in_bin))

        if bin_size > 0:
            bin_acc = float(np.mean(corr_arr[in_bin]))
            bin_conf = float(np.mean(conf_arr[in_bin]))
            ece += (bin_size / n) * abs(bin_acc - bin_conf)

    return {
        "ece": round(float(ece), 4),
        "brier_score": round(float(brier_score), 4),
    }


def compute_confidence_distribution(
    predicted_probs: list[dict[str, float]],
) -> dict[str, float]:
    """Calculate descriptive distribution percentiles for model confidence."""
    if not predicted_probs:
        raise ValueError("Cannot compute confidence distribution on empty predictions.")

    confs: list[float] = []
    for idx, p in enumerate(predicted_probs):
        if not isinstance(p, dict) or not p:
            raise ValueError(f"Prediction at index {idx} is empty or invalid.")
        for key, val in p.items():
            if isinstance(val, bool) or not isinstance(val, (int, float)) or not math.isfinite(val):
                raise ValueError(f"Non-finite confidence value {val!r} for '{key}' at index {idx}.")
            if val < 0.0 or val > 1.0:
                raise ValueError(f"Out-of-bounds confidence {val} for '{key}' at index {idx}.")
        confs.append(float(max(p.values())))

    arr = np.array(confs, dtype=np.float64)

    return {
        "p25": round(float(np.percentile(arr, 25)), 4),
        "p50": round(float(np.percentile(arr, 50)), 4),
        "p75": round(float(np.percentile(arr, 75)), 4),
        "p95": round(float(np.percentile(arr, 95)), 4),
        "mean": round(float(np.mean(arr)), 4),
    }
