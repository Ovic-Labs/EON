"""Phase 3.1.7 Integrity & Security Hardening comprehensive test suite.

Covers:
1. Dataset integrity negative tests (missing archives, invalid/placeholder digests, mismatches, malformed metadata).
2. Authenticated Ed25519 execution proof tests (key management, PEM loading, tampering, invalid signatures, unknown/revoked keys, malformed proofs).
3. Training pipeline hardening (deprecation/rejection of legacy bypass flags, failed-stage qualification blocking).
4. Model weights loading & validation (rejecting empty, corrupted, incompatible, partially loaded external weights, and NaN/Inf initializers).
5. Evaluator & metrics input validation (eliminating zip() silent truncation, rejecting mismatched sample counts, empty datasets, invalid values, unsupported labels, dimension mismatches).
6. ONNX export strict dimensions & numerical parity tests (no silent padding/truncation, parity tolerances, parity failure rejection, CPU-only end-to-end integration).
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from eon_ers.evaluation.dataset import (
    EMPTY_BYTES_SHA256,
    DatasetMetadata,
    EvaluationSample,
)
from eon_ers.evaluation.evaluator import (
    EvaluationExecutionProof,
    ModelEvaluator,
    SigningKeyPair,
    TrustedKeyRegistry,
)
from eon_ers.evaluation.metrics import (
    compute_calibration_metrics,
    compute_classification_metrics,
    compute_confidence_distribution,
    compute_confusion_matrix,
)
from eon_ers.exceptions import ERSModelIntegrityError, ERSModelUnavailableError
from eon_ers.facial.adapters import ONNXFacialModelAdapter
from eon_ers.models.loader import ModelLoader
from eon_ers.models.manifest import ModelManifest
from eon_ers.speech.adapters import ONNXSpeechModelAdapter
from eon_ers.training.export import ONNX_LOGIT_PARITY_ATOL, ONNXModelExporter
from eon_ers.training.pipeline import ModelTrainingPipeline, TrainingPipelineStage
from eon_ers.training.trainer import (
    TrainedModelArtifact,
    TrainingConfig,
    TrainingHistory,
)
from eon_ers.types import Modality

LABELS_7 = ["neutral", "happiness", "sadness", "anger", "fear", "surprise", "disgust"]


def _make_manifest(
    model_path: Path,
    sha256_checksum: str,
    *,
    input_dim: int = 64,
    num_classes: int = 7,
    classes: list[str] | None = None,
    provenance_status: str = "VERIFIED",
    training_dataset_provenance: str = "Empirical Affective Benchmark 2026",
) -> ModelManifest:
    return ModelManifest(
        model_id="ers-hardening-test-v1",
        name="ERS Hardening Test Model",
        version="1.0.0",
        modality=Modality.FACIAL,
        artifact_path=str(model_path),
        sha256_checksum=sha256_checksum,
        license="Academic MIT",
        provenance_status=provenance_status,
        training_dataset_provenance=training_dataset_provenance,
        source="OVIC Labs",
        input_specification={"name": "input_image", "shape": [1, input_dim], "dtype": "float32"},
        output_specification={
            "name": "logits",
            "shape": [1, num_classes],
            "classes": classes if classes is not None else LABELS_7[:num_classes],
        },
    )


def _make_trained_artifact(
    input_dim: int = 64,
    hidden_dim: int = 16,
    num_classes: int = 7,
    seed: int = 7,
) -> TrainedModelArtifact:
    rng = np.random.RandomState(seed)
    W1 = (rng.randn(input_dim, hidden_dim) * 0.1).astype(np.float32)
    b1 = (rng.randn(hidden_dim) * 0.05).astype(np.float32)
    W2 = (rng.randn(hidden_dim, num_classes) * 0.1).astype(np.float32)
    b2 = (rng.randn(num_classes) * 0.05).astype(np.float32)
    hist = TrainingHistory(
        epochs=[1, 2],
        train_loss=[1.4, 1.1],
        val_loss=[1.5, 1.2],
        train_acc=[0.4, 0.6],
        val_acc=[0.35, 0.55],
        best_epoch=2,
        best_val_loss=1.2,
        stopped_early=False,
        converged=True,
        overfitting_detected=False,
        trained_at="2026-11-25T00:00:00Z",
        training_duration_seconds=0.5,
        training_signature="b" * 64,
    )
    return TrainedModelArtifact(
        W1=W1,
        b1=b1,
        W2=W2,
        b2=b2,
        config=TrainingConfig(input_dim=input_dim, hidden_dim=hidden_dim, num_classes=num_classes),
        class_labels=LABELS_7[:num_classes],
        history=hist,
    )


# -----------------------------------------------------------------------------
# 1. DATASET INTEGRITY NEGATIVE TESTS
# -----------------------------------------------------------------------------


def test_dataset_rejects_malformed_metadata_and_missing_archives(tmp_path: Path) -> None:
    """DatasetMetadata must reject blank/malformed metadata and missing archives."""
    for bad_field in ("name", "source", "version", "license", "partition_strategy"):
        kwargs = {
            "name": "ValidDS",
            "source": "OVIC",
            "version": "1.0",
            "license": "MIT",
            "partition_strategy": "subject_independent",
        }
        kwargs[bad_field] = "   "
        with pytest.raises(ValueError, match="cannot be empty"):
            DatasetMetadata(**kwargs)

    valid_sha = hashlib.sha256(b"real archive bytes").hexdigest().lower()
    meta = DatasetMetadata(
        name="ValidDS",
        source="OVIC",
        version="1.0",
        license="MIT",
        checksum=valid_sha,
    )

    # None / blank / directory / missing archive must fail
    ok_none, msg_none = meta.verify_archive(None)
    assert ok_none is False
    assert "missing" in msg_none.lower()

    ok_dir, msg_dir = meta.verify_archive(tmp_path)
    assert ok_dir is False
    assert "not found" in msg_dir.lower()

    # Placeholder checksum passed directly as expected_sha256 must be rejected
    archive = tmp_path / "real.zip"
    archive.write_bytes(b"real archive bytes")
    ok_ph, msg_ph = meta.verify_archive(archive, expected_sha256=EMPTY_BYTES_SHA256)
    assert ok_ph is False
    assert "placeholder" in msg_ph.lower()

    # Manifest verification without expected checksum must fail (never silently skip)
    manifest_file = tmp_path / "manifest.json"
    manifest_file.write_text('{"samples": []}', encoding="utf-8")
    ok_man, msg_man, _ = meta.verify_manifest(manifest_file)
    assert ok_man is False
    assert "missing" in msg_man.lower()


def test_pipeline_stage3_never_accepts_checksum_format_without_archive(tmp_path: Path) -> None:
    """Stage 3 must fail when archive_path is omitted even if checksum format is valid."""
    valid_sha = hashlib.sha256(b"some real data").hexdigest().lower()
    meta = DatasetMetadata(
        name="FormatOnlyDS",
        source="OVIC Lab",
        version="1.0",
        license="Academic MIT",
        checksum=valid_sha,
    )
    assert meta.is_valid_checksum() is True

    dummy_onnx = tmp_path / "model.onnx"
    dummy_onnx.write_bytes(b"not an onnx")
    manifest = _make_manifest(dummy_onnx, sha256_checksum="0" * 64)

    samples = [
        EvaluationSample(sample_id=f"s{i}", subject_id=f"sub{i % 4}", label="neutral", data=None)
        for i in range(12)
    ]
    pipeline = ModelTrainingPipeline(meta, manifest, output_dir=str(tmp_path))
    success, stages, record = pipeline.run_pipeline(
        raw_samples=samples,
        model_weights_path=str(dummy_onnx),
        archive_path=None,  # No physical archive!
    )

    assert success is False
    assert record is not None and record.is_validated is False
    stage_3 = next(s for s in stages if s.stage == TrainingPipelineStage.STAGE_3_INTEGRITY_CHECK)
    assert stage_3.success is False
    assert "checksum syntax alone is insufficient" in stage_3.message.lower()


# -----------------------------------------------------------------------------
# 2. CRYPTOGRAPHIC EXECUTION PROOF & TAMPERING TESTS
# -----------------------------------------------------------------------------


def test_ed25519_execution_proof_key_management_and_tampering(tmp_path: Path) -> None:
    """Ed25519 proofs must verify against trusted public keys and reject tampering/unknown keys."""
    keypair = SigningKeyPair.generate(key_id="ovic-prod-key-01")
    registry = TrustedKeyRegistry()
    # Export and re-import public key via PEM
    registry.register_public_key_pem("ovic-prod-key-01", keypair.public_key_pem())

    # Private key PEM serialization round-trip
    priv_pem = keypair._private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    reloaded_key = SigningKeyPair.from_pem("ovic-prod-key-01", priv_pem)

    art_sha = hashlib.sha256(b"real model weights").hexdigest().lower()
    ds_sha = hashlib.sha256(b"real dataset archive").hexdigest().lower()

    proof = EvaluationExecutionProof.generate_proof(
        model_id="ers-facial-v1",
        artifact_sha256=art_sha,
        dataset_archive_sha256=ds_sha,
        dataset_name="AffectNet_Holdout",
        dataset_provenance="Academic License",
        subject_count=12,
        sample_count=50,
        signing_key=reloaded_key,
    )

    assert proof.key_id == "ovic-prod-key-01"
    assert proof.signature_algorithm == "Ed25519"
    assert proof.verify(art_sha, key_registry=registry, expected_dataset_archive_sha256=ds_sha)

    # 1. Verification without registry MUST fail
    assert proof.verify(art_sha, key_registry=None) is False

    # 2. Tampering ANY signed field MUST invalidate Ed25519 signature
    for field, tampered_val in [
        ("sample_count", 9999),
        ("subject_count", 99),
        ("dataset_name", "SpoofedDataset"),
        ("dataset_archive_sha256", hashlib.sha256(b"other").hexdigest().lower()),
        ("artifact_sha256", hashlib.sha256(b"other model").hexdigest().lower()),
        ("execution_timestamp", "2099-01-01T00:00:00Z"),
    ]:
        tampered = proof.model_copy(update={field: tampered_val})
        assert tampered.verify(art_sha, key_registry=registry) is False

    # 3. Invalid/bit-flipped signature MUST be rejected
    flipped_char = "0" if proof.proof_signature[0] != "0" else "1"
    bad_sig_proof = proof.model_copy(
        update={"proof_signature": flipped_char + proof.proof_signature[1:]}
    )
    assert bad_sig_proof.verify(art_sha, key_registry=registry) is False

    # 4. Signed with an untrusted / different key MUST be rejected
    rogue_key = SigningKeyPair.generate(key_id="rogue-key-99")
    rogue_proof = EvaluationExecutionProof.generate_proof(
        model_id="ers-facial-v1",
        artifact_sha256=art_sha,
        dataset_archive_sha256=ds_sha,
        dataset_name="AffectNet_Holdout",
        dataset_provenance="Academic License",
        subject_count=12,
        sample_count=50,
        signing_key=rogue_key,
    )
    assert rogue_proof.verify(art_sha, key_registry=registry) is False

    # 5. Claiming trusted key_id but signed with rogue key's private key MUST be rejected
    spoofed_id_key = SigningKeyPair(
        key_id="ovic-prod-key-01", private_key=Ed25519PrivateKey.generate()
    )
    forged_proof = EvaluationExecutionProof.generate_proof(
        model_id="ers-facial-v1",
        artifact_sha256=art_sha,
        dataset_archive_sha256=ds_sha,
        dataset_name="AffectNet_Holdout",
        dataset_provenance="Academic License",
        subject_count=12,
        sample_count=50,
        signing_key=spoofed_id_key,
    )
    assert forged_proof.verify(art_sha, key_registry=registry) is False

    # 6. Revoking trusted key invalidates subsequent verification
    assert registry.revoke_key("ovic-prod-key-01") is True
    assert proof.verify(art_sha, key_registry=registry) is False

    # 7. Malformed proof fields rejected by Pydantic schema
    with pytest.raises(ValueError):
        EvaluationExecutionProof(
            key_id="k1",
            model_id="m1",
            artifact_sha256=art_sha,
            dataset_archive_sha256=ds_sha,
            dataset_name="DS",
            dataset_provenance="MIT",
            subject_count=2,
            sample_count=10,
            execution_timestamp="2026-11-25T00:00:00Z",
            proof_signature="not-hex-" + "0" * 120,
        )


def test_signing_keypair_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """SigningKeyPair.from_env must load PEM private key cleanly without hardcoded secrets."""
    assert SigningKeyPair.from_env() is None
    kp = SigningKeyPair.generate(key_id="env-key-1")
    priv_pem = kp._private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("utf-8")
    monkeypatch.setenv("EON_ERS_SIGNING_KEY_ID", "env-key-1")
    monkeypatch.setenv("EON_ERS_SIGNING_PRIVATE_KEY_PEM", priv_pem)
    loaded = SigningKeyPair.from_env()
    assert loaded is not None
    assert loaded.key_id == "env-key-1"


# -----------------------------------------------------------------------------
# 3. TRAINING PIPELINE ANTI-BYPASS & STAGE-GATING TESTS
# -----------------------------------------------------------------------------


def test_pipeline_rejects_legacy_bypass_arguments(tmp_path: Path) -> None:
    """Pipeline must reject deprecated flags that previously claimed success without execution."""
    meta = DatasetMetadata(name="DS", source="Lab", version="1.0", license="MIT", checksum="")
    manifest = _make_manifest(tmp_path / "m.onnx", sha256_checksum="0" * 64)
    pipeline = ModelTrainingPipeline(meta, manifest, output_dir=str(tmp_path))
    samples = [
        EvaluationSample(sample_id=f"s{i}", subject_id=f"sub{i}", label="neutral") for i in range(6)
    ]

    for bad_kwargs in [
        {"training_loss_history": [1.0, 0.4]},
        {"is_calibrated": True},
        {"optimal_temperature": 1.2},
        {"onnx_exported": True},
    ]:
        with pytest.warns(DeprecationWarning):
            with pytest.raises(ValueError, match="Legacy bypass arguments"):
                pipeline.run_pipeline(raw_samples=samples, **bad_kwargs)  # type: ignore[arg-type]


# -----------------------------------------------------------------------------
# 4. MODEL WEIGHTS LOADING & ARCHITECTURE VALIDATION TESTS
# -----------------------------------------------------------------------------


def test_model_loader_rejects_empty_corrupted_incompatible_and_partial_weights(
    tmp_path: Path,
) -> None:
    """ModelLoader must actually load weights and reject empty, corrupted, incompatible, or partial ONNX files."""
    onnx = pytest.importorskip("onnx")
    from onnx import TensorProto, helper, numpy_helper

    # 1. Missing weights
    with pytest.raises(ERSModelUnavailableError):
        ModelLoader.validate_and_load_onnx_weights(tmp_path / "missing.onnx")

    # 2. Empty 0-byte weights
    empty_file = tmp_path / "empty.onnx"
    empty_file.write_bytes(b"")
    with pytest.raises(ERSModelIntegrityError, match="empty"):
        ModelLoader.validate_and_load_onnx_weights(empty_file)

    # 3. Corrupted non-ONNX bytes (previously bypassed file-existence checks!)
    corrupt_file = tmp_path / "corrupt.onnx"
    corrupt_file.write_bytes(b"not valid onnx protobuf bytes at all")
    with pytest.raises(ERSModelIntegrityError, match="Corrupted"):
        ModelLoader.validate_and_load_onnx_weights(corrupt_file)

    # 4. ONNX graph containing NaN initializer weights
    W_nan = np.full((16, 7), np.nan, dtype=np.float32)
    b_zero = np.zeros(7, dtype=np.float32)
    t_W = numpy_helper.from_array(W_nan, name="W_nan")
    t_b = numpy_helper.from_array(b_zero, name="b")
    g_nan = helper.make_graph(
        [helper.make_node("Gemm", ["input", "W_nan", "b"], ["logits"])],
        "nan_graph",
        [helper.make_tensor_value_info("input", TensorProto.FLOAT, [1, 16])],
        [helper.make_tensor_value_info("logits", TensorProto.FLOAT, [1, 7])],
        initializer=[t_W, t_b],
    )
    nan_path = tmp_path / "nan_weights.onnx"
    nan_path.write_bytes(helper.make_model(g_nan, producer_name="test").SerializeToString())
    with pytest.raises(ERSModelIntegrityError, match="non-finite"):
        ModelLoader.validate_and_load_onnx_weights(nan_path)

    # 5. Partially loaded external-data ONNX weights (missing external weights binary)
    ext_tensor = TensorProto(
        name="W_ext",
        data_type=TensorProto.FLOAT,
        dims=[16, 7],
        data_location=TensorProto.EXTERNAL,
    )
    ext_entry = ext_tensor.external_data.add()
    ext_entry.key = "location"
    ext_entry.value = "missing_weights.data"
    g_ext = helper.make_graph(
        [helper.make_node("Gemm", ["input", "W_ext", "b"], ["logits"])],
        "ext_graph",
        [helper.make_tensor_value_info("input", TensorProto.FLOAT, [1, 16])],
        [helper.make_tensor_value_info("logits", TensorProto.FLOAT, [1, 7])],
        initializer=[ext_tensor, t_b],
    )
    ext_path = tmp_path / "partial_external.onnx"
    ext_path.write_bytes(helper.make_model(g_ext, producer_name="test").SerializeToString())
    with pytest.raises(ERSModelIntegrityError, match="Partially loaded|external"):
        ModelLoader.validate_and_load_onnx_weights(ext_path)

    # 6. Incompatible tensor architecture vs manifest (valid ONNX file, wrong dtype/shape)
    W_good = np.ones((16, 7), dtype=np.float32) * 0.05
    t_Wg = numpy_helper.from_array(W_good, name="W_good")
    g_good = helper.make_graph(
        [helper.make_node("Gemm", ["input_image", "W_good", "b"], ["logits"])],
        "good_graph",
        [helper.make_tensor_value_info("input_image", TensorProto.FLOAT, [1, 16])],
        [helper.make_tensor_value_info("logits", TensorProto.FLOAT, [1, 7])],
        initializer=[t_Wg, t_b],
    )
    good_path = tmp_path / "good_16.onnx"
    onnx_bytes = helper.make_model(g_good, producer_name="test").SerializeToString()
    onnx.checker.check_model(onnx.load_from_string(onnx_bytes))
    good_path.write_bytes(onnx_bytes)
    good_sha = hashlib.sha256(onnx_bytes).hexdigest().lower()

    wrong_shape_manifest = _make_manifest(good_path, good_sha, input_dim=64, num_classes=7)
    with pytest.raises(ERSModelIntegrityError, match="shape mismatch"):
        ModelLoader.validate_and_load_onnx_weights(
            good_path, manifest=wrong_shape_manifest, expected_classes=LABELS_7
        )

    # 7. Adapters without manifests must also reject corrupted ONNX files
    face_adapter = ONNXFacialModelAdapter(model_path=str(corrupt_file))
    assert face_adapter.is_available is False
    speech_adapter = ONNXSpeechModelAdapter(model_path=str(corrupt_file))
    assert speech_adapter.is_available is False


# -----------------------------------------------------------------------------
# 5. EVALUATOR & METRICS VALIDATION TESTS (NO SILENT ZIP TRUNCATION)
# -----------------------------------------------------------------------------


def test_evaluator_and_metrics_reject_mismatches_empty_invalid_and_unsupported(
    tmp_path: Path,
) -> None:
    """Evaluator and metrics functions must eliminate silent zip() truncation and validate all inputs."""
    evaluator = ModelEvaluator(labels=LABELS_7)
    dummy_model = tmp_path / "m.onnx"
    dummy_model.write_bytes(b"weights")
    sha = hashlib.sha256(b"weights").hexdigest().lower()
    manifest = _make_manifest(dummy_model, sha, input_dim=64, num_classes=7)

    valid_p = {lbl: (0.70 if lbl == "neutral" else 0.05) for lbl in LABELS_7}

    # 1. Empty inputs rejected
    with pytest.raises(ValueError, match="empty"):
        evaluator.evaluate_predictions([], [], manifest, "DS", "test", "MIT")
    with pytest.raises(ValueError, match="empty"):
        compute_confusion_matrix([], [], LABELS_7)
    with pytest.raises(ValueError, match="empty"):
        compute_calibration_metrics([], [], LABELS_7)
    with pytest.raises(ValueError, match="empty"):
        compute_confidence_distribution([])

    # 2. Mismatched sample counts rejected (no silent zip truncation!)
    with pytest.raises(ValueError, match="Mismatched sample counts"):
        evaluator.evaluate_predictions(
            ["neutral", "happiness", "sadness"],
            [valid_p, valid_p],
            manifest,
            "DS",
            "test",
            "MIT",
        )
    with pytest.raises(ValueError, match="Mismatched sample counts"):
        compute_confusion_matrix(["neutral", "happiness"], ["neutral"], LABELS_7)
    with pytest.raises(ValueError, match="Mismatched sample counts"):
        compute_classification_metrics(["neutral"], ["neutral", "happiness"], LABELS_7)
    with pytest.raises(ValueError, match="Mismatched sample counts"):
        compute_calibration_metrics(["neutral", "happiness"], [valid_p], LABELS_7)

    # 3. Unsupported labels rejected
    with pytest.raises(ValueError, match="Unsupported ground-truth label"):
        evaluator.evaluate_predictions(["boredom"], [valid_p], manifest, "DS", "test", "MIT")
    with pytest.raises(ValueError, match="Unsupported predicted label"):
        compute_confusion_matrix(["neutral"], ["boredom"], LABELS_7)

    # 4. Invalid probability values (NaN, negative, > 1.0, missing class, bad sum) rejected
    nan_p = dict(valid_p)
    nan_p["neutral"] = float("nan")
    with pytest.raises(ValueError, match="Non-finite"):
        evaluator.evaluate_predictions(["neutral"], [nan_p], manifest, "DS", "test", "MIT")

    neg_p = dict(valid_p)
    neg_p["fear"] = -0.05
    with pytest.raises(ValueError, match="out of bounds"):
        evaluator.evaluate_predictions(["neutral"], [neg_p], manifest, "DS", "test", "MIT")

    partial_p = {"neutral": 0.9, "happiness": 0.1}
    with pytest.raises(ValueError, match="Invalid probability keys"):
        evaluator.evaluate_predictions(["neutral"], [partial_p], manifest, "DS", "test", "MIT")

    bad_sum_p = {lbl: 0.05 for lbl in LABELS_7}  # sum = 0.35
    with pytest.raises(ValueError, match="within"):
        evaluator.evaluate_predictions(["neutral"], [bad_sum_p], manifest, "DS", "test", "MIT")

    # 5. Manifest dimension mismatch rejected
    wrong_dim_manifest = _make_manifest(dummy_model, sha, input_dim=64, num_classes=5)
    with pytest.raises(ValueError, match="dimension mismatch"):
        evaluator.evaluate_predictions(
            ["neutral"], [valid_p], wrong_dim_manifest, "DS", "test", "MIT"
        )


# -----------------------------------------------------------------------------
# 6. ONNX EXPORT STRICT DIMENSIONS & NUMERICAL PARITY TESTS
# -----------------------------------------------------------------------------


def test_onnx_export_rejects_dimension_mismatch_without_padding_or_truncation(
    tmp_path: Path,
) -> None:
    """ONNXModelExporter must reject input/output shape mismatches rather than padding or slicing weights."""
    pytest.importorskip("onnx")
    artifact = _make_trained_artifact(input_dim=64, hidden_dim=16, num_classes=7)
    exporter = ONNXModelExporter()

    # Manifest expects 128 dims while artifact has 64 -> must FAIL (no silent zero-padding)
    out_pad = tmp_path / "would_pad.onnx"
    manifest_larger = _make_manifest(out_pad, "0" * 64, input_dim=128, num_classes=7)
    ok_larger, meta_larger, msg_larger = exporter.export(artifact, manifest_larger, out_pad)
    assert ok_larger is False
    assert meta_larger is None
    assert "silent padding and truncation are prohibited" in msg_larger.lower()
    assert not out_pad.exists()

    # Manifest expects 32 dims while artifact has 64 -> must FAIL (no silent truncation)
    out_trunc = tmp_path / "would_trunc.onnx"
    manifest_smaller = _make_manifest(out_trunc, "0" * 64, input_dim=32, num_classes=7)
    ok_smaller, meta_smaller, msg_smaller = exporter.export(artifact, manifest_smaller, out_trunc)
    assert ok_smaller is False
    assert meta_smaller is None
    assert "mismatch" in msg_smaller.lower()
    assert not out_trunc.exists()


def test_onnx_export_numerical_parity_verification_and_failure_gating(tmp_path: Path) -> None:
    """ONNXModelExporter must verify CPU ONNX parity against reference predictions and fail when parity breaks."""
    pytest.importorskip("onnx")
    import onnxruntime as ort

    artifact = _make_trained_artifact(input_dim=64, hidden_dim=16, num_classes=7)
    exporter = ONNXModelExporter()
    out_path = tmp_path / "parity_model.onnx"
    manifest = _make_manifest(out_path, "0" * 64, input_dim=64, num_classes=7)

    # 1. Valid export passes numerical parity check on CPU
    temp = 1.35
    ok, meta, msg = exporter.export(artifact, manifest, out_path, temperature=temp)
    assert ok is True
    assert meta is not None
    assert meta.parity_verified is True
    assert meta.max_logit_diff <= ONNX_LOGIT_PARITY_ATOL
    assert out_path.is_file()

    # Explicit CPU parity check on unseen random batch
    sess = ort.InferenceSession(str(out_path), providers=["CPUExecutionProvider"])
    probe = np.random.RandomState(99).randn(1, 64).astype(np.float32)
    onnx_logits = sess.run(None, {"input_image": probe})[0]
    ref_logits = artifact.predict_logits(probe) / temp
    assert np.allclose(onnx_logits, ref_logits, atol=1e-4, rtol=1e-4)

    # 2. Divergent reference predictions must cause export failure and remove output file
    bad_out_path = tmp_path / "bad_parity.onnx"
    manifest_bad = _make_manifest(bad_out_path, "0" * 64, input_dim=64, num_classes=7)
    ok_fail, meta_fail, msg_fail = exporter.export(
        artifact,
        manifest_bad,
        bad_out_path,
        temperature=temp,
        reference_fn=lambda x: np.full((x.shape[0], 7), 99.0, dtype=np.float32),
    )
    assert ok_fail is False
    assert meta_fail is None
    assert "parity check failed" in msg_fail.lower()
    assert not bad_out_path.exists()


def test_cpu_end_to_end_pipeline_signed_proof_and_synthetic_isolation(tmp_path: Path) -> None:
    """End-to-end CPU pipeline test verifying Ed25519 signing while keeping synthetic models unvalidated."""
    pytest.importorskip("onnx")

    archive_file = tmp_path / "synthetic_fixture_archive.zip"
    archive_file.write_bytes(b"synthetic fixture payload for integration testing only")
    archive_sha = hashlib.sha256(archive_file.read_bytes()).hexdigest().lower()

    dataset_meta = DatasetMetadata(
        name="SyntheticValidationFixture",
        source="OVIC Test Fixture",
        version="1.0.0",
        license="Academic Research License",
        commercial_allowed=False,
        checksum=archive_sha,
    )

    model_file = tmp_path / "e2e_cpu_model.onnx"
    manifest = _make_manifest(
        model_file,
        sha256_checksum="0" * 64,
        input_dim=128,
        num_classes=7,
        provenance_status="VERIFIED",
        training_dataset_provenance="Synthetic fixture (not empirical benchmark)",
    )

    signing_key = SigningKeyPair.generate(key_id="ovic-e2e-test-key")
    registry = TrustedKeyRegistry()
    registry.register_keypair(signing_key)

    samples: list[EvaluationSample] = []
    for s_idx in range(6):
        subj = f"Actor_{s_idx:02d}"
        for i in range(5):
            lbl_idx = (s_idx + i) % len(LABELS_7)
            noise = (
                np.random.RandomState(s_idx * 50 + i).normal(0.0, 0.02, (64, 64)).astype(np.float32)
            )
            img = np.clip(
                np.full((64, 64), 0.12 * (lbl_idx + 1), dtype=np.float32) + noise, 0.0, 1.0
            )
            samples.append(
                EvaluationSample(
                    sample_id=f"{subj}_{i}",
                    subject_id=subj,
                    label=LABELS_7[lbl_idx],
                    data=img,
                )
            )

    pipeline = ModelTrainingPipeline(dataset_meta, manifest, output_dir=str(tmp_path))
    success, stages, record = pipeline.run_pipeline(
        raw_samples=samples,
        model_weights_path=str(model_file),
        archive_path=archive_file,
        train_new_model=True,
        training_config=TrainingConfig(input_dim=128, num_classes=7, epochs=5, learning_rate=0.05),
        signing_key=signing_key,
        key_registry=registry,
    )

    assert len(stages) == 15
    assert record is not None
    # Software pipeline stages succeeded, ONNX file exists, and Ed25519 signature recorded...
    assert model_file.is_file()
    assert record.execution_proof_key_id == "ovic-e2e-test-key"
    assert record.execution_proof_algorithm == "Ed25519"
    assert len(record.execution_proof_signature) == 128
    # ...BUT scientific qualification MUST remain False because dataset is synthetic!
    assert success is False
    assert record.is_validated is False
    assert any("synthetic" in n.lower() for n in record.validation_notes)
