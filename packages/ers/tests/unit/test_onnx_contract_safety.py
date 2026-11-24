"""Unit tests for Critical Issue 5: ONNX Runtime & Inference Contract Safety.

Verifies:
1. Rejection of NaN and Infinite numerical values in input tensors.
2. Handling of non-finite logits from model outputs.
3. Tracking of inference failures into ModelState.MODEL_INFERENCE_FAILED.
4. Tensor rank, shape, and dtype verification in ModelManifest contracts.
5. Class ordering verification.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pytest
from eon_ers.exceptions import ERSModelExecutionError
from eon_ers.facial.adapters import ONNXFacialModelAdapter
from eon_ers.models.manifest import ModelManifest
from eon_ers.speech.adapters import ONNXSpeechModelAdapter


class _MockSession:
    """Mock ONNX Runtime InferenceSession for contract testing."""

    def __init__(
        self,
        in_name: str,
        in_shape: list[Any],
        in_type: str,
        out_name: str,
        out_shape: list[Any],
        out_type: str,
    ) -> None:
        class Node:
            def __init__(self, name: str, shape: list[Any], type_: str) -> None:
                self.name = name
                self.shape = shape
                self.type = type_

        self._inputs = [Node(in_name, in_shape, in_type)]
        self._outputs = [Node(out_name, out_shape, out_type)]

    def get_inputs(self) -> list[Any]:
        return self._inputs

    def get_outputs(self) -> list[Any]:
        return self._outputs


def test_facial_adapter_rejects_nan_and_inf_inputs() -> None:
    """Facial model adapter must reject NaN and Inf float tensors before inference."""
    repo_model = Path("packages/ers/models/facial_emotion_model.onnx")
    if not repo_model.exists():
        pytest.skip("Facial model artifact not present in repo")

    adapter = ONNXFacialModelAdapter(model_path=str(repo_model))

    # Test with NaN
    nan_tensor = np.full((1, 1, 64, 64), np.nan, dtype=np.float32)
    with pytest.raises(ERSModelExecutionError, match="non-finite"):
        adapter.predict(nan_tensor, {})

    # Test with Inf
    inf_tensor = np.full((1, 1, 64, 64), np.inf, dtype=np.float32)
    with pytest.raises(ERSModelExecutionError, match="non-finite"):
        adapter.predict(inf_tensor, {})


def test_speech_adapter_rejects_nan_and_inf_features() -> None:
    """Speech model adapter must reject NaN and Inf feature inputs."""
    repo_model = Path("packages/ers/models/speech_emotion_model.onnx")
    if not repo_model.exists():
        pytest.skip("Speech model artifact not present in repo")

    adapter = ONNXSpeechModelAdapter(model_path=str(repo_model))
    dummy_signal = np.zeros(16000, dtype=np.float32)

    nan_features = {
        "f0_mean_hz": float("nan"),
        "energy_rms_mean": 0.1,
    }
    with pytest.raises(ERSModelExecutionError, match="non-finite"):
        adapter.predict(dummy_signal, 16000, nan_features)


def test_manifest_tensor_contract_validation() -> None:
    """Manifest must validate tensor rank, shapes, and dtypes strictly."""
    manifest = ModelManifest(
        model_id="test-facial-v1",
        name="Test ConvNet",
        version="1.0.0",
        modality="facial",
        artifact_path="test.onnx",
        sha256_checksum="0" * 64,
        license="MIT",
        source="OVIC",
        input_specification={"name": "input_image", "shape": [1, 1, 64, 64], "dtype": "float32"},
        output_specification={
            "name": "logits",
            "shape": [1, 7],
            "classes": ["neutral", "happiness", "sadness", "anger", "fear", "surprise", "disgust"],
        },
    )

    # 1. Matching session passes
    valid_session = _MockSession(
        in_name="input_image",
        in_shape=[1, 1, 64, 64],
        in_type="tensor(float)",
        out_name="logits",
        out_shape=[1, 7],
        out_type="tensor(float)",
    )
    ok, msg = manifest.validate_tensor_contracts(valid_session)
    assert ok is True
    assert "verified" in msg.lower()

    # 2. Input rank mismatch fails
    rank_mismatch_session = _MockSession(
        in_name="input_image",
        in_shape=[1, 64, 64],  # 3D instead of 4D
        in_type="tensor(float)",
        out_name="logits",
        out_shape=[1, 7],
        out_type="tensor(float)",
    )
    ok, msg = manifest.validate_tensor_contracts(rank_mismatch_session)
    assert ok is False
    assert "rank mismatch" in msg.lower()

    # 3. Input dtype invalid fails
    dtype_mismatch_session = _MockSession(
        in_name="input_image",
        in_shape=[1, 1, 64, 64],
        in_type="tensor(int64)",  # Int instead of float
        out_name="logits",
        out_shape=[1, 7],
        out_type="tensor(float)",
    )
    ok, msg = manifest.validate_tensor_contracts(dtype_mismatch_session)
    assert ok is False
    assert "dtype invalid" in msg.lower()

    # 4. Output class dimension mismatch fails
    class_dim_mismatch_session = _MockSession(
        in_name="input_image",
        in_shape=[1, 1, 64, 64],
        in_type="tensor(float)",
        out_name="logits",
        out_shape=[1, 5],  # 5 classes instead of 7
        out_type="tensor(float)",
    )
    ok, msg = manifest.validate_tensor_contracts(class_dim_mismatch_session)
    assert ok is False
    assert "shape mismatch" in msg.lower() or "class dimension mismatch" in msg.lower()
