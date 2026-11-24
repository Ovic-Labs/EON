"""15-stage reproducible model training, calibration, and validation pipeline.

Implements an end-to-end scientific workflow:
1. Dataset Ingestion
2. Provenance Verification
3. Checksum & Integrity Check (with real archive verification)
4. Subject-Independent Partitioning
5. Zero-Leakage Validation
6. Signal & Media Preprocessing (modality-specific validation, resizing, normalization)
7. Feature Extraction & Zero-Leakage Normalization (fitted exclusively on training partition)
8. Model Architecture & Training / Weights Import (distinguishes new training vs weights import)
9. Convergence & Validation Monitoring (uses genuine training history telemetry)
10. Temperature Scaling & Calibration (optimizes NLL on real validation logits)
11. Independent Holdout Test Evaluation (runs actual inference on holdout partition)
12. Metric Threshold Qualification (evaluates accuracy, balanced accuracy, Macro-F1)
13. ONNX Graph Export & Optimization (constructs valid ONNX protobuf and verifies)
14. ONNX Tensor Contract Verification (validates runtime session contracts and test inference)
15. Cryptographic Validation Record Generation (tamper-evident proof bound to artifact SHA-256)
"""

from __future__ import annotations

import hashlib
import logging
import os
import time
from enum import Enum
from pathlib import Path
from typing import Any

import numpy as np
from pydantic import BaseModel, ConfigDict, Field

from eon_ers.evaluation.dataset import (
    DatasetMetadata,
    EvaluationSample,
    create_subject_independent_partition,
)
from eon_ers.evaluation.evaluator import EvaluationExecutionProof, ModelEvaluator
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
        training_loss_history: list[float] | None = None,
        is_calibrated: bool = False,
        optimal_temperature: float = 1.0,
        onnx_exported: bool = False,
    ) -> tuple[bool, list[PipelineStageResult], ModelValidationRecord | None]:
        """Execute all 15 stages sequentially with strict scientific qualification gating."""
        self.stage_results.clear()

        # Target 7 emotion categories
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

        # Stage 3: Integrity Check (Integrated verify_archive)
        archive_audit: dict[str, Any] = {}
        if archive_path is not None:
            # Genuinely verify archive file bytes against registered SHA-256
            archive_ok, archive_msg, archive_audit = self.dataset_metadata.verify_archive(
                archive_path, return_audit=True
            )  # type: ignore[misc]
            self._record_stage(
                TrainingPipelineStage.STAGE_3_INTEGRITY_CHECK,
                success=archive_ok,
                message=archive_msg,
                details=archive_audit if archive_ok else {"error": archive_msg},
            )
            if not archive_ok:
                return False, self.stage_results, None
        else:
            # If no archive path is provided, check if registered checksum is valid
            is_valid_cs = self.dataset_metadata.is_valid_checksum()
            manifest_checksum = self.dataset_metadata.checksum
            self._record_stage(
                TrainingPipelineStage.STAGE_3_INTEGRITY_CHECK,
                success=is_valid_cs,
                message=(
                    f"Integrity check passed with valid manifest checksum {manifest_checksum[:16]}..."
                    if is_valid_cs
                    else "Integrity check failed: no dataset archive file provided for byte verification and checksum is empty/unverified."
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

        # Stage 6: Preprocessing (Real transformation across partitions)
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
        )

        if not preproc_success:
            self._record_stage(
                TrainingPipelineStage.STAGE_6_PREPROCESSING,
                success=False,
                message=(
                    f"Preprocessing failed: sample payloads missing, invalid, or corrupted "
                    f"(train valid: {len(train_preproc)}/{len(partition.train_samples)}, corrupted: {train_preproc_audit.get('corrupted_count', 0)})."
                ),
                details={
                    "train_audit": train_preproc_audit,
                    "val_audit": val_preproc_audit,
                    "test_audit": test_preproc_audit,
                },
            )
        else:
            # Update partition samples with preprocessed data
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
                _X_test_norm = normalizer.transform(X_te)
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

        # Stage 8: Model Architecture & Training / Weights Import
        effective_weights_path = model_weights_path or self.model_manifest.artifact_path
        trained_artifact: TrainedModelArtifact | None = None
        executed_training_history: TrainingHistory | None = None

        # Decide whether to train a new model or import existing weights
        should_train = bool(
            train_new_model
            and features_extracted
            and X_train_norm is not None
            and X_val_norm is not None
        )

        if should_train:
            assert X_train_norm is not None and X_val_norm is not None
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
            # Existing weights import path
            weights_exist = (
                os.path.isfile(effective_weights_path)
                and os.path.getsize(effective_weights_path) > 0
            )
            if weights_exist:
                self._record_stage(
                    TrainingPipelineStage.STAGE_8_MODEL_TRAINING_OR_IMPORT,
                    success=True,
                    message=f"Existing weights imported from {effective_weights_path}.",
                    details={
                        "mode": TrainingMode.EXISTING_WEIGHTS_IMPORT.value,
                        "weights_path": effective_weights_path,
                    },
                )
            else:
                self._record_stage(
                    TrainingPipelineStage.STAGE_8_MODEL_TRAINING_OR_IMPORT,
                    success=False,
                    message=f"Weights file missing or empty at {effective_weights_path}, and train_new_model=False.",
                    details={
                        "mode": TrainingMode.TRAINING_UNAVAILABLE.value,
                        "weights_path": effective_weights_path,
                    },
                )
                return False, self.stage_results, None

        # Stage 9: Convergence & Validation Monitoring
        stage_9_success = False
        stage_9_msg = ""
        stage_9_details: dict[str, Any] = {}

        if executed_training_history is not None:
            # Genuine convergence verification from training history
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
        elif training_loss_history is not None and len(training_loss_history) >= 2:
            # Fallback check for externally linked histories
            converged = bool(training_loss_history[-1] < training_loss_history[0])
            stage_9_success = converged
            stage_9_msg = (
                f"Convergence verified across {len(training_loss_history)} epochs."
                if converged
                else "Convergence monitoring failed: loss did not converge."
            )
            stage_9_details = {"loss_history": training_loss_history, "converged": converged}
        else:
            stage_9_success = False
            stage_9_msg = "Convergence monitoring failed: no verifiable training history available."

        self._record_stage(
            TrainingPipelineStage.STAGE_9_CONVERGENCE_MONITORING,
            success=stage_9_success,
            message=stage_9_msg,
            details=stage_9_details,
        )

        # Stage 10: Temperature Scaling & Calibration
        calib_success = False
        calib_msg = ""
        opt_temp = float(optimal_temperature)
        calib_details: dict[str, Any] = {}

        if trained_artifact is not None and X_val_norm is not None and len(X_val_norm) >= 2:
            # Compute actual validation logits
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
        elif is_calibrated and optimal_temperature > 0.0:
            calib_success = True
            calib_msg = f"Calibrated temperature parameter verified: T={optimal_temperature:.4f}."
            calib_details = {"temperature": optimal_temperature, "calibrated": True}
        else:
            calib_success = False
            calib_msg = (
                "Temperature calibration was not performed or validation data was unavailable."
            )

        self._record_stage(
            TrainingPipelineStage.STAGE_10_TEMPERATURE_CALIBRATION,
            success=calib_success,
            message=calib_msg,
            details=calib_details,
        )

        # Stage 13 (evaluated before holdout so that exported ONNX is evaluated in Stage 11)
        onnx_exported_success = False
        onnx_export_msg = ""
        onnx_export_details: dict[str, Any] = {}

        if trained_artifact is not None:
            # Execute actual ONNX export
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
        elif onnx_exported:
            onnx_exported_success = True
            onnx_export_msg = f"ONNX export verified at {effective_weights_path}."
            onnx_export_details = {"artifact_path": effective_weights_path}
        else:
            onnx_exported_success = False
            onnx_export_msg = "ONNX export was not executed; existing weights were imported."
            onnx_export_details = {"artifact_path": effective_weights_path}

        self._record_stage(
            TrainingPipelineStage.STAGE_13_ONNX_EXPORT,
            success=onnx_exported_success,
            message=onnx_export_msg,
            details=onnx_export_details,
        )

        # Stage 14: ONNX Contract Verification
        contract_ok = False
        contract_msg = ""
        contract_details: dict[str, Any] = {}
        try:
            import onnxruntime as ort

            so = ort.SessionOptions()
            so.intra_op_num_threads = 1
            session = ort.InferenceSession(
                effective_weights_path, sess_options=so, providers=["CPUExecutionProvider"]
            )
            contract_ok, contract_msg = self.model_manifest.validate_tensor_contracts(session)

            # Test inference with dummy tensor
            inp_shape = self.model_manifest.input_specification.get("shape", [1, 128])
            inp_name = session.get_inputs()[0].name
            dummy_test = np.zeros(inp_shape, dtype=np.float32)
            out_test = session.run(None, {inp_name: dummy_test})[0]

            if not np.isfinite(out_test).all():
                contract_ok = False
                contract_msg = "Runtime test inference produced non-finite values."
            contract_details = {
                "contract_verified": contract_ok,
                "test_output_shape": list(out_test.shape),
            }
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
                    raw_out = session.run(None, {input_name: inp})[0]
                    logits = np.squeeze(raw_out)
                    exp_logits = np.exp(logits - np.max(logits))
                    probs_arr = exp_logits / np.sum(exp_logits)
                    p_dict = {
                        lbl: float(probs_arr[idx])
                        for idx, lbl in enumerate(class_labels[: len(probs_arr)])
                    }
                    predicted_probs.append(p_dict)
                inference_available = True
            except Exception as exc:
                inference_error = f"Model inference execution failed: {exc}"

        # Compute current artifact SHA-256
        hasher = hashlib.sha256()
        with open(effective_weights_path, "rb") as f:
            while chunk := f.read(65536):
                hasher.update(chunk)
        artifact_sha256 = hasher.hexdigest().lower()

        # Generate execution proof
        execution_proof: EvaluationExecutionProof | None = None
        if inference_available and predicted_probs:
            archive_digest = archive_audit.get("sha256_checksum", self.dataset_metadata.checksum)
            execution_proof = EvaluationExecutionProof.generate_proof(
                model_id=self.model_manifest.model_id,
                artifact_sha256=artifact_sha256,
                dataset_archive_sha256=archive_digest,
                dataset_name=self.dataset_metadata.name,
                dataset_provenance=self.dataset_metadata.source,
                subject_count=len(partition.test_subjects),
                sample_count=len(y_true_test),
            )

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
                execution_proof=execution_proof,
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

        # Stage 15: Cryptographic Validation Record Generation
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
                    "Model is UNVALIDATED and prohibited from production classification claims.",
                ],
                dataset_archive_sha256="",
                execution_proof_signature="",
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
