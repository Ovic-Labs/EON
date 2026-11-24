"""Unit tests for scientific evaluation metrics and evaluator qualification thresholds."""

from __future__ import annotations

from pathlib import Path

from eon_ers.evaluation.evaluator import ModelEvaluator
from eon_ers.evaluation.metrics import (
    compute_calibration_metrics,
    compute_classification_metrics,
    compute_confidence_distribution,
    compute_confusion_matrix,
)
from eon_ers.models.manifest import ModelManifest

LABELS = ["neutral", "happiness", "sadness", "anger", "fear", "surprise", "disgust"]


def test_confusion_matrix_and_macro_metrics() -> None:
    """Verify confusion matrix, balanced accuracy, and macro F1 calculations."""
    y_true = ["neutral", "neutral", "happiness", "happiness", "sadness"]
    y_pred = ["neutral", "happiness", "happiness", "happiness", "sadness"]

    cm = compute_confusion_matrix(y_true, y_pred, LABELS)
    assert len(cm) == 7
    assert len(cm[0]) == 7
    # 1 neutral correctly predicted, 1 neutral misclassified as happiness
    neutral_idx = LABELS.index("neutral")
    happy_idx = LABELS.index("happiness")
    assert cm[neutral_idx][neutral_idx] == 1
    assert cm[neutral_idx][happy_idx] == 1

    macro, per_class, _ = compute_classification_metrics(y_true, y_pred, LABELS)
    assert macro["accuracy"] == 0.8
    assert macro["total_samples"] == 5.0
    assert "precision" in per_class["neutral"]
    assert "recall" in per_class["happiness"]
    assert "f1" in per_class["sadness"]


def test_calibration_metrics_ece_and_brier() -> None:
    """Verify Expected Calibration Error (ECE) and Brier Score calculations."""
    y_true = ["neutral", "happiness"]
    probs = [
        {
            "neutral": 0.9,
            "happiness": 0.1,
            "sadness": 0.0,
            "anger": 0.0,
            "fear": 0.0,
            "surprise": 0.0,
            "disgust": 0.0,
        },
        {
            "neutral": 0.2,
            "happiness": 0.8,
            "sadness": 0.0,
            "anger": 0.0,
            "fear": 0.0,
            "surprise": 0.0,
            "disgust": 0.0,
        },
    ]

    metrics = compute_calibration_metrics(y_true, probs, LABELS)
    assert "ece" in metrics
    assert "brier_score" in metrics
    assert metrics["ece"] >= 0.0
    assert metrics["brier_score"] >= 0.0


def test_confidence_distribution() -> None:
    """Verify confidence percentile calculations."""
    probs = [
        {"neutral": 0.5, "happiness": 0.5},
        {"neutral": 0.8, "happiness": 0.2},
        {"neutral": 0.95, "happiness": 0.05},
        {"neutral": 0.3, "happiness": 0.7},
    ]
    dist = compute_confidence_distribution(probs)
    assert "p50" in dist
    assert "p95" in dist
    assert "mean" in dist
    assert dist["p95"] >= dist["p50"]


def test_model_evaluator_qualification_rules(tmp_path: Path) -> None:
    """Verify ModelEvaluator enforces strict qualification standards."""
    evaluator = ModelEvaluator(labels=LABELS)

    # Create dummy manifest with unverified provenance
    manifest_data = {
        "model_id": "test-model-eval",
        "name": "Test Model",
        "version": "1.0.0",
        "modality": "facial",
        "framework": "onnx",
        "artifact_path": str(tmp_path / "dummy.onnx"),
        "sha256_checksum": "a" * 64,
        "license": "UNVERIFIED",
        "commercial_use_allowed": False,
        "commercial_use_status": "RESTRICTED",
        "provenance_status": "UNVERIFIED",
        "training_dataset_provenance": "UNVERIFIED",
        "training_procedure": "UNVERIFIED",
        "validation_status": "UNVERIFIED",
        "license_evidence": "UNVERIFIED",
        "source": "OVIC Test",
        "input_specification": {"shape": [1, 1, 64, 64]},
        "output_specification": {"shape": [1, 7], "classes": LABELS},
        "cpu_supported": True,
        "accelerator_support": ["CPUExecutionProvider"],
        "known_limitations": ["Testing only."],
    }
    manifest = ModelManifest.model_validate(manifest_data)

    y_true = ["neutral", "happiness", "sadness", "anger", "fear", "surprise", "disgust"]
    # Uniform uninformative predictions
    uniform_prob = {cat: 1.0 / 7.0 for cat in LABELS}
    predicted_probs = [uniform_prob for _ in y_true]

    record, full_report = evaluator.evaluate_predictions(
        y_true=y_true,
        predicted_probs=predicted_probs,
        model_manifest=manifest,
        dataset_name="synthetic_test",
        dataset_split="test",
        dataset_license="Proprietary Test",
    )

    # Must fail qualification because: synthetic dataset, unverified provenance, low F1
    assert record.is_validated is False
    assert record.abstention_rate == 1.0
    assert any("unverified provenance" in note.lower() for note in record.validation_notes)
    assert any("synthetic validation fixtures" in note.lower() for note in record.validation_notes)

    # Generate markdown report and ensure it formats without error
    md = evaluator.generate_markdown_report(full_report)
    assert "# Model Evaluation & Qualification Report" in md
    assert "UNVALIDATED / RESTRICTED" in md
