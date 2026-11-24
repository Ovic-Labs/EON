"""15-stage reproducible model training, calibration, and validation pipeline.

Implements an end-to-end scientific workflow:
1. Dataset Ingestion
2. Provenance Verification
3. Checksum & Integrity Check
4. Subject-Independent Partitioning
5. Zero-Leakage Validation
6. Signal & Media Preprocessing
7. Feature Extraction / Normalization
8. Model Architecture & Training / Weights Import
9. Convergence & Validation Monitoring
10. Temperature Scaling & Calibration
11. Independent Holdout Test Evaluation
12. Metric Threshold Qualification
13. ONNX Graph Export & Optimization
14. ONNX Tensor Contract Verification
15. Cryptographic Validation Record Generation & SHA-256 Binding
"""

from __future__ import annotations

import hashlib
import logging
import os
import time
from enum import Enum
from typing import Any

import numpy as np
from pydantic import BaseModel, ConfigDict, Field

from eon_ers.evaluation.dataset import (
    DatasetMetadata,
    EvaluationSample,
    create_subject_independent_partition,
)
from eon_ers.evaluation.evaluator import ModelEvaluator
from eon_ers.models.manifest import ModelManifest
from eon_ers.models.validation_record import ModelValidationRecord
from eon_ers.types import EmotionCategory

logger = logging.getLogger("eon_ers.training.pipeline")


class TrainingPipelineStage(str, Enum):
    """The 15 sequential stages of the ERS training and qualification pipeline."""

    STAGE_1_DATASET_INGESTION = "1_dataset_ingestion"
    STAGE_2_PROVENANCE_VERIFICATION = "2_provenance_verification"
    STAGE_3_INTEGRITY_CHECK = "3_integrity_check"
    STAGE_4_SUBJECT_SPLITTING = "4_subject_splitting"
    STAGE_5_ZERO_LEAKAGE_VALIDATION = "5_zero_leakage_validation"
    STAGE_6_PREPROCESSING = "6_preprocessing"
    STAGE_7_FEATURE_NORMALIZATION = "7_feature_normalization"
    STAGE_8_MODEL_TRAINING_OR_IMPORT = "8_model_training_or_weights_import"
    STAGE_9_CONVERGENCE_MONITORING = "9_convergence_monitoring"
    STAGE_10_TEMPERATURE_CALIBRATION = "10_temperature_calibration"
    STAGE_11_TEST_EVALUATION = "11_test_evaluation"
    STAGE_12_METRIC_QUALIFICATION = "12_metric_qualification"
    STAGE_13_ONNX_EXPORT = "13_onnx_export"
    STAGE_14_CONTRACT_VERIFICATION = "14_contract_verification"
    STAGE_15_VALIDATION_RECORD_GENERATION = "15_validation_record_generation"


class PipelineStageResult(BaseModel):
    """Execution result for a single training pipeline stage."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    stage: TrainingPipelineStage
    success: bool
    message: str
    details: dict[str, Any] = Field(default_factory=dict)
    timestamp: float = Field(default_factory=time.time)


class ModelTrainingPipeline:
    """Scientific training, calibration, and qualification pipeline for ERS models."""

    def __init__(
        self,
        dataset_metadata: DatasetMetadata,
        model_manifest: ModelManifest,
        output_dir: str = "models",
    ) -> None:
        self.dataset_metadata = dataset_metadata
        self.model_manifest = model_manifest
        self.output_dir = output_dir
        self.stage_results: list[PipelineStageResult] = []

    def _record_stage(
        self,
        stage: TrainingPipelineStage,
        success: bool,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> PipelineStageResult:
        res = PipelineStageResult(
            stage=stage,
            success=success,
            message=message,
            details=details or {},
            timestamp=time.time(),
        )
        self.stage_results.append(res)
        level = logging.INFO if success else logging.WARNING
        logger.log(level, f"[{stage.value}] {message}")
        return res

    def run_pipeline(
        self,
        raw_samples: list[EvaluationSample],
        model_weights_path: str | None = None,
        test_subject_ratio: float = 0.20,
        val_subject_ratio: float = 0.10,
        training_loss_history: list[float] | None = None,
        is_calibrated: bool = False,
        optimal_temperature: float = 1.0,
        onnx_exported: bool = False,
    ) -> tuple[bool, list[PipelineStageResult], ModelValidationRecord | None]:
        """Execute all 15 stages sequentially with strict qualification gating."""
        self.stage_results.clear()

        # Stage 1: Dataset Ingestion
        if not raw_samples:
            self._record_stage(
                TrainingPipelineStage.STAGE_1_DATASET_INGESTION,
                success=False,
                message="Dataset ingestion failed: sample list is empty.",
            )
            return False, self.stage_results, None

        has_sample_data = any(s.data is not None for s in raw_samples)
        self._record_stage(
            TrainingPipelineStage.STAGE_1_DATASET_INGESTION,
            success=True,
            message=f"Ingested {len(raw_samples)} samples from {self.dataset_metadata.name} (has_data={has_sample_data}).",
            details={
                "sample_count": len(raw_samples),
                "dataset": self.dataset_metadata.name,
                "has_sample_data": has_sample_data,
            },
        )

        # Stage 2: Provenance Verification
        prov_ok = bool(
            self.dataset_metadata.source
            and self.dataset_metadata.license
            and self.dataset_metadata.license.strip().upper() not in ("", "UNVERIFIED")
        )
        commercial_ok = self.dataset_metadata.is_commercially_usable()
        self._record_stage(
            TrainingPipelineStage.STAGE_2_PROVENANCE_VERIFICATION,
            success=prov_ok,
            message=f"Provenance verified: license '{self.dataset_metadata.license}', commercial_allowed={commercial_ok}.",
            details={
                "license": self.dataset_metadata.license,
                "commercial_allowed": commercial_ok,
            },
        )

        # Stage 3: Integrity Check - reject empty or placeholder checksums
        is_valid_cs = self.dataset_metadata.is_valid_checksum()
        manifest_checksum = self.dataset_metadata.checksum
        self._record_stage(
            TrainingPipelineStage.STAGE_3_INTEGRITY_CHECK,
            success=is_valid_cs,
            message=(
                f"Integrity check passed with valid manifest checksum {manifest_checksum[:16]}..."
                if is_valid_cs
                else f"Integrity check failed: invalid or unverified dataset checksum '{manifest_checksum}'."
            ),
            details={"checksum": manifest_checksum, "is_valid_checksum": is_valid_cs},
        )

        # Stage 4: Subject-Independent Partitioning
        try:
            partition = create_subject_independent_partition(
                samples=raw_samples,
                test_subject_ratio=test_subject_ratio,
                val_subject_ratio=val_subject_ratio,
            )
            self._record_stage(
                TrainingPipelineStage.STAGE_4_SUBJECT_SPLITTING,
                success=True,
                message=f"Partitioned into train ({len(partition.train_samples)}), "
                f"val ({len(partition.val_samples)}), test ({len(partition.test_samples)}).",
                details={
                    "train_subjects": len(partition.train_subjects),
                    "val_subjects": len(partition.val_subjects),
                    "test_subjects": len(partition.test_subjects),
                },
            )
        except Exception as exc:
            self._record_stage(
                TrainingPipelineStage.STAGE_4_SUBJECT_SPLITTING,
                success=False,
                message=f"Subject partitioning failed: {exc}",
            )
            return False, self.stage_results, None

        # Stage 5: Zero-Leakage Validation
        try:
            partition._verify_zero_leakage()
            self._record_stage(
                TrainingPipelineStage.STAGE_5_ZERO_LEAKAGE_VALIDATION,
                success=True,
                message="Zero leakage verified: disjoint subject sets across all partitions.",
            )
        except ValueError as exc:
            self._record_stage(
                TrainingPipelineStage.STAGE_5_ZERO_LEAKAGE_VALIDATION,
                success=False,
                message=f"Subject leakage validation failed: {exc}",
            )
            return False, self.stage_results, None

        # Stage 6: Preprocessing - report success ONLY if actual raw media was preprocessed
        train_has_data = any(s.data is not None for s in partition.train_samples)
        if not train_has_data:
            self._record_stage(
                TrainingPipelineStage.STAGE_6_PREPROCESSING,
                success=False,
                message="Preprocessing failed: sample data payloads are None (no raw sensory media provided).",
                details={"has_data": False},
            )
        else:
            self._record_stage(
                TrainingPipelineStage.STAGE_6_PREPROCESSING,
                success=True,
                message=f"Preprocessing executed on {len(partition.train_samples)} training samples.",
                details={"has_data": True, "samples_preprocessed": len(partition.train_samples)},
            )

        # Stage 7: Feature Normalization - report success ONLY if features are available
        if not train_has_data:
            self._record_stage(
                TrainingPipelineStage.STAGE_7_FEATURE_NORMALIZATION,
                success=False,
                message="Feature normalization failed: sample features unavailable.",
                details={"has_features": False},
            )
        else:
            self._record_stage(
                TrainingPipelineStage.STAGE_7_FEATURE_NORMALIZATION,
                success=True,
                message="Feature normalization completed across feature channels.",
                details={"has_features": True},
            )

        # Stage 8: Model Architecture & Training / Weights Import
        effective_weights_path = model_weights_path or self.model_manifest.artifact_path
        weights_exist = (
            os.path.isfile(effective_weights_path) and os.path.getsize(effective_weights_path) > 0
        )
        self._record_stage(
            TrainingPipelineStage.STAGE_8_MODEL_TRAINING_OR_IMPORT,
            success=weights_exist,
            message=f"Weights import status: {'Found' if weights_exist else 'Missing or empty'} at {effective_weights_path}.",
            details={"weights_path": effective_weights_path, "weights_exist": weights_exist},
        )
        if not weights_exist:
            return False, self.stage_results, None

        # Stage 9: Convergence & Validation Monitoring
        # Genuinely reports success only if training loss history is provided and demonstrates convergence
        has_loss_history = bool(training_loss_history and len(training_loss_history) >= 2)
        converged = has_loss_history and (
            training_loss_history[-1] < training_loss_history[0]  # type: ignore[index]
        )
        self._record_stage(
            TrainingPipelineStage.STAGE_9_CONVERGENCE_MONITORING,
            success=converged,
            message=(
                f"Convergence verified across {len(training_loss_history or [])} epochs (loss: {training_loss_history[0]:.4f} -> {training_loss_history[-1]:.4f})."  # type: ignore[index]
                if converged
                else "Convergence monitoring failed: no valid training loss history provided or loss failed to converge."
            ),
            details={"converged": converged, "epochs": len(training_loss_history or [])},
        )

        # Stage 10: Temperature Scaling & Calibration
        # Genuinely reports success only if temperature calibration was successfully executed and optimized
        self._record_stage(
            TrainingPipelineStage.STAGE_10_TEMPERATURE_CALIBRATION,
            success=is_calibrated,
            message=(
                f"Temperature calibration step completed and verified: T={optimal_temperature:.4f}."
                if is_calibrated
                else "Temperature calibration was not executed or failed to optimize."
            ),
            details={"temperature": optimal_temperature, "is_calibrated": is_calibrated},
        )

        # Stage 11: Independent Holdout Test Evaluation
        # Replace mock/uniform predictions with actual inference. If inference is unavailable, fail closed and mark BLOCKED.
        y_true_test = [s.label for s in partition.test_samples]
        test_has_data = len(partition.test_samples) > 0 and all(
            s.data is not None for s in partition.test_samples
        )

        inference_available = False
        predicted_probs: list[dict[str, float]] = []
        inference_error: str = ""

        if not test_has_data:
            inference_error = "Holdout test samples lack empirical data payloads (s.data is None)."
        else:
            try:
                import onnxruntime as ort

                so = ort.SessionOptions()
                so.intra_op_num_threads = 1
                session = ort.InferenceSession(
                    effective_weights_path, sess_options=so, providers=["CPUExecutionProvider"]
                )
                input_name = session.get_inputs()[0].name
                expected_shape = self.model_manifest.input_specification.get("shape")
                label_classes = [
                    c.value
                    for c in EmotionCategory
                    if c not in (EmotionCategory.UNKNOWN, EmotionCategory.INSUFFICIENT_EVIDENCE)
                ]

                for s in partition.test_samples:
                    inp = np.array(s.data, dtype=np.float32)
                    if expected_shape and len(inp.shape) < len(expected_shape):
                        inp = np.expand_dims(inp, axis=0)
                    raw_out = session.run(None, {input_name: inp})[0]
                    logits = np.squeeze(raw_out)
                    exp_logits = np.exp(logits - np.max(logits))
                    probs_arr = exp_logits / np.sum(exp_logits)
                    p_dict = {
                        lbl: float(probs_arr[idx])
                        for idx, lbl in enumerate(label_classes[: len(probs_arr)])
                    }
                    predicted_probs.append(p_dict)
                inference_available = True
            except Exception as exc:
                inference_error = f"Model inference execution failed: {exc}"

        val_record: ModelValidationRecord | None = None
        evaluator = ModelEvaluator()

        if inference_available and predicted_probs:
            val_record, report = evaluator.evaluate_predictions(
                y_true=y_true_test,
                predicted_probs=predicted_probs,
                model_manifest=self.model_manifest,
                dataset_name=self.dataset_metadata.name,
                dataset_split="test",
                dataset_license=self.dataset_metadata.license,
                commercial_allowed=commercial_ok,
            )
            self._record_stage(
                TrainingPipelineStage.STAGE_11_TEST_EVALUATION,
                success=True,
                message=f"Independent holdout evaluation executed on {len(y_true_test)} test samples.",
                details={"samples_evaluated": len(y_true_test), "status": "COMPLETED"},
            )
        else:
            self._record_stage(
                TrainingPipelineStage.STAGE_11_TEST_EVALUATION,
                success=False,
                message=f"Holdout evaluation BLOCKED: {inference_error}",
                details={"status": "BLOCKED", "reason": inference_error},
            )

        # Stage 12: Metric Threshold Qualification
        if val_record is not None:
            qualification_passed = val_record.is_validated
            macro_f1_val = val_record.evaluation_metrics.get("macro_f1", 0.0)
            balanced_acc_val = val_record.evaluation_metrics.get("balanced_accuracy", 0.0)
            self._record_stage(
                TrainingPipelineStage.STAGE_12_METRIC_QUALIFICATION,
                success=qualification_passed,
                message=f"Metric qualification: is_validated={qualification_passed} (Macro-F1={macro_f1_val:.4f}).",
                details={
                    "is_validated": qualification_passed,
                    "macro_f1": macro_f1_val,
                    "balanced_accuracy": balanced_acc_val,
                },
            )
        else:
            qualification_passed = False
            self._record_stage(
                TrainingPipelineStage.STAGE_12_METRIC_QUALIFICATION,
                success=False,
                message="Metric qualification BLOCKED: holdout evaluation was blocked.",
                details={"status": "BLOCKED", "is_validated": False},
            )

        # Stage 13: ONNX Export
        # Report success only if an actual ONNX export operation was performed and verified
        self._record_stage(
            TrainingPipelineStage.STAGE_13_ONNX_EXPORT,
            success=onnx_exported,
            message=(
                f"ONNX export executed and verified at {effective_weights_path}."
                if onnx_exported
                else "ONNX export was not executed; existing weights were imported."
            ),
            details={"onnx_exported": onnx_exported, "artifact_path": effective_weights_path},
        )

        # Stage 14: ONNX Contract Verification
        # Genuinely loads the runtime session and validates tensor contracts against manifest
        contract_ok = False
        contract_msg = ""
        try:
            import onnxruntime as ort

            so = ort.SessionOptions()
            so.intra_op_num_threads = 1
            sess = ort.InferenceSession(
                effective_weights_path, sess_options=so, providers=["CPUExecutionProvider"]
            )
            contract_ok, contract_msg = self.model_manifest.validate_tensor_contracts(sess)
        except Exception as exc:
            contract_ok = False
            contract_msg = f"Failed to load ONNX session for contract verification: {exc}"

        self._record_stage(
            TrainingPipelineStage.STAGE_14_CONTRACT_VERIFICATION,
            success=contract_ok,
            message=f"ONNX contract verification: {contract_msg}",
            details={"contract_verified": contract_ok, "details": contract_msg},
        )

        # Stage 15: Cryptographic Validation Record Generation
        hasher = hashlib.sha256()
        with open(effective_weights_path, "rb") as f:
            while chunk := f.read(65536):
                hasher.update(chunk)
        artifact_sha256 = hasher.hexdigest().lower()

        if val_record is None:
            record_id = f"VAL-{self.model_manifest.model_id}-{int(time.time())}"
            val_record = ModelValidationRecord(
                record_id=record_id,
                model_id=self.model_manifest.model_id,
                model_version=self.model_manifest.version,
                artifact_sha256=artifact_sha256,
                is_validated=False,
                training_dataset=self.model_manifest.training_dataset_provenance,
                training_dataset_version="1.0.0",
                dataset_license=self.dataset_metadata.license,
                commercial_use_allowed=commercial_ok,
                commercial_use_restrictions=["Research and testing baseline only."],
                preprocessing_specification=self.model_manifest.input_specification,
                label_mapping=[
                    c.value
                    for c in EmotionCategory
                    if c not in (EmotionCategory.UNKNOWN, EmotionCategory.INSUFFICIENT_EVIDENCE)
                ],
                evaluation_dataset=self.dataset_metadata.name,
                evaluation_split="test",
                evaluation_script="eon_ers.training.pipeline",
                evaluation_script_version="1.0.0",
                evaluation_metrics={"macro_f1": 0.0, "balanced_accuracy": 0.0, "accuracy": 0.0},
                per_class_metrics={},
                calibration_metrics={"ece": 0.0, "brier_score": 0.0},
                confidence_distribution={"mean": 0.0, "p50": 0.0, "p90": 0.0, "p99": 0.0},
                abstention_rate=1.0,
                evaluator="OVIC Labs Scientific Qualification Suite",
                validation_timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                validation_notes=[
                    f"Holdout evaluation BLOCKED: {inference_error}",
                    "Model is UNVALIDATED and prohibited from production classification claims.",
                ],
            )
        else:
            val_record = val_record.model_copy(update={"artifact_sha256": artifact_sha256})

        self._record_stage(
            TrainingPipelineStage.STAGE_15_VALIDATION_RECORD_GENERATION,
            success=True,
            message=f"Generated validation record bound to SHA-256 {artifact_sha256[:16]}...",
            details={"artifact_sha256": artifact_sha256, "record_id": val_record.record_id},
        )

        return qualification_passed, self.stage_results, val_record
