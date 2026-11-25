"""Scientific evaluation runner and report generator for ERS emotion models."""

from __future__ import annotations

import hashlib
import math
import os
import time
from typing import Any

from eon_ers.evaluation.dataset import KNOWN_PLACEHOLDER_CHECKSUMS
from eon_ers.evaluation.metrics import (
    _validate_labels_list,
    compute_calibration_metrics,
    compute_classification_metrics,
    compute_confidence_distribution,
)
from eon_ers.evaluation.proof import (
    EvaluationExecutionProof,
    SigningKeyPair,
    TrustedKeyRegistry,
)
from eon_ers.models.manifest import ModelManifest
from eon_ers.models.validation_record import ModelValidationRecord
from eon_ers.types import EmotionCategory

__all__ = [
    "EvaluationExecutionProof",
    "ModelEvaluator",
    "SigningKeyPair",
    "TrustedKeyRegistry",
]


class ModelEvaluator:
    """Scientific evaluation engine producing auditable validation records."""

    def __init__(
        self,
        labels: list[str] | None = None,
        confidence_threshold: float = 0.40,
        uncertainty_threshold: float = 0.60,
    ) -> None:
        self.labels = (
            list(labels)
            if labels is not None
            else [
                EmotionCategory.NEUTRAL.value,
                EmotionCategory.HAPPINESS.value,
                EmotionCategory.SADNESS.value,
                EmotionCategory.ANGER.value,
                EmotionCategory.FEAR.value,
                EmotionCategory.SURPRISE.value,
                EmotionCategory.DISGUST.value,
            ]
        )
        _validate_labels_list(self.labels)
        if not (0.0 <= confidence_threshold <= 1.0):
            raise ValueError(
                f"confidence_threshold must be in [0.0, 1.0], got {confidence_threshold}."
            )
        if not (0.0 <= uncertainty_threshold <= 1.0):
            raise ValueError(
                f"uncertainty_threshold must be in [0.0, 1.0], got {uncertainty_threshold}."
            )
        self.confidence_threshold = confidence_threshold
        self.uncertainty_threshold = uncertainty_threshold

    def _validate_evaluation_inputs(
        self,
        y_true: list[str],
        predicted_probs: list[dict[str, float]],
        model_manifest: ModelManifest,
    ) -> None:
        """Strictly validate sample counts, labels, probability distributions, and manifest dimensions."""
        if not isinstance(y_true, list) or not isinstance(predicted_probs, list):
            raise ValueError("y_true and predicted_probs must be lists.")

        total_samples = len(y_true)
        if total_samples == 0:
            raise ValueError("Evaluation dataset cannot be empty.")

        if total_samples != len(predicted_probs):
            raise ValueError(
                f"Mismatched sample counts: len(y_true)={total_samples} != "
                f"len(predicted_probs)={len(predicted_probs)}."
            )

        expected_label_set = set(self.labels)
        for idx, lbl in enumerate(y_true):
            if not isinstance(lbl, str) or lbl not in expected_label_set:
                raise ValueError(
                    f"Unsupported ground-truth label {lbl!r} at index {idx}; "
                    f"expected one of {self.labels}."
                )

        # Validate output manifest dimensions if specified
        out_spec = model_manifest.output_specification
        out_shape = out_spec.get("shape")
        if out_shape is not None:
            if (
                not isinstance(out_shape, list)
                or len(out_shape) == 0
                or not isinstance(out_shape[-1], int)
                or out_shape[-1] != len(self.labels)
            ):
                raise ValueError(
                    f"Manifest output dimension mismatch: output_specification.shape={out_shape} "
                    f"incompatible with {len(self.labels)} evaluation labels."
                )

        manifest_classes = out_spec.get("classes")
        if manifest_classes is not None and list(manifest_classes) != self.labels:
            raise ValueError(
                f"Manifest output class mismatch: {manifest_classes} != {self.labels}."
            )

        for idx, p_dict in enumerate(predicted_probs):
            if not isinstance(p_dict, dict) or not p_dict:
                raise ValueError(
                    f"Prediction probability map at index {idx} cannot be empty or non-dict."
                )

            keys = set(p_dict.keys())
            missing = expected_label_set - keys
            extra = keys - expected_label_set
            if missing or extra:
                raise ValueError(
                    f"Invalid probability keys at index {idx}: "
                    f"missing={sorted(missing)}, unsupported={sorted(extra)}."
                )

            prob_sum = 0.0
            for k, val in p_dict.items():
                if (
                    isinstance(val, bool)
                    or not isinstance(val, (int, float))
                    or not math.isfinite(val)
                ):
                    raise ValueError(
                        f"Non-finite or invalid probability {val!r} for class '{k}' at index {idx}."
                    )
                if val < 0.0 or val > 1.0:
                    raise ValueError(
                        f"Probability out of bounds [0.0, 1.0] for class '{k}' at index {idx}: {val}."
                    )
                prob_sum += float(val)

            if abs(prob_sum - 1.0) > 0.02:
                raise ValueError(
                    f"Probability distribution at index {idx} sums to {prob_sum:.6f}, "
                    f"expected 1.0 within +/-0.02 tolerance."
                )

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
        execution_proof: EvaluationExecutionProof | None = None,
        key_registry: TrustedKeyRegistry | None = None,
        expected_dataset_archive_sha256: str | None = None,
        pipeline_stages_ok: bool = True,
    ) -> tuple[ModelValidationRecord, dict[str, Any]]:
        """Evaluate raw model predictions and generate a cryptographic validation record."""
        self._validate_evaluation_inputs(y_true, predicted_probs, model_manifest)
        total_samples = len(y_true)

        # Determine discrete predictions and abstentions using strict paired iteration
        y_pred: list[str] = []
        abstained_count = 0

        for _yt, p_dict in zip(y_true, predicted_probs, strict=True):
            top_cat = max(p_dict, key=p_dict.get)  # type: ignore[arg-type]
            top_conf = p_dict[top_cat]

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
        artifact_sha256 = model_manifest.sha256_checksum.strip().lower()
        if os.path.isfile(artifact_path):
            hasher = hashlib.sha256()
            with open(artifact_path, "rb") as f:
                while chunk := f.read(65536):
                    hasher.update(chunk)
            artifact_sha256 = hasher.hexdigest().lower()

        # Scientific qualification criteria:
        is_empirical_dataset = (
            "synthetic" not in dataset_name.lower()
            and "synthetic" not in model_manifest.training_dataset_provenance.lower()
            and total_samples >= 10
        )

        k_classes = len(self.labels)
        uniform_target = round(1.0 / k_classes, 4)
        is_mock_evaluation = all(
            all(abs(val - uniform_target) < 0.01 for val in p_dict.values())
            for p_dict in predicted_probs
        )
        actual_inference_conducted = not is_mock_evaluation and abstention_rate < 1.0

        has_provenance = (
            model_manifest.provenance_status.upper() == "VERIFIED"
            and dataset_license.strip().upper() not in ("", "UNVERIFIED")
            and model_manifest.training_dataset_provenance.upper() != "UNVERIFIED"
        )

        has_valid_manifest_checksum = (
            model_manifest.sha256_checksum.strip().lower() not in KNOWN_PLACEHOLDER_CHECKSUMS
        )
        artifact_integrity_passed = (
            has_valid_manifest_checksum and model_manifest.verify_integrity()
        )

        accuracy_acceptable = (
            macro_summary.get("macro_f1", 0.0) >= 0.40
            and macro_summary.get("balanced_accuracy", 0.0) >= 0.40
            and macro_summary.get("accuracy", 0.0) >= 0.40
        )

        proof_reason = ""
        if execution_proof is None:
            has_valid_execution_proof = False
            proof_reason = (
                "Evaluation lacks verifiable execution proof from a trusted pipeline; "
                "scientific qualification denied."
            )
        else:
            has_valid_execution_proof, proof_reason = execution_proof.verify_detailed(
                expected_artifact_sha256=artifact_sha256,
                key_registry=key_registry,
                expected_dataset_archive_sha256=expected_dataset_archive_sha256,
            )

        is_validated = bool(
            pipeline_stages_ok
            and is_empirical_dataset
            and actual_inference_conducted
            and has_provenance
            and artifact_integrity_passed
            and accuracy_acceptable
            and has_valid_execution_proof
        )

        notes = list(evaluation_notes) if evaluation_notes else []
        if not pipeline_stages_ok:
            notes.append(
                "One or more upstream training/verification pipeline stages failed; model cannot be qualified."
            )
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
        if not has_valid_execution_proof:
            notes.append(proof_reason)

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
            dataset_archive_sha256=(
                execution_proof.dataset_archive_sha256 if execution_proof else ""
            ),
            execution_proof_key_id=(execution_proof.key_id if execution_proof else ""),
            execution_proof_algorithm=(
                execution_proof.signature_algorithm if execution_proof else ""
            ),
            execution_proof_signature=(execution_proof.proof_signature if execution_proof else ""),
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
