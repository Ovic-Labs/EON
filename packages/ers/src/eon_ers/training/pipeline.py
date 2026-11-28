"""15-stage reproducible model training, calibration, and validation pipeline.

Implements an end-to-end scientific workflow:
1. Dataset Ingestion
2. Provenance Verification
3. Checksum & Integrity Check (requires actual archive bytes and recomputes SHA-256)
4. Subject-Independent Partitioning
5. Zero-Leakage Validation
6. Signal & Media Preprocessing (modality-specific validation, resizing, normalization)
7. Feature Extraction & Zero-Leakage Normalization (fitted exclusively on training partition)
8. Model Architecture & Training / Weights Import (trains CPU MLP or validates & loads real ONNX weights)
9. Convergence & Validation Monitoring (uses genuine training history telemetry only)
10. Temperature Scaling & Calibration (optimizes NLL on real validation logits only)
11. Independent Holdout Test Evaluation (runs actual inference on holdout partition)
12. Metric Threshold Qualification (requires all prior stages passed + metrics + Ed25519 proof)
13. ONNX Graph Export & Parity Verification (no silent padding/truncation; numerical parity check)
14. ONNX Tensor Contract Verification (validates runtime session weights, contracts, and test inference)
15. Cryptographic Validation Record Generation (Ed25519 proof bound to artifact & archive SHA-256)
"""

from __future__ import annotations

import hashlib
import logging
import os
import time
import warnings
from enum import Enum
from pathlib import Path
from typing import Any

import numpy as np
from pydantic import BaseModel, ConfigDict, Field

from eon_ers.evaluation.dataset import (
    DatasetMetadata,
    EvaluationSample,
    create_subject_independent_partition,
    is_valid_sha256_digest,
)
from eon_ers.evaluation.evaluator import (
    EvaluationExecutionProof,
    ModelEvaluator,
    SigningKeyPair,
    TrustedKeyRegistry,
)
from eon_ers.models.loader import ModelLoader
from eon_ers.models.manifest import ModelManifest
from eon_ers.models.validation_record import ModelValidationRecord
from eon_ers.training.calibration import TemperatureCalibrator
from eon_ers.training.export import ONNXModelExporter
from eon_ers.training.features import FeatureExtractor, ZeroLeakageNormalizer
from eon_ers.training.preprocessing import PreprocessingConfig, SamplePreprocessor
from eon_ers.training.trainer import (
    CPUModelTrainer,
    TrainedModelArtifact,
    TrainingConfig,
    TrainingHistory,
    TrainingMode,
)
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

    @staticmethod
    def _reject_legacy_bypass_flags(
        *,
        training_loss_history: list[float] | None,
        is_calibrated: bool,
        optimal_temperature: float | None,
        onnx_exported: bool,
    ) -> None:
        """Deprecate and prohibit legacy boolean/history flags from claiming execution success."""
        if (
            training_loss_history is not None
            or is_calibrated
            or optimal_temperature is not None
            or onnx_exported
        ):
            warnings.warn(
                "Legacy bypass arguments (training_loss_history, is_calibrated, "
                "optimal_temperature, onnx_exported) are deprecated and rejected.",
                DeprecationWarning,
                stacklevel=3,
            )
            raise ValueError(
                "Legacy bypass arguments (training_loss_history, is_calibrated, "
                "optimal_temperature, onnx_exported) cannot be used to claim training, "
                "calibration, or ONNX export success without genuine execution."
            )

    def run_pipeline(
        self,
        raw_samples: list[EvaluationSample],
        model_weights_path: str | None = None,
        test_subject_ratio: float = 0.20,
        val_subject_ratio: float = 0.10,
        archive_path: str | Path | None = None,
        manifest_path: str | Path | None = None,
        train_new_model: bool = False,
        training_config: TrainingConfig | None = None,
        preprocessing_config: PreprocessingConfig | None = None,
        signing_key: SigningKeyPair | None = None,
        key_registry: TrustedKeyRegistry | None = None,
        # Deprecated legacy parameters kept only as fail-closed compatibility guards:
        training_loss_history: list[float] | None = None,
        is_calibrated: bool = False,
        optimal_temperature: float | None = None,
        onnx_exported: bool = False,
    ) -> tuple[bool, list[PipelineStageResult], ModelValidationRecord | None]:
        """Execute all 15 stages sequentially with strict security and qualification gating."""
        self.stage_results.clear()

        self._reject_legacy_bypass_flags(
            training_loss_history=training_loss_history,
            is_calibrated=is_calibrated,
            optimal_temperature=optimal_temperature,
            onnx_exported=onnx_exported,
        )

        class_labels = [
            EmotionCategory.NEUTRAL.value,
            EmotionCategory.HAPPINESS.value,
            EmotionCategory.SADNESS.value,
            EmotionCategory.ANGER.value,
            EmotionCategory.FEAR.value,
            EmotionCategory.SURPRISE.value,
            EmotionCategory.DISGUST.value,
        ]

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
            self.dataset_metadata.source.strip()
            and self.dataset_metadata.license.strip()
            and self.dataset_metadata.license.strip().upper() not in ("", "UNVERIFIED")
        )
        commercial_ok = self.dataset_metadata.is_commercially_usable()
        self._record_stage(
            TrainingPipelineStage.STAGE_2_PROVENANCE_VERIFICATION,
            success=prov_ok,
            message=f"Provenance {'verified' if prov_ok else 'unverified'}: license '{self.dataset_metadata.license}', commercial_allowed={commercial_ok}.",
            details={
                "license": self.dataset_metadata.license,
                "commercial_allowed": commercial_ok,
            },
        )

        # Stage 3: Dataset Integrity Verification (ALWAYS requires physical archive bytes)
        archive_audit: dict[str, Any] = {}
        archive_verified = False
        if archive_path is not None:
            archive_ok, archive_msg, archive_audit = self.dataset_metadata.verify_archive(
                archive_path, return_audit=True
            )  # type: ignore[misc]
            manifest_ok = True
            manifest_msg = ""
            if archive_ok and (
                manifest_path is not None or self.dataset_metadata.manifest_checksum
            ):
                manifest_ok, manifest_msg, manifest_audit = self.dataset_metadata.verify_manifest(
                    manifest_path, samples=raw_samples
                )
                if manifest_ok:
                    archive_audit["manifest_audit"] = manifest_audit

            stage3_ok = bool(archive_ok and manifest_ok)
            stage3_msg = (
                archive_msg
                if not archive_ok
                else (manifest_msg if not manifest_ok else archive_msg)
            )
            archive_verified = stage3_ok
            self._record_stage(
                TrainingPipelineStage.STAGE_3_INTEGRITY_CHECK,
                success=stage3_ok,
                message=stage3_msg,
                details=archive_audit if stage3_ok else {"error": stage3_msg},
            )
            if not stage3_ok:
                return False, self.stage_results, None
        else:
            # Syntactic checksum validation is NEVER proof of dataset archive integrity.
            self._record_stage(
                TrainingPipelineStage.STAGE_3_INTEGRITY_CHECK,
                success=False,
                message=(
                    "Integrity check failed: physical dataset archive file is required for "
                    "byte-level SHA-256 verification; checksum syntax alone is insufficient."
                ),
                details={
                    "archive_provided": False,
                    "checksum_format_valid": self.dataset_metadata.is_valid_checksum(),
                },
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

        # Stage 6: Preprocessing
        preproc = SamplePreprocessor(preprocessing_config)
        modality = self.model_manifest.modality

        train_preproc, train_preproc_audit = preproc.preprocess_partition(
            partition.train_samples, modality
        )
        val_preproc, val_preproc_audit = preproc.preprocess_partition(
            partition.val_samples, modality
        )
        test_preproc, test_preproc_audit = preproc.preprocess_partition(
            partition.test_samples, modality
        )

        preproc_success = (
            len(train_preproc) > 0
            and len(val_preproc) > 0
            and len(test_preproc) > 0
            and train_preproc_audit.get("corrupted_count", 0) == 0
            and val_preproc_audit.get("corrupted_count", 0) == 0
            and test_preproc_audit.get("corrupted_count", 0) == 0
        )

        if not preproc_success:
            self._record_stage(
                TrainingPipelineStage.STAGE_6_PREPROCESSING,
                success=False,
                message=(
                    f"Preprocessing failed: sample payloads missing, invalid, or corrupted "
                    f"(train valid: {len(train_preproc)}/{len(partition.train_samples)}, "
                    f"corrupted: {train_preproc_audit.get('corrupted_count', 0)})."
                ),
                details={
                    "train_audit": train_preproc_audit,
                    "val_audit": val_preproc_audit,
                    "test_audit": test_preproc_audit,
                },
            )
        else:
            partition = type(partition)(
                train_samples=train_preproc,
                val_samples=val_preproc,
                test_samples=test_preproc,
            )
            self._record_stage(
                TrainingPipelineStage.STAGE_6_PREPROCESSING,
                success=True,
                message=f"Preprocessing executed on all {partition.total_samples} samples across train/val/test.",
                details={
                    "preprocessed_train": len(train_preproc),
                    "preprocessed_val": len(val_preproc),
                    "preprocessed_test": len(test_preproc),
                    "config": preproc.config.model_dump(),
                },
            )

        # Stage 7: Feature Extraction & Zero-Leakage Normalization
        extractor = FeatureExtractor()
        normalizer = ZeroLeakageNormalizer()
        features_extracted = False
        X_train_norm: np.ndarray | None = None
        X_val_norm: np.ndarray | None = None
        y_train_labels: list[str] = []
        y_val_labels: list[str] = []
        y_test_labels: list[str] = []

        if preproc_success:
            try:
                X_tr, y_train_labels, _ = extractor.extract_partition_matrix(
                    partition.train_samples, modality
                )
                X_va, y_val_labels, _ = extractor.extract_partition_matrix(
                    partition.val_samples, modality
                )
                X_te, y_test_labels, _ = extractor.extract_partition_matrix(
                    partition.test_samples, modality
                )

                # Fit normalizer EXCLUSIVELY on training features
                normalizer.fit(X_tr, modality=modality)

                # Transform all partitions consistently
                X_train_norm = normalizer.transform(X_tr)
                X_val_norm = normalizer.transform(X_va)
                _ = normalizer.transform(X_te)
                features_extracted = True

                self._record_stage(
                    TrainingPipelineStage.STAGE_7_FEATURE_NORMALIZATION,
                    success=True,
                    message=f"Feature extraction & zero-leakage normalization completed (feature dim: {X_tr.shape[1]}).",
                    details={
                        "feature_dim": X_tr.shape[1],
                        "train_samples": len(X_tr),
                        "val_samples": len(X_va),
                        "test_samples": len(X_te),
                        "zero_leakage_verified": True,
                    },
                )
            except Exception as exc:
                self._record_stage(
                    TrainingPipelineStage.STAGE_7_FEATURE_NORMALIZATION,
                    success=False,
                    message=f"Feature extraction failed: {exc}",
                )
        else:
            self._record_stage(
                TrainingPipelineStage.STAGE_7_FEATURE_NORMALIZATION,
                success=False,
                message="Feature normalization failed: preprocessing was unsuccessful or sample data is missing.",
            )

        # Stage 8: Model Architecture & Training / Real Weights Import
        effective_weights_path = model_weights_path or self.model_manifest.artifact_path
        trained_artifact: TrainedModelArtifact | None = None
        executed_training_history: TrainingHistory | None = None
        imported_weights_verified = False

        if train_new_model:
            if features_extracted and X_train_norm is not None and X_val_norm is not None:
                trainer_cfg = training_config or TrainingConfig(
                    input_dim=X_train_norm.shape[1], num_classes=len(class_labels)
                )
                trainer = CPUModelTrainer(trainer_cfg)

                train_ok, trained_artifact, executed_training_history, train_msg = trainer.train(
                    X_train=X_train_norm,
                    y_train=y_train_labels,
                    X_val=X_val_norm,
                    y_val=y_val_labels,
                    class_labels=class_labels,
                )

                if train_ok and trained_artifact and executed_training_history:
                    self._record_stage(
                        TrainingPipelineStage.STAGE_8_MODEL_TRAINING_OR_IMPORT,
                        success=True,
                        message=f"Genuine CPU model training completed: {train_msg}",
                        details={
                            "mode": TrainingMode.ACTUAL_MODEL_TRAINING.value,
                            "epochs_trained": len(executed_training_history.epochs),
                            "best_epoch": executed_training_history.best_epoch,
                            "best_val_loss": executed_training_history.best_val_loss,
                            "signature": executed_training_history.training_signature,
                        },
                    )
                else:
                    self._record_stage(
                        TrainingPipelineStage.STAGE_8_MODEL_TRAINING_OR_IMPORT,
                        success=False,
                        message=f"Model training failed: {train_msg}",
                        details={"mode": TrainingMode.TRAINING_FAILED.value, "error": train_msg},
                    )
                    return False, self.stage_results, None
            else:
                self._record_stage(
                    TrainingPipelineStage.STAGE_8_MODEL_TRAINING_OR_IMPORT,
                    success=False,
                    message="Model training unavailable: preprocessing or feature extraction did not succeed.",
                    details={"mode": TrainingMode.TRAINING_UNAVAILABLE.value},
                )
                return False, self.stage_results, None
        else:
            # Real existing weights import: load ONNX, check weights, verify contracts & smoke test.
            # Never treat mere file existence as valid weights import.
            try:
                _, weight_audit = ModelLoader.validate_and_load_onnx_weights(
                    artifact_path=effective_weights_path,
                    manifest=self.model_manifest,
                    num_threads=1,
                    expected_classes=class_labels,
                    verify_manifest_checksum=True,
                )
                imported_weights_verified = True
                self._record_stage(
                    TrainingPipelineStage.STAGE_8_MODEL_TRAINING_OR_IMPORT,
                    success=True,
                    message=f"Existing ONNX weights loaded and verified from {effective_weights_path}.",
                    details={
                        "mode": TrainingMode.EXISTING_WEIGHTS_IMPORT.value,
                        **weight_audit,
                    },
                )
            except Exception as exc:
                self._record_stage(
                    TrainingPipelineStage.STAGE_8_MODEL_TRAINING_OR_IMPORT,
                    success=False,
                    message=f"Weights import failed verification for '{effective_weights_path}': {exc}",
                    details={
                        "mode": TrainingMode.EXISTING_WEIGHTS_IMPORT.value,
                        "weights_path": effective_weights_path,
                        "error": str(exc),
                    },
                )

        # Stage 9: Convergence & Validation Monitoring (genuine training telemetry only)
        stage_9_success = False
        stage_9_msg = ""
        stage_9_details: dict[str, Any] = {}

        if executed_training_history is not None:
            hist = executed_training_history
            if not hist.converged:
                stage_9_success = False
                stage_9_msg = (
                    f"Training did not converge (best val loss: {hist.best_val_loss:.4f})."
                )
            elif hist.overfitting_detected:
                stage_9_success = False
                stage_9_msg = "Severe overfitting detected: validation loss diverged while training loss fell."
            elif len(hist.epochs) < 2:
                stage_9_success = False
                stage_9_msg = f"Insufficient epochs trained ({len(hist.epochs)} < 2)."
            else:
                stage_9_success = True
                stage_9_msg = (
                    f"Convergence verified across {len(hist.epochs)} epochs "
                    f"(train loss: {hist.train_loss[0]:.4f} -> {hist.train_loss[-1]:.4f}, "
                    f"val loss: {hist.val_loss[0]:.4f} -> {hist.best_val_loss:.4f})."
                )
            stage_9_details = hist.model_dump()
        else:
            stage_9_success = False
            stage_9_msg = (
                "Convergence monitoring failed: no genuine training execution history available."
            )

        self._record_stage(
            TrainingPipelineStage.STAGE_9_CONVERGENCE_MONITORING,
            success=stage_9_success,
            message=stage_9_msg,
            details=stage_9_details,
        )

        # Stage 10: Temperature Scaling & Calibration (genuine validation optimization only)
        calib_success = False
        calib_msg = ""
        opt_temp = 1.0
        calib_details: dict[str, Any] = {}

        if trained_artifact is not None and X_val_norm is not None and len(X_val_norm) >= 2:
            val_logits = trained_artifact.predict_logits(X_val_norm)
            calibrator = TemperatureCalibrator()
            c_ok, c_res, c_msg = calibrator.calibrate(val_logits, y_val_labels, class_labels)

            if c_ok and c_res is not None:
                calib_success = True
                opt_temp = c_res.optimal_temperature
                calib_msg = c_msg
                calib_details = c_res.model_dump()
            else:
                calib_success = False
                calib_msg = f"Temperature calibration failed: {c_msg}"
        else:
            calib_success = False
            calib_msg = "Temperature calibration was not executed: trained model or validation data unavailable."

        self._record_stage(
            TrainingPipelineStage.STAGE_10_TEMPERATURE_CALIBRATION,
            success=calib_success,
            message=calib_msg,
            details=calib_details,
        )

        # Stage 13: ONNX Export & Numerical Parity Verification (before Stage 11 holdout inference)
        onnx_exported_success = False
        onnx_export_msg = ""
        onnx_export_details: dict[str, Any] = {}

        if trained_artifact is not None:
            exporter = ONNXModelExporter()
            exp_ok, exp_meta, exp_msg = exporter.export(
                artifact=trained_artifact,
                manifest=self.model_manifest,
                output_path=effective_weights_path,
                temperature=opt_temp,
            )
            onnx_exported_success = exp_ok
            onnx_export_msg = exp_msg
            if exp_meta:
                onnx_export_details = exp_meta.model_dump()
        else:
            onnx_exported_success = False
            onnx_export_msg = (
                "ONNX export was not executed; no newly trained model artifact produced."
            )
            onnx_export_details = {"artifact_path": effective_weights_path}

        self._record_stage(
            TrainingPipelineStage.STAGE_13_ONNX_EXPORT,
            success=onnx_exported_success,
            message=onnx_export_msg,
            details=onnx_export_details,
        )

        # Stage 14: ONNX Contract & Weights Verification
        contract_ok = False
        contract_msg = ""
        contract_details: dict[str, Any] = {}
        try:
            verify_checksum_in_stage14 = not train_new_model or is_valid_sha256_digest(
                self.model_manifest.sha256_checksum
            )
            _, contract_details = ModelLoader.validate_and_load_onnx_weights(
                artifact_path=effective_weights_path,
                manifest=self.model_manifest,
                num_threads=1,
                expected_classes=class_labels,
                verify_manifest_checksum=verify_checksum_in_stage14,
            )
            contract_ok = True
            contract_msg = "ONNX weights, tensor contracts, and smoke inference verified."
        except Exception as exc:
            contract_ok = False
            contract_msg = f"Contract verification failed: {exc}"
            contract_details = {"error": str(exc)}

        self._record_stage(
            TrainingPipelineStage.STAGE_14_CONTRACT_VERIFICATION,
            success=contract_ok,
            message=f"ONNX contract verification: {contract_msg}",
            details=contract_details,
        )

        # Stage 11: Independent Holdout Test Evaluation
        y_true_test = [s.label for s in partition.test_samples]
        test_has_data = len(partition.test_samples) > 0 and all(
            s.data is not None for s in partition.test_samples
        )

        inference_available = False
        predicted_probs: list[dict[str, float]] = []
        inference_error = ""

        can_run_inference = (
            test_has_data and (onnx_exported_success or imported_weights_verified) and contract_ok
        )

        if not test_has_data:
            inference_error = "Holdout test samples lack empirical data payloads (s.data is None)."
        elif not can_run_inference:
            inference_error = "Holdout inference blocked: ONNX weights failed export, import, or contract verification."
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

                for s in partition.test_samples:
                    sample_payload = s.data
                    if (
                        expected_shape
                        and len(expected_shape) == 2
                        and expected_shape[1] == 128
                        and isinstance(sample_payload, np.ndarray)
                        and sample_payload.ndim >= 2
                    ):
                        raw_feat = extractor.extract_sample_features(s, modality)
                        if normalizer.is_fitted:
                            sample_payload = normalizer.transform(np.expand_dims(raw_feat, axis=0))[
                                0
                            ]
                        else:
                            sample_payload = raw_feat

                    inp = np.array(sample_payload, dtype=np.float32)
                    if expected_shape and len(inp.shape) < len(expected_shape):
                        while len(inp.shape) < len(expected_shape):
                            inp = np.expand_dims(inp, axis=0)
                    if expected_shape and list(inp.shape) != list(expected_shape):
                        raise ValueError(
                            f"Holdout sample tensor shape {list(inp.shape)} != expected {expected_shape}."
                        )

                    raw_out = session.run(None, {input_name: inp})[0]
                    logits = np.squeeze(raw_out)
                    if logits.ndim != 1 or len(logits) != len(class_labels):
                        raise ValueError(
                            f"Model logit shape {logits.shape} incompatible with {len(class_labels)} classes."
                        )
                    exp_logits = np.exp(logits - np.max(logits))
                    probs_arr = exp_logits / np.sum(exp_logits)
                    p_dict = {lbl: float(probs_arr[idx]) for idx, lbl in enumerate(class_labels)}
                    predicted_probs.append(p_dict)
                inference_available = True
            except Exception as exc:
                inference_error = f"Model inference execution failed: {exc}"

        # Compute current artifact SHA-256 safely if file exists
        artifact_sha256 = "0" * 64
        if os.path.isfile(effective_weights_path):
            hasher = hashlib.sha256()
            with open(effective_weights_path, "rb") as f:
                while chunk := f.read(65536):
                    hasher.update(chunk)
            artifact_sha256 = hasher.hexdigest().lower()

        # Check all upstream stages before Stage 11
        prior_stages_before_11_ok = all(r.success for r in self.stage_results)

        # Generate authenticated Ed25519 execution proof ONLY if archive verified AND signing key provided
        active_signing_key = signing_key or SigningKeyPair.from_env()
        execution_proof: EvaluationExecutionProof | None = None
        archive_digest = archive_audit.get("sha256_checksum", "")

        if (
            inference_available
            and predicted_probs
            and archive_verified
            and is_valid_sha256_digest(archive_digest)
            and is_valid_sha256_digest(artifact_sha256)
            and active_signing_key is not None
        ):
            execution_proof = EvaluationExecutionProof.generate_proof(
                model_id=self.model_manifest.model_id,
                artifact_sha256=artifact_sha256,
                dataset_archive_sha256=archive_digest,
                dataset_name=self.dataset_metadata.name,
                dataset_provenance=self.dataset_metadata.source,
                subject_count=len(partition.test_subjects),
                sample_count=len(y_true_test),
                signing_key=active_signing_key,
            )

        val_record: ModelValidationRecord | None = None
        evaluator = ModelEvaluator()

        if inference_available and predicted_probs:
            self._record_stage(
                TrainingPipelineStage.STAGE_11_TEST_EVALUATION,
                success=True,
                message=f"Independent holdout evaluation executed on {len(y_true_test)} test samples.",
                details={"samples_evaluated": len(y_true_test), "status": "COMPLETED"},
            )
            all_stages_ok = prior_stages_before_11_ok and True
            val_record, _ = evaluator.evaluate_predictions(
                y_true=y_true_test,
                predicted_probs=predicted_probs,
                model_manifest=self.model_manifest,
                dataset_name=self.dataset_metadata.name,
                dataset_split="test",
                dataset_license=self.dataset_metadata.license,
                commercial_allowed=commercial_ok,
                execution_proof=execution_proof,
                key_registry=key_registry,
                expected_dataset_archive_sha256=archive_digest if archive_verified else None,
                pipeline_stages_ok=all_stages_ok,
            )
        else:
            self._record_stage(
                TrainingPipelineStage.STAGE_11_TEST_EVALUATION,
                success=False,
                message=f"Holdout evaluation BLOCKED: {inference_error}",
                details={"status": "BLOCKED", "reason": inference_error},
            )

        # Stage 12: Metric Threshold & Full-Pipeline Qualification
        all_prior_ok = all(r.success for r in self.stage_results)
        if val_record is not None:
            qualification_passed = bool(val_record.is_validated and all_prior_ok)
            macro_f1_val = val_record.evaluation_metrics.get("macro_f1", 0.0)
            balanced_acc_val = val_record.evaluation_metrics.get("balanced_accuracy", 0.0)
            self._record_stage(
                TrainingPipelineStage.STAGE_12_METRIC_QUALIFICATION,
                success=qualification_passed,
                message=f"Metric qualification: is_validated={qualification_passed} (Macro-F1={macro_f1_val:.4f}, all_prior_stages_ok={all_prior_ok}).",
                details={
                    "is_validated": qualification_passed,
                    "all_prior_stages_ok": all_prior_ok,
                    "macro_f1": macro_f1_val,
                    "balanced_accuracy": balanced_acc_val,
                },
            )
        else:
            qualification_passed = False
            self._record_stage(
                TrainingPipelineStage.STAGE_12_METRIC_QUALIFICATION,
                success=False,
                message="Metric qualification BLOCKED: holdout evaluation or upstream stages failed.",
                details={
                    "status": "BLOCKED",
                    "is_validated": False,
                    "all_prior_stages_ok": all_prior_ok,
                },
            )

        # Stage 15: Validation Record Generation (always preserves is_validated=False if any stage failed)
        if val_record is None:
            record_id = f"VAL-{self.model_manifest.model_id}-{int(time.time())}"
            failed_stage_names = [r.stage.value for r in self.stage_results if not r.success]
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
                label_mapping=class_labels,
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
                    f"Failed pipeline stages: {failed_stage_names}",
                    "Model is UNVALIDATED and prohibited from production classification claims.",
                ],
                dataset_archive_sha256="",
                execution_proof_key_id="",
                execution_proof_algorithm="",
                execution_proof_signature="",
            )
        else:
            val_record = val_record.model_copy(
                update={
                    "artifact_sha256": artifact_sha256,
                    "is_validated": bool(val_record.is_validated and all_prior_ok),
                }
            )

        self._record_stage(
            TrainingPipelineStage.STAGE_15_VALIDATION_RECORD_GENERATION,
            success=True,
            message=f"Generated validation record bound to SHA-256 {artifact_sha256[:16]}... (is_validated={val_record.is_validated}).",
            details={
                "artifact_sha256": artifact_sha256,
                "record_id": val_record.record_id,
                "is_validated": val_record.is_validated,
            },
        )

        return qualification_passed, self.stage_results, val_record
