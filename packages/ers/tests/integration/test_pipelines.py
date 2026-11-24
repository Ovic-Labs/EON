"""End-to-end integration tests for ERS pipelines and evaluation framework."""

import io
import wave

import numpy as np
import pytest
from eon_ers.config import ERSConfig
from eon_ers.contracts import ERSInput
from eon_ers.engine import ERSEngine
from eon_ers.facial.adapters import DeterministicTestFacialAdapter
from eon_ers.facial.pipeline import FacialPipeline
from eon_ers.metrics.evaluation import ModelEvaluationFramework
from eon_ers.types import DeviceType, Modality, ObservationStatus
from PIL import Image


def make_test_face() -> bytes:
    arr = np.random.randint(60, 220, size=(96, 96, 3), dtype=np.uint8)
    img = Image.fromarray(arr)
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def make_test_speech() -> bytes:
    sr = 16000
    t = np.linspace(0, 1.0, sr, endpoint=False)
    audio = 0.3 * np.sin(2 * np.pi * 180 * t)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes((audio * 32767).astype(np.int16).tobytes())
    return buf.getvalue()


@pytest.mark.asyncio
async def test_end_to_end_real_onnx_pipelines() -> None:
    """AC-ERS-01: End-to-end execution of real ONNX models on CPU."""
    config = ERSConfig(
        device=DeviceType.CPU,
        facial_model_path="packages/ers/models/facial_emotion_model.onnx",
        speech_model_path="packages/ers/models/speech_emotion_model.onnx",
    )
    async with ERSEngine(config) as engine:
        # 1. Facial execution
        face_inp = ERSInput(
            session_id="integ-session-01",
            modality=Modality.FACIAL,
            consent_reference="token-2026",
            image_payload=make_test_face(),
        )
        face_obs = await engine.process_facial(face_inp)
        assert face_obs.status in (ObservationStatus.OK, ObservationStatus.INSUFFICIENT_EVIDENCE)
        assert face_obs.model_id == "ers-facial-onnx-cpu-v1"
        assert face_obs.confidence > 0.0
        assert face_obs.is_definitive_claim is False
        assert face_inp.image_payload is None  # Payload scrubbed

        # 2. Speech execution
        speech_inp = ERSInput(
            session_id="integ-session-01",
            modality=Modality.SPEECH,
            consent_reference="token-2026",
            audio_payload=make_test_speech(),
            sample_rate=16000,
        )
        speech_obs = await engine.process_speech(speech_inp)
        assert speech_obs.status == ObservationStatus.OK
        assert speech_obs.model_id == "ers-speech-onnx-cpu-v1"
        assert speech_obs.confidence > 0.0
        assert speech_obs.is_definitive_claim is False
        assert speech_inp.audio_payload is None  # Payload scrubbed

        # 3. Multimodal fusion
        face_inp2 = ERSInput(
            session_id="integ-session-01",
            modality=Modality.FACIAL,
            consent_reference="token-2026",
            image_payload=make_test_face(),
        )
        speech_inp2 = ERSInput(
            session_id="integ-session-01",
            modality=Modality.SPEECH,
            consent_reference="token-2026",
            audio_payload=make_test_speech(),
            sample_rate=16000,
        )
        fused = await engine.process_multimodal(face_inp2, speech_inp2)
        assert fused.confidence > 0.0
        assert fused.dominant_estimate in fused.fused_probabilities
        assert fused.is_definitive_claim is False


def test_missing_model_adapter_behavior() -> None:
    """AC-ERS-02: Missing model behavior without fabricating emotions."""
    config = ERSConfig()
    missing_adapter = DeterministicTestFacialAdapter(simulate_unavailable=True)
    pipeline = FacialPipeline(config, model_adapter=missing_adapter)

    inp = ERSInput(
        session_id="sess-missing",
        modality=Modality.FACIAL,
        consent_reference="token",
        image_payload=make_test_face(),
    )
    obs = pipeline.process(inp)
    assert obs.status == ObservationStatus.MODEL_UNAVAILABLE
    assert obs.confidence == 0.0
    assert obs.uncertainty == 1.0
    assert any("unavailable" in lim.lower() for lim in obs.limitations)


@pytest.mark.asyncio
async def test_multimodal_missing_modality_fallback() -> None:
    """AC-ERS-03: Graceful fallback when one modality is absent."""
    config = ERSConfig(
        facial_model_path="packages/ers/models/facial_emotion_model.onnx",
        speech_model_path="packages/ers/models/speech_emotion_model.onnx",
    )
    async with ERSEngine(config) as engine:
        face_inp = ERSInput(
            session_id="sess-single",
            modality=Modality.FACIAL,
            consent_reference="token",
            image_payload=make_test_face(),
        )
        # Speech is None
        fused = await engine.process_multimodal(face_inp, None)
        assert fused.facial_observation is not None
        assert fused.speech_observation is None
        assert Modality.SPEECH in fused.missing_modalities
        assert fused.modality_weights["facial"] == 1.0
        assert fused.modality_weights["speech"] == 0.0


def test_model_evaluation_framework() -> None:
    """AC-ERS-04: Model evaluation metrics computation (F1, Brier, ECE)."""
    y_true = ["neutral", "happiness", "anger", "sadness", "neutral"]
    y_pred = ["neutral", "happiness", "anger", "neutral", "neutral"]
    probs = [
        {"neutral": 0.8, "happiness": 0.1, "anger": 0.05, "sadness": 0.05},
        {"neutral": 0.1, "happiness": 0.85, "anger": 0.02, "sadness": 0.03},
        {"neutral": 0.1, "happiness": 0.1, "anger": 0.75, "sadness": 0.05},
        {"neutral": 0.6, "happiness": 0.1, "anger": 0.1, "sadness": 0.2},
        {"neutral": 0.9, "happiness": 0.05, "anger": 0.02, "sadness": 0.03},
    ]

    metrics = ModelEvaluationFramework.evaluate(y_true, y_pred, probs)
    assert metrics["accuracy"] == 0.8
    assert metrics["macro_f1"] > 0.6
    assert metrics["brier_score"] >= 0.0
    assert metrics["expected_calibration_error"] >= 0.0
    assert "neutral" in metrics["per_class"]
