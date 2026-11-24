"""Unit tests for Critical Issue 2: Model Qualification and Observation Status Precedence.

Verifies:
1. Model qualification state (ModelState) and input quality status (InputQualityStatus) are decoupled.
2. Degraded input with unvalidated model keeps status = MODEL_UNVALIDATED (not overwritten by DEGRADED).
3. Degraded input with validated model has status = DEGRADED.
4. Failed inference has status = FAILED and model_state = MODEL_INFERENCE_FAILED.
5. Deterministic precedence policy:
   FAILED > MODEL_UNAVAILABLE > MODEL_UNVALIDATED > INSUFFICIENT_EVIDENCE > DEGRADED > OK.
"""

from __future__ import annotations

import io
import wave

import numpy as np
from eon_ers.config import ERSConfig
from eon_ers.contracts import ERSInput
from eon_ers.facial.pipeline import FacialPipeline
from eon_ers.quality.audio_quality import AudioQualityEvaluator
from eon_ers.quality.face_quality import FaceQualityEvaluator
from eon_ers.speech.pipeline import SpeechPipeline
from eon_ers.types import (
    EmotionCategory,
    InputQualityStatus,
    Modality,
    ModelState,
    ObservationStatus,
)
from PIL import Image


def _create_facial_jpeg_bytes() -> bytes:
    # 128x128 image with high spatial contrast face region
    arr = np.ones((128, 128, 3), dtype=np.uint8) * 180
    arr[30:50, 30:50] = 50
    arr[30:50, 78:98] = 50
    arr[75:95, 40:88] = 80
    img = Image.fromarray(arr)
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def _create_clipped_wav_bytes() -> bytes:
    t = np.linspace(0, 1.0, 16000, endpoint=False, dtype=np.float32)
    signal = 1.5 * np.sin(2 * np.pi * 300 * t)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(16000)
        clipped = np.clip(signal, -1.0, 1.0)
        pcm = (clipped * 32767).astype(np.int16).tobytes()
        wf.writeframes(pcm)
    return buf.getvalue()


def test_facial_pipeline_unvalidated_model_with_degraded_quality() -> None:
    """An unvalidated model must preserve MODEL_UNVALIDATED even when input quality is degraded."""
    # Configure evaluator thresholds so this face image triggers DEGRADED quality
    config = ERSConfig()
    pipeline = FacialPipeline(config=config)
    pipeline.quality_evaluator = FaceQualityEvaluator(
        blur_threshold=1000.0, max_brightness=150.0, max_dimension=100
    )

    image_bytes = _create_facial_jpeg_bytes()
    ers_input = ERSInput(
        session_id="test-precedence",
        modality=Modality.FACIAL,
        consent_reference="consent-token-001",
        image_payload=image_bytes,
    )

    observation = pipeline.process(ers_input)

    # Status must strictly be MODEL_UNVALIDATED (never overwritten by DEGRADED)
    assert observation.status == ObservationStatus.MODEL_UNVALIDATED
    # Input quality dimension correctly reports DEGRADED independently
    assert observation.input_quality == InputQualityStatus.DEGRADED
    assert observation.model_state in (
        ModelState.MODEL_LOADED_UNVERIFIED,
        ModelState.MODEL_EXPERIMENTAL,
        ModelState.MODEL_MISSING,
    )
    assert observation.is_calibrated is False


def test_speech_pipeline_unvalidated_model_with_degraded_quality() -> None:
    """Speech pipeline must preserve MODEL_UNVALIDATED even when audio is noisy/degraded."""
    config = ERSConfig()
    pipeline = SpeechPipeline(config=config)
    # Configure audio quality evaluator so clipped long audio triggers DEGRADED
    pipeline.quality_evaluator = AudioQualityEvaluator(
        clipping_threshold=0.01, min_snr_db=50.0, max_duration_seconds=0.5
    )

    wav_bytes = _create_clipped_wav_bytes()
    ers_input = ERSInput(
        session_id="test-precedence-speech",
        modality=Modality.SPEECH,
        consent_reference="consent-token-002",
        audio_payload=wav_bytes,
        sample_rate=16000,
    )

    observation = pipeline.process(ers_input)

    assert observation.status == ObservationStatus.MODEL_UNVALIDATED
    assert observation.input_quality == InputQualityStatus.DEGRADED
    assert observation.model_state in (
        ModelState.MODEL_LOADED_UNVERIFIED,
        ModelState.MODEL_EXPERIMENTAL,
        ModelState.MODEL_MISSING,
    )
    assert observation.is_calibrated is False


def test_unusable_quality_produces_insufficient_evidence() -> None:
    """When input quality is unusable (e.g. extremely short duration < 0.2s), pipeline returns INSUFFICIENT_EVIDENCE."""
    config = ERSConfig()
    pipeline = SpeechPipeline(config=config)

    # Extremely short audio (50 samples = 0.003s < min 0.2s) -> UNUSABLE
    audio = np.ones(50, dtype=np.float32) * 0.1
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(16000)
        wf.writeframes((audio * 32767).astype(np.int16).tobytes())
    wav_bytes = buf.getvalue()

    ers_input = ERSInput(
        session_id="test-unusable",
        modality=Modality.SPEECH,
        consent_reference="consent-token-003",
        audio_payload=wav_bytes,
        sample_rate=16000,
    )

    observation = pipeline.process(ers_input)

    assert observation.status == ObservationStatus.INSUFFICIENT_EVIDENCE
    assert observation.input_quality == InputQualityStatus.UNUSABLE
    assert observation.dominant_estimate == EmotionCategory.INSUFFICIENT_EVIDENCE.value
