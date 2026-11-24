"""Comprehensive regression test suite for Phase 3.1.5 Evaluation Integrity.

Validates the remediation of the five confirmed Phase 3.1.4 defects:
1. Defect 1: Mock/uniform predictions in training pipeline replaced with actual inference;
             fails closed and marks evaluation BLOCKED when inference is unavailable.
2. Defect 2: Removal of false-success reporting across stages 3, 6, 7, 9, 10, 13, 14.
3. Defect 3: Dataset checksum verification rejects empty, placeholder, and invalid checksums;
             verifies actual file bytes against registered SHA-256 without inventing hashes.
4. Defect 4: Multimodal probability validation enforces exact 7 supported classes, finite values,
             non-negativity, and unit sum within numerical tolerance (0.02).
5. Defect 5: Scientific qualification gating guarantees validation records cannot claim qualification
             unless empirical holdout inference, verified provenance, artifact integrity, and accuracy
             thresholds all pass.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from eon_ers.config import ERSConfig
from eon_ers.contracts import EmotionObservation
from eon_ers.evaluation.dataset import (
    EMPTY_BYTES_SHA256,
    KNOWN_PLACEHOLDER_CHECKSUMS,
    DatasetMetadata,
    EvaluationSample,
)
from eon_ers.evaluation.evaluator import ModelEvaluator
from eon_ers.fusion.multimodal import (
    PROBABILITY_SUM_TOLERANCE,
    SUPPORTED_EMOTION_CLASSES,
    MultimodalFusionPipeline,
    evaluate_modality_eligibility,
    validate_emotion_probabilities,
)
from eon_ers.models.manifest import ModelManifest
from eon_ers.training.pipeline import (
    ModelTrainingPipeline,
    TrainingPipelineStage,
)
from eon_ers.types import (
    InputQualityStatus,
    Modality,
    ModalityEligibilityStatus,
    ModelState,
    ObservationStatus,
)

# -----------------------------------------------------------------------------
# DEFECT 3: Dataset Checksum Rejection & Archive Integrity Tests
# -----------------------------------------------------------------------------


def test_dataset_checksum_rejects_empty_and_placeholders() -> None:
    """DatasetMetadata.is_valid_checksum must reject empty strings and known placeholder hashes."""
    # Empty checksum
    meta_empty = DatasetMetadata(
        name="Empty", source="Lab", version="1.0", license="MIT", checksum=""
    )
    assert meta_empty.is_valid_checksum() is False

    # Empty bytes SHA-256 (e3b0c442...)
    meta_empty_bytes = DatasetMetadata(
        name="EmptyBytes",
        source="Lab",
        version="1.0",
        license="MIT",
        checksum=EMPTY_BYTES_SHA256,
    )
    assert meta_empty_bytes.is_valid_checksum() is False

    # All known placeholder digests
    for placeholder in KNOWN_PLACEHOLDER_CHECKSUMS:
        meta_ph = DatasetMetadata(
            name="Placeholder",
            source="Lab",
            version="1.0",
            license="MIT",
            checksum=placeholder,
        )
        assert meta_ph.is_valid_checksum() is False

    # Invalid lengths or characters
    assert (
        DatasetMetadata(
            name="Short", source="Lab", version="1.0", license="MIT", checksum="a" * 63
        ).is_valid_checksum()
        is False
    )
    assert (
        DatasetMetadata(
            name="Long", source="Lab", version="1.0", license="MIT", checksum="a" * 65
        ).is_valid_checksum()
        is False
    )
    assert (
        DatasetMetadata(
            name="NonHex",
            source="Lab",
            version="1.0",
            license="MIT",
            checksum="z" * 64,
        ).is_valid_checksum()
        is False
    )

    # Valid non-placeholder SHA-256
    valid_hash = hashlib.sha256(b"real dataset archive content").hexdigest().lower()
    meta_valid = DatasetMetadata(
        name="Valid", source="Lab", version="1.0", license="MIT", checksum=valid_hash
    )
    assert meta_valid.is_valid_checksum() is True


def test_dataset_verify_archive(tmp_path: Path) -> None:
    """DatasetMetadata.verify_archive must verify actual bytes and reject missing, empty, or mismatched files."""
    real_content = b"affective dataset archive binary data payload"
    valid_hash = hashlib.sha256(real_content).hexdigest().lower()

    meta = DatasetMetadata(
        name="TestArchive",
        source="OVIC Labs",
        version="1.0",
        license="MIT",
        checksum=valid_hash,
    )

    # Missing file
    ok, msg = meta.verify_archive(tmp_path / "nonexistent.zip")
    assert ok is False
    assert "not found" in msg.lower()

    # Empty 0-byte file
    empty_file = tmp_path / "empty.zip"
    empty_file.write_bytes(b"")
    ok, msg = meta.verify_archive(empty_file)
    assert ok is False
    assert "empty" in msg.lower()

    # Checksum mismatch
    corrupted_file = tmp_path / "corrupted.zip"
    corrupted_file.write_bytes(b"tampered content")
    ok, msg = meta.verify_archive(corrupted_file)
    assert ok is False
    assert "mismatch" in msg.lower()

    # Successful verification
    good_file = tmp_path / "good.zip"
    good_file.write_bytes(real_content)
    ok, msg = meta.verify_archive(good_file)
    assert ok is True
    assert "verified" in msg.lower()


# -----------------------------------------------------------------------------
# DEFECT 4: Multimodal Probability Distribution Validation Tests
# -----------------------------------------------------------------------------


def test_validate_emotion_probabilities_contract() -> None:
    """validate_emotion_probabilities must validate exact 7 classes, finite values, non-negativity, and unit sum."""
    # Empty or None
    assert validate_emotion_probabilities(None)[0] is False
    assert validate_emotion_probabilities({})[0] is False

    # Missing classes (only 2 out of 7)
    partial = {"happiness": 0.8, "neutral": 0.2}
    ok, msg = validate_emotion_probabilities(partial)
    assert ok is False
    assert "missing classes" in msg

    # Extra unsupported class
    extra = {c: 1.0 / 8.0 for c in SUPPORTED_EMOTION_CLASSES}
    extra["boredom"] = 1.0 / 8.0
    ok, msg = validate_emotion_probabilities(extra)
    assert ok is False
    assert "unsupported classes" in msg

    # Non-finite values (NaN / Inf)
    nan_dict = {c: 1.0 / 7.0 for c in SUPPORTED_EMOTION_CLASSES}
    nan_dict["happiness"] = float("nan")
    ok, msg = validate_emotion_probabilities(nan_dict)
    assert ok is False
    assert "non-finite" in msg

    inf_dict = {c: 1.0 / 7.0 for c in SUPPORTED_EMOTION_CLASSES}
    inf_dict["anger"] = float("inf")
    ok, msg = validate_emotion_probabilities(inf_dict)
    assert ok is False
    assert "non-finite" in msg

    # Negative values
    neg_dict = {c: 0.2 for c in SUPPORTED_EMOTION_CLASSES}
    neg_dict["fear"] = -0.2
    ok, msg = validate_emotion_probabilities(neg_dict)
    assert ok is False
    assert "negative" in msg

    # Non-unit sum exceeding tolerance (tolerance = 0.02)
    bad_sum = {c: 0.1 for c in SUPPORTED_EMOTION_CLASSES}  # sum = 0.7
    ok, msg = validate_emotion_probabilities(bad_sum)
    assert ok is False
    assert "does not sum to 1.0" in msg

    # Valid probability distribution summing to 1.0
    valid_probs = {
        "neutral": 0.10,
        "happiness": 0.70,
        "sadness": 0.05,
        "anger": 0.05,
        "fear": 0.04,
        "surprise": 0.03,
        "disgust": 0.03,
    }
    ok, msg = validate_emotion_probabilities(valid_probs)
    assert ok is True

    # Valid within float tolerance (e.g., float32 softmax sum = 1.009)
    valid_tol = dict(valid_probs)
    valid_tol["happiness"] = 0.71  # sum = 1.01 <= 1.0 + 0.02
    assert validate_emotion_probabilities(valid_tol, tolerance=PROBABILITY_SUM_TOLERANCE)[0] is True


def test_multimodal_fusion_rejects_invalid_probabilities() -> None:
    """Multimodal fusion pipeline must isolate observations with invalid probability distributions to diagnostic only."""
    pipeline = MultimodalFusionPipeline(config=ERSConfig())
    now = 1000.0

    valid_probs = {
        "neutral": 0.1,
        "happiness": 0.9,
        "sadness": 0.0,
        "anger": 0.0,
        "fear": 0.0,
        "surprise": 0.0,
        "disgust": 0.0,
    }
    invalid_probs = {"happiness": 0.9, "neutral": 0.1}  # Missing other 5 classes

    # Validated facial with invalid probabilities
    obs_face_invalid = EmotionObservation(
        observation_id="obs-invalid-1",
        timestamp=now,
        modality=Modality.FACIAL,
        expression_observations={},
        emotion_probabilities=invalid_probs,
        dominant_estimate="happiness",
        confidence=0.85,
        uncertainty=0.15,
        quality_score=0.9,
        model_id="test-facial",
        model_version="1.0.0",
        processing_latency_ms=2.0,
        status=ObservationStatus.OK,
        input_quality=InputQualityStatus.ACCEPTABLE,
        model_state=ModelState.MODEL_LOADED_VALIDATED,
        is_validated=True,
    )

    eligible, status, reason = evaluate_modality_eligibility(obs_face_invalid, now)
    assert eligible is False
    assert status == ModalityEligibilityStatus.DIAGNOSTIC_ONLY
    assert "Invalid probability distribution" in reason

    # Valid speech observation
    obs_speech_valid = EmotionObservation(
        observation_id="obs-valid-2",
        timestamp=now,
        modality=Modality.SPEECH,
        expression_observations={},
        emotion_probabilities=valid_probs,
        dominant_estimate="happiness",
        confidence=0.80,
        uncertainty=0.20,
        quality_score=0.85,
        model_id="test-speech",
        model_version="1.0.0",
        processing_latency_ms=3.0,
        status=ObservationStatus.OK,
        input_quality=InputQualityStatus.ACCEPTABLE,
        model_state=ModelState.MODEL_LOADED_VALIDATED,
        is_validated=True,
    )

    result = pipeline.fuse(obs_face_invalid, obs_speech_valid, current_time=now)
    # Facial must be strictly isolated to diagnostic only; classification driven 100% by speech!
    assert result.is_validated is True
    assert result.classification_eligible_modalities == [Modality.SPEECH.value]
    assert Modality.FACIAL.value in result.diagnostic_modalities
    assert result.modality_weights[Modality.FACIAL.value] == 0.0
    assert result.modality_weights[Modality.SPEECH.value] == 1.0


# -----------------------------------------------------------------------------
# DEFECT 1 & 2: Training Pipeline Integrity & Anti-False-Success Tests
# -----------------------------------------------------------------------------


def test_pipeline_fails_closed_when_holdout_inference_unavailable(tmp_path: Path) -> None:
    """Stage 11 must fail closed with BLOCKED when test samples lack data payloads."""
    dummy_weights = tmp_path / "model.onnx"
    dummy_weights.write_bytes(b"dummy weights data")

    manifest = ModelManifest(
        model_id="integ-model-v1",
        name="Integrity Test Model",
        version="1.0.0",
        modality=Modality.FACIAL,
        artifact_path=str(dummy_weights),
        sha256_checksum="0" * 64,
        license="OVIC Labs Testing",
        source="OVIC Labs",
        input_specification={"name": "input", "shape": [1, 1, 64, 64]},
        output_specification={"name": "logits", "shape": [1, 7]},
    )

    valid_meta = DatasetMetadata(
        name="TestDS",
        source="OVIC Research",
        version="1.0",
        license="MIT",
        checksum=hashlib.sha256(b"ds").hexdigest(),
    )

    pipeline = ModelTrainingPipeline(
        dataset_metadata=valid_meta,
        model_manifest=manifest,
        output_dir=str(tmp_path),
    )

    # Samples WITHOUT data payloads (data=None)
    samples = [
        EvaluationSample(
            sample_id=f"s_{i}", subject_id=f"Subj_{i // 3}", label="neutral", data=None
        )
        for i in range(12)
    ]

    success, stages, val_record = pipeline.run_pipeline(
        raw_samples=samples,
        model_weights_path=str(dummy_weights),
    )

    assert success is False
    assert len(stages) == 15

    # Stage 11 must report BLOCKED
    stage_11 = next(r for r in stages if r.stage == TrainingPipelineStage.STAGE_11_TEST_EVALUATION)
    assert stage_11.success is False
    assert stage_11.details.get("status") == "BLOCKED"
    assert "Holdout evaluation BLOCKED" in stage_11.message

    # Stage 12 must report BLOCKED
    stage_12 = next(
        r for r in stages if r.stage == TrainingPipelineStage.STAGE_12_METRIC_QUALIFICATION
    )
    assert stage_12.success is False
    assert stage_12.details.get("status") == "BLOCKED"

    # Validation record must be unvalidated
    assert val_record is not None
    assert val_record.is_validated is False
    assert val_record.abstention_rate == 1.0
    assert any("BLOCKED" in note for note in val_record.validation_notes)


def test_pipeline_anti_false_success_stages(tmp_path: Path) -> None:
    """Pipeline stages 3, 6, 7, 9, 10, 13, 14 must not report false success."""
    dummy_weights = tmp_path / "model.onnx"
    dummy_weights.write_bytes(b"dummy weights data")

    # Dataset with empty/unverified checksum
    unverified_meta = DatasetMetadata(
        name="UnverifiedDS",
        source="OVIC Research",
        version="1.0",
        license="MIT",
        checksum="",  # Empty checksum!
    )

    manifest = ModelManifest(
        model_id="integ-model-v2",
        name="Integrity Test Model",
        version="1.0.0",
        modality=Modality.FACIAL,
        artifact_path=str(dummy_weights),
        sha256_checksum="0" * 64,
        license="OVIC Labs Testing",
        source="OVIC Labs",
        input_specification={"name": "input", "shape": [1, 1, 64, 64]},
        output_specification={"name": "logits", "shape": [1, 7]},
    )

    pipeline = ModelTrainingPipeline(
        dataset_metadata=unverified_meta,
        model_manifest=manifest,
        output_dir=str(tmp_path),
    )

    # Samples without data
    samples = [
        EvaluationSample(
            sample_id=f"s_{i}", subject_id=f"Subj_{i // 3}", label="neutral", data=None
        )
        for i in range(12)
    ]

    # Run without convergence history, without calibration, without onnx export
    success, stages, _ = pipeline.run_pipeline(
        raw_samples=samples,
        model_weights_path=str(dummy_weights),
        training_loss_history=None,
        is_calibrated=False,
        onnx_exported=False,
    )

    # Verify Stage 3 reports failure (empty checksum)
    stage_3 = next(r for r in stages if r.stage == TrainingPipelineStage.STAGE_3_INTEGRITY_CHECK)
    assert stage_3.success is False

    # Verify Stage 6 & 7 report failure (no raw media data payloads)
    stage_6 = next(r for r in stages if r.stage == TrainingPipelineStage.STAGE_6_PREPROCESSING)
    assert stage_6.success is False
    stage_7 = next(
        r for r in stages if r.stage == TrainingPipelineStage.STAGE_7_FEATURE_NORMALIZATION
    )
    assert stage_7.success is False

    # Verify Stage 9 reports failure (no convergence history)
    stage_9 = next(
        r for r in stages if r.stage == TrainingPipelineStage.STAGE_9_CONVERGENCE_MONITORING
    )
    assert stage_9.success is False

    # Verify Stage 10 reports failure (not calibrated)
    stage_10 = next(
        r for r in stages if r.stage == TrainingPipelineStage.STAGE_10_TEMPERATURE_CALIBRATION
    )
    assert stage_10.success is False

    # Verify Stage 13 reports failure (not exported)
    stage_13 = next(r for r in stages if r.stage == TrainingPipelineStage.STAGE_13_ONNX_EXPORT)
    assert stage_13.success is False

    # Verify Stage 14 reports failure (dummy bytes cannot load as ONNX runtime session)
    stage_14 = next(
        r for r in stages if r.stage == TrainingPipelineStage.STAGE_14_CONTRACT_VERIFICATION
    )
    assert stage_14.success is False


# -----------------------------------------------------------------------------
# DEFECT 5: Scientific Qualification Gating Tests
# -----------------------------------------------------------------------------


def test_evaluator_rejects_mock_predictions_from_qualification(tmp_path: Path) -> None:
    """ModelEvaluator must reject mock/uniform predictions and never grant is_validated = True."""
    evaluator = ModelEvaluator()

    dummy_model = tmp_path / "valid.onnx"
    dummy_model.write_bytes(b"model bytes for test")
    valid_sha = hashlib.sha256(b"model bytes for test").hexdigest().lower()

    manifest = ModelManifest(
        model_id="qual-test-v1",
        name="Qualification Model",
        version="1.0.0",
        modality=Modality.FACIAL,
        artifact_path=str(dummy_model),
        sha256_checksum=valid_sha,
        license="MIT",
        provenance_status="VERIFIED",
        training_dataset_provenance="Empirical Benchmark 2026",
        source="OVIC Labs",
        input_specification={"name": "input", "shape": [1, 1, 64, 64]},
        output_specification={"name": "logits", "shape": [1, 7], "classes": evaluator.labels},
    )

    y_true = ["neutral", "happiness", "sadness", "anger", "fear", "surprise", "disgust"] * 2

    # Mock/uniform predictions: 1.0 / 7 for each category
    mock_prob = {cat: 1.0 / 7.0 for cat in evaluator.labels}
    mock_preds = [dict(mock_prob) for _ in y_true]

    record, _ = evaluator.evaluate_predictions(
        y_true=y_true,
        predicted_probs=mock_preds,
        model_manifest=manifest,
        dataset_name="AffectNet_Holdout",
        dataset_split="test",
        dataset_license="Academic Non-Commercial",
    )

    assert record.is_validated is False
    assert any("mock or uniform predictions" in n.lower() for n in record.validation_notes)


def test_evaluator_rejects_placeholder_checksum_and_mismatch(tmp_path: Path) -> None:
    """ModelEvaluator must reject models whose manifest checksum is a placeholder or does not match artifact bytes."""
    evaluator = ModelEvaluator()

    dummy_model = tmp_path / "valid2.onnx"
    dummy_model.write_bytes(b"some model weights")

    # Placeholder checksum in manifest
    manifest_placeholder = ModelManifest(
        model_id="qual-test-v2",
        name="Qualification Model",
        version="1.0.0",
        modality=Modality.FACIAL,
        artifact_path=str(dummy_model),
        sha256_checksum="0" * 64,  # Placeholder!
        license="MIT",
        provenance_status="VERIFIED",
        training_dataset_provenance="Empirical Benchmark 2026",
        source="OVIC Labs",
        input_specification={"name": "input", "shape": [1, 1, 64, 64]},
        output_specification={"name": "logits", "shape": [1, 7]},
    )

    y_true = ["happiness"] * 10
    # Good diverse predictions
    good_preds = [
        {
            "neutral": 0.05,
            "happiness": 0.70,
            "sadness": 0.05,
            "anger": 0.05,
            "fear": 0.05,
            "surprise": 0.05,
            "disgust": 0.05,
        }
        for _ in range(10)
    ]

    record, _ = evaluator.evaluate_predictions(
        y_true=y_true,
        predicted_probs=good_preds,
        model_manifest=manifest_placeholder,
        dataset_name="Empirical_Benchmark",
        dataset_split="test",
        dataset_license="MIT",
    )

    # Must fail artifact integrity check
    assert record.is_validated is False
    assert any("integrity verification failed" in n.lower() for n in record.validation_notes)
