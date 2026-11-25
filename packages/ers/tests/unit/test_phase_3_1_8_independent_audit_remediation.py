"""Phase 3.1.8 Independent Audit Remediation & Regression Test Suite.

Verifies fixes for issues discovered during the full Phase 3.1.8 repository audit:
1. Cryptographic proof key rotation, revoked-key isolation, algorithm confusion rejection,
   malformed/RSA public key rejection, and env/file key provisioning edge cases.
2. Safe archive extraction (format checks, path traversal, symlinks, file count & zip-bomb limits)
   and duplicate/malformed sample/manifest rejection.
3. Model framework, modality, and major-version compatibility validation + validation record binding.
4. LiveSessionManager removal of consent_reference bypass, hashed consent token storage,
   buffer scrubbing on consent rejection, and ERSEngine.process_multimodal metadata/isolation propagation.
5. Live dashboard API/WebSocket schema contract consistency.
6. Exact analytical verification of confusion matrix, precision, recall, F1, balanced accuracy, Brier, and ECE (including b=0 zero-confidence edge case).
"""

from __future__ import annotations

import base64
import hashlib
import io
import tarfile
import zipfile
from pathlib import Path

import numpy as np
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from eon_ers.config import ERSConfig
from eon_ers.contracts import ERSInput
from eon_ers.engine import ERSEngine
from eon_ers.evaluation.dataset import (
    DatasetMetadata,
    EvaluationPartition,
    EvaluationSample,
    create_subject_independent_partition,
)
from eon_ers.evaluation.metrics import (
    compute_calibration_metrics,
    compute_classification_metrics,
)
from eon_ers.evaluation.proof import (
    EvaluationExecutionProof,
    SigningKeyPair,
    TrustedKeyRegistry,
)
from eon_ers.exceptions import ERSModelIntegrityError, ERSPrivacyConsentError
from eon_ers.facial.adapters import DeterministicTestFacialAdapter
from eon_ers.facial.pipeline import FacialPipeline
from eon_ers.live.dashboard import get_dashboard_html
from eon_ers.live.manager import LiveSessionManager
from eon_ers.metrics.evaluation import ModelEvaluationFramework
from eon_ers.models.loader import ModelLoader
from eon_ers.models.manifest import ModelManifest
from eon_ers.models.validation_record import ModelValidationRecord
from eon_ers.speech.adapters import DeterministicTestSpeechAdapter
from eon_ers.speech.pipeline import SpeechPipeline
from eon_ers.types import Modality
from PIL import Image


def _make_sample_jpeg_bytes() -> bytes:
    img = Image.new("RGB", (96, 96), color=(180, 160, 140))
    arr = np.array(img)
    arr[25:40, 25:40] = (30, 30, 30)
    arr[25:40, 56:71] = (30, 30, 30)
    buf = io.BytesIO()
    Image.fromarray(arr).save(buf, format="JPEG")
    return buf.getvalue()


# -----------------------------------------------------------------------------
# 1. CRYPTOGRAPHIC KEY ROTATION, ALGORITHM CONFUSION & MALFORMED KEY TESTS
# -----------------------------------------------------------------------------


def test_ed25519_key_rotation_algorithm_confusion_and_malformed_keys(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify key rotation, explicit revocation, algorithm confusion checks, and malformed key rejection."""
    registry = TrustedKeyRegistry()
    k1 = SigningKeyPair.generate("key-v1")
    k2 = SigningKeyPair.generate("key-v2")
    registry.register_keypair(k1)

    art_sha = hashlib.sha256(b"model artifact v1").hexdigest().lower()
    ds_sha = hashlib.sha256(b"dataset archive v1").hexdigest().lower()

    proof_v1 = EvaluationExecutionProof.generate_proof(
        model_id="m1",
        artifact_sha256=art_sha,
        dataset_archive_sha256=ds_sha,
        dataset_name="AffectNet_Holdout",
        dataset_provenance="Academic MIT",
        subject_count=5,
        sample_count=20,
        signing_key=k1,
    )
    assert proof_v1.verify(art_sha, key_registry=registry) is True

    # Rotate k1 -> k2 (revokes k1)
    registry.rotate_key("key-v1", "key-v2", k2, revoke_old=True)
    assert registry.is_trusted("key-v2") is True
    assert registry.is_trusted("key-v1") is False
    assert registry.is_revoked("key-v1") is True

    # Old proof rejected with explicit revoked reason
    ok_old, msg_old = proof_v1.verify_detailed(art_sha, key_registry=registry)
    assert ok_old is False
    assert "revoked" in msg_old.lower()

    # Re-registering a revoked key_id must fail
    with pytest.raises(ValueError, match="revoked"):
        registry.register_keypair(k1)

    # Proof signed with new key succeeds
    proof_v2 = EvaluationExecutionProof.generate_proof(
        model_id="m1",
        artifact_sha256=art_sha,
        dataset_archive_sha256=ds_sha,
        dataset_name="AffectNet_Holdout",
        dataset_provenance="Academic MIT",
        subject_count=5,
        sample_count=20,
        signing_key=k2,
    )
    assert proof_v2.verify(art_sha, key_registry=registry) is True

    # Algorithm confusion via model_construct must be rejected even with valid key_id
    confused = EvaluationExecutionProof.model_construct(
        **{**proof_v2.model_dump(), "signature_algorithm": "HS256"}
    )
    ok_alg, msg_alg = confused.verify_detailed(art_sha, key_registry=registry)
    assert ok_alg is False
    assert "algorithm confusion" in msg_alg.lower()

    # Reject non-Ed25519 (RSA) public key
    rsa_priv = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    rsa_pub_pem = rsa_priv.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    with pytest.raises(ValueError, match="not an Ed25519"):
        registry.register_public_key_pem("rsa-key", rsa_pub_pem)

    # Reject malformed/empty PEM public & private keys
    with pytest.raises(ValueError, match="empty"):
        registry.register_public_key_pem("empty", b"   ")
    with pytest.raises(Exception):
        registry.register_public_key_pem("corrupt", b"not a pem key")

    empty_pem_file = tmp_path / "empty.pem"
    empty_pem_file.write_bytes(b"")
    with pytest.raises(ValueError, match="empty"):
        SigningKeyPair.from_pem_file("k", empty_pem_file)
    with pytest.raises(FileNotFoundError):
        SigningKeyPair.from_pem_file("k", tmp_path / "missing.pem")

    # Partial env configuration must fail explicitly
    monkeypatch.setenv("EON_ERS_SIGNING_KEY_ID", "env-k")
    monkeypatch.delenv("EON_ERS_SIGNING_PRIVATE_KEY_PEM", raising=False)
    monkeypatch.delenv("EON_ERS_SIGNING_PRIVATE_KEY_PATH", raising=False)
    with pytest.raises(ValueError, match="incomplete"):
        SigningKeyPair.from_env()


# -----------------------------------------------------------------------------
# 2. DATASET SAFE EXTRACTION, TRAVERSAL, BOMB PROTECTION & DUPLICATES
# -----------------------------------------------------------------------------


def test_safe_archive_extraction_blocks_traversal_symlinks_and_bombs(tmp_path: Path) -> None:
    """DatasetMetadata.safe_extract_archive must extract valid archives and reject unsafe ones."""
    # 1. Valid ZIP archive
    good_zip = tmp_path / "good.zip"
    with zipfile.ZipFile(good_zip, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("labels/manifest.csv", "sample_id,subject_id,label\ns1,sub1,neutral\n")
    good_sha = hashlib.sha256(good_zip.read_bytes()).hexdigest().lower()
    meta = DatasetMetadata(
        name="SafeDS", source="OVIC", version="1.0", license="MIT", checksum=good_sha
    )
    ok_zip, msg_zip, audit_zip = meta.safe_extract_archive(good_zip, tmp_path / "out_good")
    assert ok_zip is True
    assert audit_zip["extracted_files"] == 1
    assert (tmp_path / "out_good" / "labels" / "manifest.csv").is_file()

    # 2. Zip-bomb protection (compression ratio & uncompressed limits)
    bomb_zip = tmp_path / "bomb.zip"
    with zipfile.ZipFile(bomb_zip, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("big.txt", b"A" * 500_000)
    bomb_sha = hashlib.sha256(bomb_zip.read_bytes()).hexdigest().lower()
    meta_bomb = meta.model_copy(update={"checksum": bomb_sha})
    ok_bomb, msg_bomb, _ = meta_bomb.safe_extract_archive(
        bomb_zip, tmp_path / "out_bomb", max_compression_ratio=10.0
    )
    assert ok_bomb is False
    assert "bomb" in msg_bomb.lower() or "ratio" in msg_bomb.lower()

    # 3. Path traversal rejection in ZIP
    trav_zip = tmp_path / "traversal.zip"
    with zipfile.ZipFile(trav_zip, "w") as zf:
        zf.writestr("../../outside.txt", "pwned")
    trav_sha = hashlib.sha256(trav_zip.read_bytes()).hexdigest().lower()
    meta_trav = meta.model_copy(update={"checksum": trav_sha})
    ok_trav, msg_trav, _ = meta_trav.safe_extract_archive(trav_zip, tmp_path / "out_trav")
    assert ok_trav is False
    assert "traversal" in msg_trav.lower()
    assert not (tmp_path / "outside.txt").exists()

    # 4. Symlink rejection in TAR
    sym_tar = tmp_path / "symlink.tar.gz"
    with tarfile.open(sym_tar, "w:gz") as tf:
        ti = tarfile.TarInfo("evil_link")
        ti.type = tarfile.SYMTYPE
        ti.linkname = "/etc/passwd"
        tf.addfile(ti)
    sym_sha = hashlib.sha256(sym_tar.read_bytes()).hexdigest().lower()
    meta_sym = meta.model_copy(update={"checksum": sym_sha})
    ok_sym, msg_sym, _ = meta_sym.safe_extract_archive(sym_tar, tmp_path / "out_sym")
    assert ok_sym is False
    assert "link" in msg_sym.lower()

    # 5. Unsupported archive extension rejected
    bad_ext = tmp_path / "archive.rar"
    bad_ext.write_bytes(b"rar payload")
    bad_ext_sha = hashlib.sha256(b"rar payload").hexdigest().lower()
    meta_bad_ext = meta.model_copy(update={"checksum": bad_ext_sha})
    ok_ext, msg_ext, _ = meta_bad_ext.safe_extract_archive(bad_ext, tmp_path / "out_ext")
    assert ok_ext is False
    assert "unsupported" in msg_ext.lower()


def test_duplicate_and_malformed_samples_and_manifests_rejected(tmp_path: Path) -> None:
    """Dataset partitioning and manifest validation must reject duplicate or blank sample IDs."""
    with pytest.raises(ValueError, match="cannot be blank"):
        EvaluationSample(sample_id="   ", subject_id="sub1", label="neutral")

    dup_samples = [
        EvaluationSample(sample_id="dup-1", subject_id="sub1", label="neutral"),
        EvaluationSample(sample_id="dup-1", subject_id="sub2", label="happiness"),
        EvaluationSample(sample_id="s3", subject_id="sub3", label="anger"),
    ]
    with pytest.raises(ValueError, match="Duplicate sample_id"):
        create_subject_independent_partition(dup_samples)

    with pytest.raises(ValueError, match="Duplicate sample_id"):
        EvaluationPartition(
            train_samples=[EvaluationSample(sample_id="dup", subject_id="s1", label="neutral")],
            val_samples=[EvaluationSample(sample_id="dup", subject_id="s2", label="neutral")],
            test_samples=[EvaluationSample(sample_id="u3", subject_id="s3", label="neutral")],
        )

    dup_csv = tmp_path / "dup.csv"
    dup_csv.write_text(
        "sample_id,subject_id,label\ns1,a1,neutral\ns1,a2,happiness\n", encoding="utf-8"
    )
    csv_sha = hashlib.sha256(dup_csv.read_bytes()).hexdigest().lower()
    meta = DatasetMetadata(
        name="DupDS",
        source="OVIC",
        version="1.0",
        license="MIT",
        manifest_checksum=csv_sha,
    )
    ok_man, msg_man, _ = meta.verify_manifest(dup_csv)
    assert ok_man is False
    assert "duplicate sample_id" in msg_man.lower()


# -----------------------------------------------------------------------------
# 3. MODEL COMPATIBILITY (MODALITY, FRAMEWORK, VERSION) & BINDING TESTS
# -----------------------------------------------------------------------------


def test_model_loader_rejects_incompatible_modality_framework_and_version(tmp_path: Path) -> None:
    """ModelLoader must enforce framework, modality, and major semantic version compatibility."""
    facial_onnx = Path("packages/ers/models/facial_emotion_model.onnx")
    if not facial_onnx.is_file():
        pytest.skip("Baseline facial model not found.")
    real_sha = hashlib.sha256(facial_onnx.read_bytes()).hexdigest().lower()

    base_kw = dict(
        model_id="compat-test",
        name="Compat Model",
        version="1.0.0",
        modality=Modality.FACIAL,
        framework="onnx",
        artifact_path=str(facial_onnx),
        sha256_checksum=real_sha,
        license="MIT",
        source="OVIC",
        input_specification={"name": "input_image", "shape": [1, 1, 64, 64], "dtype": "float32"},
        output_specification={
            "name": "logits",
            "shape": [1, 7],
            "classes": ["neutral", "happiness", "sadness", "anger", "fear", "surprise", "disgust"],
        },
    )

    # 1. Wrong modality (manifest says speech, loader expects facial)
    wrong_mod = ModelManifest(**{**base_kw, "modality": Modality.SPEECH})  # type: ignore[arg-type]
    with pytest.raises(ERSModelIntegrityError, match="Incompatible model modality"):
        ModelLoader.load_onnx_session(wrong_mod, expected_modality=Modality.FACIAL)

    # 2. Wrong framework
    wrong_fw = ModelManifest(**{**base_kw, "framework": "openvino"})  # type: ignore[arg-type]
    with pytest.raises(ERSModelIntegrityError, match="Incompatible model framework"):
        ModelLoader.load_onnx_session(wrong_fw, expected_modality=Modality.FACIAL)

    # 3. Incompatible major version
    wrong_ver = ModelManifest(**{**base_kw, "version": "2.0.0"})  # type: ignore[arg-type]
    with pytest.raises(ERSModelIntegrityError, match="Incompatible model major version"):
        ModelLoader.load_onnx_session(
            wrong_ver, expected_modality=Modality.FACIAL, supported_major_versions={1}
        )

    # 4. ModelValidationRecord rejects placeholder checksums in verify_artifact_binding
    dummy_file = tmp_path / "empty_hash.onnx"
    dummy_file.write_bytes(b"some weights")
    rec = ModelValidationRecord(
        record_id="val-1",
        model_id="m",
        model_version="1.0.0",
        artifact_sha256="0" * 64,
        is_validated=False,
        training_dataset="none",
        dataset_license="MIT",
        label_mapping=["neutral"],
        evaluation_dataset="ds",
        evaluation_split="test",
        evaluation_script="test",
        evaluation_metrics={"accuracy": 0.0},
        evaluator="test",
        validation_timestamp="2026-11-25T00:00:00Z",
    )
    assert rec.verify_artifact_binding(str(dummy_file)) is False


# -----------------------------------------------------------------------------
# 4. LIVE SESSION CONSENT ISOLATION, ENGINE SCRUBBING & MULTIMODAL METADATA
# -----------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_live_manager_requires_caller_consent_and_engine_preserves_multimodal_state() -> None:
    """LiveSessionManager must never bypass consent verification by reading cached secrets."""
    engine = ERSEngine(ERSConfig(require_explicit_consent=True))
    await engine.start()
    try:
        # Inject deterministic validated pipelines to test ERSEngine.process_multimodal propagation
        engine._facial_pipeline = FacialPipeline(
            engine.config, model_adapter=DeterministicTestFacialAdapter()
        )
        engine._speech_pipeline = SpeechPipeline(
            engine.config, model_adapter=DeterministicTestSpeechAdapter()
        )
        manager = LiveSessionManager(engine)

        session_id = "victim-session"
        secret_ref = "super-secret-consent-token-999"
        manager.register_session_consent(session_id, secret_ref)

        # Verify raw secret is NOT stored in ConsentManager or LiveSessionManager memory
        assert engine.consent_mgr._consents[session_id] != secret_ref
        assert "consent_reference" not in manager._active_sessions[session_id]

        face_b64 = base64.b64encode(_make_sample_jpeg_bytes()).decode("ascii")

        # 1. Calling process_frame WITHOUT consent_reference MUST be rejected (no cached bypass!)
        unauth_res = await manager.process_frame(session_id, face_b64, consent_reference=None)
        assert unauth_res["status"] == "consent_rejected"

        unauth_multi = await manager.process_multimodal_live(
            session_id=session_id, image_base64=face_b64, consent_reference=None
        )
        assert unauth_multi["status"] == "consent_rejected"

        # 2. ERSEngine scrubs media buffers even when consent validation raises
        bad_inp = ERSInput(
            session_id=session_id,
            modality=Modality.FACIAL,
            consent_reference="wrong-secret",
            image_payload=b"sensitive-raw-image-bytes",
        )
        with pytest.raises(ERSPrivacyConsentError):
            await engine.process(bad_inp)
        assert bad_inp.image_payload is None

        # 3. ERSEngine.process_multimodal propagates fusion validation metadata accurately
        good_face_inp = ERSInput(
            session_id=session_id,
            modality=Modality.FACIAL,
            consent_reference=secret_ref,
            image_payload=_make_sample_jpeg_bytes(),
        )
        fused = await engine.process_multimodal(good_face_inp, None)
        assert fused.is_validated is True
        assert fused.fusion_status == "facial_only_validated"
        assert fused.classification_eligible_modalities == ["facial"]
        assert fused.is_definitive_claim is False
    finally:
        await engine.stop()


def test_dashboard_html_matches_server_contracts() -> None:
    """Verify embedded dashboard HTML references match real backend REST & WS contracts."""
    html = get_dashboard_html()
    assert 'data.overall_qualification === "VALIDATED"' in html
    assert "m.modality || m.model_id" in html
    assert "image_base64: frameData" in html
    assert "consent_reference: state.consentReference" in html


# -----------------------------------------------------------------------------
# 5. ANALYTICAL EVALUATION & CALIBRATION NUMERICAL VERIFICATION TESTS
# -----------------------------------------------------------------------------


def test_exact_analytical_classification_and_calibration_metrics() -> None:
    """Verify confusion matrix, macro F1, balanced accuracy, Brier score, and ECE (including p=0 bin)."""
    labels = ["neutral", "happiness", "sadness"]
    # Ground truth: [N, H, S, H]
    y_true = ["neutral", "happiness", "sadness", "happiness"]
    # Preds:        [N, N, S, H]
    # CM: N: TP=1,FP=1,FN=0 (P=0.5, R=1.0, F1=2/3)
    #     H: TP=1,FP=0,FN=1 (P=1.0, R=0.5, F1=2/3)
    #     S: TP=1,FP=0,FN=0 (P=1.0, R=1.0, F1=1.0)
    y_pred = ["neutral", "neutral", "sadness", "happiness"]
    macro, per_class, cm = compute_classification_metrics(y_true, y_pred, labels)

    assert cm == [[1, 0, 0], [1, 1, 0], [0, 0, 1]]
    assert macro["accuracy"] == 0.75
    assert macro["balanced_accuracy"] == round((1.0 + 0.5 + 1.0) / 3.0, 4)
    assert macro["macro_f1"] == round((2.0 / 3.0 + 2.0 / 3.0 + 1.0) / 3.0, 4)
    assert per_class["neutral"]["precision"] == 0.5
    assert per_class["happiness"]["recall"] == 0.5

    # Include 0.0 confidence sample (tests b=0 inclusive lower bound in ECE!)
    probs = [
        {"neutral": 0.8, "happiness": 0.2, "sadness": 0.0},
        {"neutral": 0.0, "happiness": 1.0, "sadness": 0.0},
    ]
    calib = compute_calibration_metrics(["neutral", "happiness"], probs, labels, n_bins=10)
    # Brier: sample 0 = (0.8-1)^2 + 0.2^2 = 0.08; sample 1 = 0.0 -> mean = 0.04
    assert calib["brier_score"] == 0.04
    # ECE: bin (0.7,0.8]: |1 - 0.8| * 0.5 = 0.1; bin (0.9,1.0]: |1 - 1.0| * 0.5 = 0.0 -> 0.1
    assert calib["ece"] == 0.1

    # Verify ModelEvaluationFramework handles all-present classes & b=0 zero-confidence bin cleanly
    fw = ModelEvaluationFramework.evaluate(
        ["neutral", "happiness"], ["neutral", "happiness"], probs, classes=["neutral", "happiness"]
    )
    assert fw["accuracy"] == 1.0
    assert fw["balanced_accuracy"] == 1.0
    assert fw["brier_score"] == 0.04
    assert fw["expected_calibration_error"] == 0.1

    # Zero confidence sample in b=0 bin (confidence == 0.0 -> ECE |1.0 - 0.0| = 1.0)
    fw_zero_conf = ModelEvaluationFramework.evaluate(
        ["neutral"],
        ["neutral"],
        [{"neutral": 0.0, "happiness": 0.0}],
        classes=["neutral", "happiness"],
    )
    assert fw_zero_conf["expected_calibration_error"] == 1.0
