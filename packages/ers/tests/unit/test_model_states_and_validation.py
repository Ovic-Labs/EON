"""Unit tests for Phase 3.1.3 Model State lifecycle and cryptographic validation records."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
from eon_ers.config import ERSConfig
from eon_ers.contracts import ERSInput
from eon_ers.facial.adapters import ONNXFacialModelAdapter
from eon_ers.facial.pipeline import FacialPipeline
from eon_ers.models.validation_record import ModelValidationRecord
from eon_ers.types import EmotionCategory, Modality, ModelState, ObservationStatus


def test_model_state_enum_completeness() -> None:
    """Verify all mandatory ModelState enum values are present."""
    expected_states = {
        "MODEL_MISSING",
        "MODEL_LOADING",
        "MODEL_LOADED_UNVERIFIED",
        "MODEL_LOADED_VALIDATED",
        "MODEL_UNAVAILABLE",
        "MODEL_INFERENCE_FAILED",
        "MODEL_EXPERIMENTAL",
    }
    actual_states = {s.name for s in ModelState}
    assert expected_states == actual_states


def test_model_validation_record_schema_and_binding(tmp_path: Path) -> None:
    """Verify ModelValidationRecord serialization and artifact checksum verification."""
    fake_artifact = tmp_path / "model.onnx"
    fake_artifact.write_bytes(b"dummy onnx weights binary content")

    import hashlib

    hasher = hashlib.sha256()
    hasher.update(b"dummy onnx weights binary content")
    correct_sha = hasher.hexdigest()

    record = ModelValidationRecord(
        record_id="VAL-test-001",
        model_id="test-model",
        model_version="1.0.0",
        artifact_sha256=correct_sha,
        is_validated=True,
        training_dataset="AffectNet-Cleaned",
        training_dataset_version="2.0",
        dataset_license="CC-BY-4.0",
        commercial_use_allowed=True,
        commercial_use_restrictions=[],
        preprocessing_specification={"shape": [1, 1, 64, 64]},
        label_mapping=["neutral", "happiness", "sadness"],
        evaluation_dataset="AffectNet-Test",
        evaluation_split="test",
        evaluation_script="eval_test.py",
        evaluation_script_version="1.0.0",
        evaluation_metrics={
            "accuracy": 0.85,
            "balanced_accuracy": 0.84,
            "macro_precision": 0.83,
            "macro_recall": 0.84,
            "macro_f1": 0.835,
        },
        evaluator="Dr. Test",
        validation_timestamp="2026-11-24T00:00:00Z",
    )

    # Valid binding
    assert record.verify_artifact_binding(str(fake_artifact)) is True

    # Tampered artifact fails verification
    fake_artifact.write_bytes(b"tampered content")
    assert record.verify_artifact_binding(str(fake_artifact)) is False

    # Persist and reload
    save_path = tmp_path / "model.validation.json"
    record.save_to_file(save_path)
    loaded = ModelValidationRecord.load_from_file(save_path)
    assert loaded.record_id == record.record_id
    assert loaded.artifact_sha256 == record.artifact_sha256
    assert loaded.is_validated is True


def test_adapter_state_transitions(tmp_path: Path) -> None:
    """Verify adapter transitions across missing, unverified, and validated states."""
    # 1. Missing model
    missing_adapter = ONNXFacialModelAdapter(model_path=str(tmp_path / "non_existent.onnx"))
    assert missing_adapter.model_state == ModelState.MODEL_MISSING
    assert missing_adapter.is_available is False
    assert missing_adapter.is_validated is False

    # 2. Real repo baseline model without validation record claiming validated
    repo_facial_onnx = Path("packages/ers/models/facial_emotion_model.onnx")
    if repo_facial_onnx.exists():
        adapter = ONNXFacialModelAdapter(model_path=str(repo_facial_onnx))
        assert adapter.is_available is True
        # Since baseline validation record has is_validated = False:
        assert adapter.is_validated is False
        assert adapter.model_state == ModelState.MODEL_LOADED_UNVERIFIED


def test_unvalidated_model_suppresses_predictions(tmp_path: Path) -> None:
    """Verify that unvalidated baseline models suppress discrete categorization."""
    repo_facial_onnx = Path("packages/ers/models/facial_emotion_model.onnx")
    if not repo_facial_onnx.exists():
        pytest.skip("Facial ONNX baseline not present.")

    config = ERSConfig(facial_model_path=str(repo_facial_onnx))
    pipeline = FacialPipeline(config)

    # Create dummy face image
    import io

    from PIL import Image

    arr = np.random.randint(50, 200, size=(128, 128, 3), dtype=np.uint8)
    arr[30:50, 30:50] = 50
    arr[30:50, 78:98] = 50
    arr[75:95, 40:88] = 80
    img = Image.fromarray(arr)
    buf = io.BytesIO()
    img.save(buf, format="JPEG")

    inp = ERSInput(
        session_id="test-unval-suppress",
        modality=Modality.FACIAL,
        consent_reference="token-val",
        image_payload=buf.getvalue(),
    )
    obs = pipeline.process(inp)

    # Invariant: Must abstain as UNKNOWN or INSUFFICIENT_EVIDENCE because model is unvalidated
    assert obs.status == ObservationStatus.MODEL_UNVALIDATED
    assert obs.dominant_estimate in (
        EmotionCategory.UNKNOWN.value,
        EmotionCategory.INSUFFICIENT_EVIDENCE.value,
    )
    assert obs.confidence == 0.0
    assert obs.uncertainty == 1.0
    assert obs.is_validated is False
    assert obs.is_definitive_claim is False
    assert obs.model_state == ModelState.MODEL_LOADED_UNVERIFIED
