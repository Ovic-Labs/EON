"""Empirical evaluation metrics and calibration calculations for emotion models.

Computes accuracy, balanced accuracy, macro precision/recall/F1, per-class metrics,
confusion matrix, Brier score, Expected Calibration Error (ECE), and abstention rates.
"""

from __future__ import annotations

import numpy as np


def compute_confusion_matrix(
    y_true: list[str], y_pred: list[str], labels: list[str]
) -> list[list[int]]:
    """Compute 2D confusion matrix with fixed class ordering."""
    label_to_idx = {lbl: i for i, lbl in enumerate(labels)}
    k = len(labels)
    cm = [[0 for _ in range(k)] for _ in range(k)]

    for t, p in zip(y_true, y_pred):
        if t in label_to_idx and p in label_to_idx:
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
    """Compute Expected Calibration Error (ECE) and Brier Score.

    ECE measures the absolute divergence between confidence and empirical accuracy.
    Brier Score measures the mean squared error of predicted probability distributions.
    """
    if not y_true or not predicted_probs:
        return {"ece": 0.0, "brier_score": 0.0}

    label_to_idx = {lbl: i for i, lbl in enumerate(labels)}
    k = len(labels)
    n = len(y_true)

    # 1. Brier Score: (1/N) * sum_i sum_k (p_ik - y_ik)^2
    brier_sum = 0.0
    confidences: list[float] = []
    correct_flags: list[bool] = []

    for t, p_dict in zip(y_true, predicted_probs):
        p_vec = np.array([p_dict.get(lbl, 0.0) for lbl in labels], dtype=np.float64)
        # Normalize in case probabilities don't sum to 1.0
        p_sum = np.sum(p_vec)
        if p_sum > 0:
            p_vec = p_vec / p_sum

        t_idx = label_to_idx.get(t, -1)
        y_vec = np.zeros(k, dtype=np.float64)
        if t_idx >= 0:
            y_vec[t_idx] = 1.0

        brier_sum += float(np.sum((p_vec - y_vec) ** 2))

        top_pred_idx = int(np.argmax(p_vec))
        top_conf = float(p_vec[top_pred_idx])
        confidences.append(top_conf)
        correct_flags.append(top_pred_idx == t_idx)

    brier_score = float(brier_sum / n)

    # 2. Expected Calibration Error (ECE)
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
        return {"p25": 0.0, "p50": 0.0, "p75": 0.0, "p95": 0.0, "mean": 0.0}

    confs = [max(p.values()) if p else 0.0 for p in predicted_probs]
    arr = np.array(confs, dtype=np.float64)

    return {
        "p25": round(float(np.percentile(arr, 25)), 4),
        "p50": round(float(np.percentile(arr, 50)), 4),
        "p75": round(float(np.percentile(arr, 75)), 4),
        "p95": round(float(np.percentile(arr, 95)), 4),
        "mean": round(float(np.mean(arr)), 4),
    }
