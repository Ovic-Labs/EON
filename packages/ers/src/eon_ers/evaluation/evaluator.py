"""Scientific evaluation runner and report generator for ERS emotion models."""

from __future__ import annotations

import hashlib
import os
import time
from typing import Any

from eon_ers.evaluation.dataset import KNOWN_PLACEHOLDER_CHECKSUMS
from eon_ers.evaluation.metrics import (
    compute_calibration_metrics,
    compute_classification_metrics,
    compute_confidence_distribution,
)
from eon_ers.models.manifest import ModelManifest
from eon_ers.models.validation_record import ModelValidationRecord
from eon_ers.types import EmotionCategory


class ModelEvaluator:
    """Scientific evaluation engine producing auditable validation records."""

    def __init__(
        self,
        labels: list[str] | None = None,
        confidence_threshold: float = 0.40,
        uncertainty_threshold: float = 0.60,
    ) -> None:
        self.labels = labels or [
            EmotionCategory.NEUTRAL.value,
            EmotionCategory.HAPPINESS.value,
            EmotionCategory.SADNESS.value,
            EmotionCategory.ANGER.value,
            EmotionCategory.FEAR.value,
            EmotionCategory.SURPRISE.value,
            EmotionCategory.DISGUST.value,
        ]
        self.confidence_threshold = confidence_threshold
        self.uncertainty_threshold = uncertainty_threshold

    def evaluate_predictions(
        self,
        y_true: list[str],
        predicted_probs: list[dict[str, float]],
        model_manifest: ModelManifest,
        dataset_name: str,
        dataset_split: str,
        dataset_license: str,
        evaluator_name: str = "OVIC Labs Scientific Qualification Suite",
        commercial_allowed: bool = False,
        commercial_restrictions: list[str] | None = None,
        evaluation_notes: list[str] | None = None,
    ) -> tuple[ModelValidationRecord, dict[str, Any]]:
        """Evaluate raw model predictions and generate a cryptographic validation record."""
        total_samples = len(y_true)
        if total_samples == 0:
            raise ValueError("Evaluation dataset cannot be empty.")

        # Determine discrete predictions and abstentions
        y_pred: list[str] = []
        abstained_count = 0

        for p_dict in predicted_probs:
            if not p_dict:
                y_pred.append(EmotionCategory.UNKNOWN.value)
                abstained_count += 1
                continue

            top_cat = max(p_dict, key=p_dict.get)  # type: ignore[arg-type]
            top_conf = p_dict[top_cat]

            # Check for uniform/uninformative baseline (e.g., all probs equal 1/K)
            k = len(self.labels)
            uniform_val = round(1.0 / k, 4)
            is_uniform = all(abs(val - uniform_val) < 0.01 for val in p_dict.values())

            if is_uniform or top_conf < self.confidence_threshold:
                y_pred.append(EmotionCategory.INSUFFICIENT_EVIDENCE.value)
                abstained_count += 1
            else:
                y_pred.append(top_cat)

        abstention_rate = round(abstained_count / total_samples, 4)

        # Compute classification metrics
        macro_summary, per_class, confusion_matrix = compute_classification_metrics(
            y_true, y_pred, self.labels
        )

        # Compute calibration metrics
        calib_summary = compute_calibration_metrics(y_true, predicted_probs, self.labels)

        # Compute confidence percentiles
        conf_dist = compute_confidence_distribution(predicted_probs)

        # Compute artifact SHA-256
        artifact_path = model_manifest.artifact_path
        artifact_sha256 = model_manifest.sha256_checksum
        if os.path.isfile(artifact_path):
            hasher = hashlib.sha256()
            with open(artifact_path, "rb") as f:
                while chunk := f.read(65536):
                    hasher.update(chunk)
            artifact_sha256 = hasher.hexdigest().lower()

        # Scientific qualification threshold criteria (Phase 3.1.5 non-negotiables):
        # A model is ONLY qualified as is_validated = True if:
        # 1. Macro-F1 >= 0.40, Balanced accuracy >= 0.40, and Accuracy >= 0.40
        # 2. Evaluation was conducted on empirical, non-synthetic datasets with sufficient samples (>= 10)
        # 3. Model weights and dataset provenance are strictly verified
        # 4. Actual inference was conducted (mock/uniform predictions rejected)
        # 5. Model artifact exists and SHA-256 integrity check passes with non-placeholder hash
        is_empirical_dataset = "synthetic" not in dataset_name.lower() and total_samples >= 10

        # Detect uniform/mock predictions
        k_classes = len(self.labels)
        uniform_target = round(1.0 / k_classes, 4)
        is_mock_evaluation = total_samples > 0 and all(
            bool(p_dict) and all(abs(val - uniform_target) < 0.01 for val in p_dict.values())
            for p_dict in predicted_probs
        )
        actual_inference_conducted = not is_mock_evaluation and abstention_rate < 1.0

        has_provenance = (
            model_manifest.provenance_status.upper() == "VERIFIED"
            and dataset_license.strip().upper() not in ("", "UNVERIFIED")
            and model_manifest.training_dataset_provenance.upper() != "UNVERIFIED"
        )

        has_valid_manifest_checksum = (
            model_manifest.sha256_checksum.lower() not in KNOWN_PLACEHOLDER_CHECKSUMS
        )
        artifact_integrity_passed = (
            has_valid_manifest_checksum and model_manifest.verify_integrity()
        )

        accuracy_acceptable = (
            macro_summary.get("macro_f1", 0.0) >= 0.40
            and macro_summary.get("balanced_accuracy", 0.0) >= 0.40
            and macro_summary.get("accuracy", 0.0) >= 0.40
        )

        is_validated = bool(
            is_empirical_dataset
            and actual_inference_conducted
            and has_provenance
            and artifact_integrity_passed
            and accuracy_acceptable
        )

        notes = list(evaluation_notes) if evaluation_notes else []
        if not is_empirical_dataset:
            notes.append(
                "Evaluation used synthetic validation fixtures or insufficient sample size; not empirical accuracy qualification."
            )
        if not actual_inference_conducted:
            notes.append(
                "Mock or uniform predictions detected; actual empirical model inference required."
            )
        if not has_provenance:
            notes.append(
                "Model weights, training dataset, or evaluation dataset have unverified provenance; prohibited from production validation."
            )
        if not artifact_integrity_passed:
            notes.append(
                f"Model artifact integrity verification failed: weights file missing, placeholder hash, or SHA-256 does not match manifest digest '{model_manifest.sha256_checksum}'."
            )
        if not accuracy_acceptable:
            notes.append(
                f"Model failed accuracy thresholds (Macro-F1 {macro_summary.get('macro_f1', 0.0)} < 0.40). "
                "Classifications must be suppressed as INSUFFICIENT_EVIDENCE."
            )

        record_id = f"VAL-{model_manifest.model_id}-{int(time.time())}"
        val_record = ModelValidationRecord(
            record_id=record_id,
            model_id=model_manifest.model_id,
            model_version=model_manifest.version,
            artifact_sha256=artifact_sha256,
            is_validated=is_validated,
            training_dataset=model_manifest.training_dataset_provenance,
            training_dataset_version="1.0.0",
            dataset_license=dataset_license,
            commercial_use_allowed=commercial_allowed,
            commercial_use_restrictions=commercial_restrictions
            or ["Research and testing baseline only."],
            preprocessing_specification=model_manifest.input_specification,
            label_mapping=self.labels,
            evaluation_dataset=dataset_name,
            evaluation_split=dataset_split,
            evaluation_script="eon_ers.evaluation.evaluator",
            evaluation_script_version="1.0.0",
            evaluation_metrics=macro_summary,
            per_class_metrics=per_class,
            calibration_metrics=calib_summary,
            confidence_distribution=conf_dist,
            abstention_rate=abstention_rate,
            evaluator=evaluator_name,
            validation_timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            validation_notes=notes,
        )

        full_report: dict[str, Any] = {
            "validation_record": val_record.model_dump(),
            "confusion_matrix": confusion_matrix,
            "labels": self.labels,
        }

        return val_record, full_report

    def generate_markdown_report(self, report: dict[str, Any]) -> str:
        """Render a formatted human-readable Markdown evaluation report."""
        record = report["validation_record"]
        cm = report["confusion_matrix"]
        labels = report["labels"]

        md: list[str] = []
        md.append(f"# Model Evaluation & Qualification Report: {record['model_id']}")
        md.append(f"**Record ID:** `{record['record_id']}`  ")
        md.append(
            f"**Validation Status:** **{'VALIDATED' if record['is_validated'] else 'UNVALIDATED / RESTRICTED'}**  "
        )
        md.append(f"**Evaluator:** {record['evaluator']}  ")
        md.append(f"**Timestamp:** {record['validation_timestamp']}  ")
        md.append(f"**Artifact SHA-256:** `{record['artifact_sha256']}`  \n")

        md.append("## 1. Governance & Provenance")
        md.append(f"- **Training Dataset:** {record['training_dataset']}")
        md.append(
            f"- **Evaluation Dataset:** {record['evaluation_dataset']} (`{record['evaluation_split']}` split)"
        )
        md.append(f"- **Dataset License:** {record['dataset_license']}")
        md.append(f"- **Commercial Use Allowed:** `{record['commercial_use_allowed']}`")
        if record["commercial_use_restrictions"]:
            md.append("- **Restrictions:**")
            for r in record["commercial_use_restrictions"]:
                md.append(f"  - {r}")
        md.append("")

        md.append("## 2. Macro Classification Metrics")
        metrics = record["evaluation_metrics"]
        md.append("| Metric | Score |")
        md.append("|---|:---:|")
        for k, v in metrics.items():
            md.append(f"| **{k.replace('_', ' ').title()}** | `{v}` |")
        md.append(f"| **Abstention Rate** | `{record['abstention_rate']}` |")
        md.append("")

        md.append("## 3. Calibration Metrics")
        calib = record["calibration_metrics"]
        md.append(f"- **Expected Calibration Error (ECE):** `{calib.get('ece', 0.0)}`")
        md.append(f"- **Brier Score:** `{calib.get('brier_score', 0.0)}`")
        md.append("")

        md.append("## 4. Per-Class Performance")
        md.append("| Emotion Category | Precision | Recall | F1-Score | Support |")
        md.append("|---|:---:|:---:|:---:|:---:|")
        for cat, c_metrics in record["per_class_metrics"].items():
            md.append(
                f"| `{cat}` | {c_metrics['precision']:.4f} | {c_metrics['recall']:.4f} | {c_metrics['f1']:.4f} | {int(c_metrics['support'])} |"
            )
        md.append("")

        md.append("## 5. Confusion Matrix")
        header = "| True \\ Pred | " + " | ".join([f"`{lbl}`" for lbl in labels]) + " |"
        sep = "|---|" + "|".join([":---:" for _ in labels]) + "|"
        md.append(header)
        md.append(sep)
        for i, row_label in enumerate(labels):
            row_vals = " | ".join([str(val) for val in cm[i]])
            md.append(f"| `{row_label}` | {row_vals} |")
        md.append("")

        md.append("## 6. Validation Notes & Limitations")
        for note in record["validation_notes"]:
            md.append(f"- {note}")
        md.append("")

        return "\n".join(md)
