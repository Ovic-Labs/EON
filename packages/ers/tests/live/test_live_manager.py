"""Unit and integration tests for LiveSessionManager."""

from __future__ import annotations

import base64
import io
import wave

import numpy as np
import pytest
from eon_ers.config import ERSConfig
from eon_ers.engine import ERSEngine
from eon_ers.live.manager import LiveSessionManager
from eon_ers.types import Modality
from PIL import Image


def create_sample_face_b64() -> str:
    """Generate sample JPEG face base64 data URI."""
    img = Image.new("RGB", (128, 128), color=(200, 180, 160))
    arr = np.array(img)
    arr[30:45, 30:50] = (50, 50, 50)
    arr[30:45, 78:98] = (50, 50, 50)
    arr[75:90, 40:88] = (180, 60, 60)
    synth = Image.fromarray(arr)
    buf = io.BytesIO()
    synth.save(buf, format="JPEG")
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    return f"data:image/jpeg;base64,{b64}"


def create_sample_audio_b64() -> str:
    """Generate sample 16kHz sine wave audio base64 data URI."""
    sr = 16000
    duration = 0.5
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    audio = 0.3 * np.sin(2 * np.pi * 200 * t)
    audio_int16 = (audio * 32767).astype(np.int16)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(audio_int16.tobytes())
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    return f"data:audio/wav;base64,{b64}"


@pytest.fixture
async def live_manager() -> LiveSessionManager:
    """Fixture providing an initialized LiveSessionManager."""
    config = ERSConfig(
        enable_facial=True,
        enable_speech=True,
        enable_multimodal_fusion=True,
        facial_model_path="packages/ers/models/facial_emotion_model.onnx",
        speech_model_path="packages/ers/models/speech_emotion_model.onnx",
    )
    engine = ERSEngine(config)
    manager = LiveSessionManager(engine)
    await manager.initialize()
    yield manager
    await manager.shutdown()


@pytest.mark.asyncio
async def test_manager_lifecycle(live_manager: LiveSessionManager) -> None:
    """Test manager starts and shuts down cleanly."""
    assert live_manager.engine.is_running
    status = live_manager.get_health_status()
    assert status["status"] == "HEALTHY"
    assert status["core_integration_status"] == "NOT_CONNECTED"


@pytest.mark.asyncio
async def test_consent_management(live_manager: LiveSessionManager) -> None:
    """Test session consent registration, query, and revocation."""
    session_id = "test-session-consent-1"
    consent_ref = "valid-consent-token-xyz"

    assert not live_manager.has_consent(session_id)
    live_manager.register_session_consent(session_id, consent_ref)
    assert live_manager.has_consent(session_id)

    status = live_manager.get_session_consent_status(session_id)
    assert status["has_active_consent"] is True
    assert status["is_revoked"] is False
    assert status["masked_reference"] == "valid***xyz"

    live_manager.revoke_session_consent(session_id)
    assert not live_manager.has_consent(session_id)
    status_revoked = live_manager.get_session_consent_status(session_id)
    assert status_revoked["has_active_consent"] is False
    assert status_revoked["is_revoked"] is True


@pytest.mark.asyncio
async def test_process_frame_valid(live_manager: LiveSessionManager) -> None:
    """Test processing valid base64 image frame."""
    session_id = "test-frame-session"
    consent_ref = "token-face-1"
    live_manager.register_session_consent(session_id, consent_ref)

    face_b64 = create_sample_face_b64()
    result = await live_manager.process_frame(session_id, face_b64, consent_ref)

    assert result["status"] in ("ok", "insufficient_evidence", "model_unvalidated")
    assert result["modality"] == Modality.FACIAL.value
    assert "dominant_estimate" in result
    assert "emotion_probabilities" in result
    assert result["is_definitive_claim"] is False
    assert result["latency_ms"] > 0.0


@pytest.mark.asyncio
async def test_process_frame_invalid_base64(live_manager: LiveSessionManager) -> None:
    """Test processing corrupted or invalid base64 string returns error."""
    session_id = "test-corrupted-b64"
    consent_ref = "token-corr-1"
    live_manager.register_session_consent(session_id, consent_ref)

    result = await live_manager.process_frame(
        session_id, "data:image/jpeg;base64,not-valid-base64-content!@#$", consent_ref
    )
    assert result["status"] == "error"
    assert "Invalid image base64 payload" in result["error"]


@pytest.mark.asyncio
async def test_process_frame_empty_payload(live_manager: LiveSessionManager) -> None:
    """Test processing empty image base64 returns error gracefully."""
    session_id = "test-empty-b64"
    consent_ref = "token-empty-1"
    live_manager.register_session_consent(session_id, consent_ref)

    result = await live_manager.process_frame(session_id, "", consent_ref)
    assert result["status"] == "error"


@pytest.mark.asyncio
async def test_process_frame_unauthorized_consent(live_manager: LiveSessionManager) -> None:
    """Test processing frame without valid consent returns consent_rejected."""
    session_id = "unauth-session"
    face_b64 = create_sample_face_b64()

    result = await live_manager.process_frame(session_id, face_b64, "unregistered-token")
    assert result["status"] == "consent_rejected"
    assert "error" in result


@pytest.mark.asyncio
async def test_process_audio_valid(live_manager: LiveSessionManager) -> None:
    """Test processing valid base64 audio chunk."""
    session_id = "test-audio-session"
    consent_ref = "token-audio-1"
    live_manager.register_session_consent(session_id, consent_ref)

    audio_b64 = create_sample_audio_b64()
    result = await live_manager.process_audio(session_id, audio_b64, 16000, consent_ref)

    assert result["status"] in ("ok", "insufficient_evidence", "model_unvalidated")
    assert result["modality"] == Modality.SPEECH.value
    assert "dominant_estimate" in result
    assert result["is_definitive_claim"] is False
    assert result["latency_ms"] > 0.0


@pytest.mark.asyncio
async def test_process_audio_invalid_base64(live_manager: LiveSessionManager) -> None:
    """Test processing invalid audio base64 returns error."""
    session_id = "test-audio-inv"
    consent_ref = "token-audio-inv"
    live_manager.register_session_consent(session_id, consent_ref)

    result = await live_manager.process_audio(session_id, "corrupted-b64-chunk", 16000, consent_ref)
    assert result["status"] == "error"


@pytest.mark.asyncio
async def test_process_multimodal_live(live_manager: LiveSessionManager) -> None:
    """Test simultaneous facial and speech ingestion and fusion."""
    session_id = "test-multimodal-live"
    consent_ref = "token-multi-1"
    live_manager.register_session_consent(session_id, consent_ref)

    face_b64 = create_sample_face_b64()
    audio_b64 = create_sample_audio_b64()

    result = await live_manager.process_multimodal_live(
        session_id=session_id,
        image_base64=face_b64,
        audio_base64=audio_b64,
        sample_rate=16000,
        consent_reference=consent_ref,
    )

    assert result["dominant_estimate"] is not None
    assert result["is_definitive_claim"] is False
    assert "fused_probabilities" in result
    assert "modality_weights" in result
    assert result["latency_ms"] > 0.0
