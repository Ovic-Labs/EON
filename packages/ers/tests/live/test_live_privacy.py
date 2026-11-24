"""Privacy, consent lifecycle, and safety invariant tests for live streaming."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from eon_ers.config import ERSConfig
from eon_ers.engine import ERSEngine
from eon_ers.live.manager import LiveSessionManager

from .conftest import create_sample_audio_b64, create_sample_face_b64


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
async def test_instant_revocation_mid_stream(live_manager: LiveSessionManager) -> None:
    """Verify that revoking consent mid-stream immediately blocks further processing."""
    session_id = "stream-revocation-session"
    token = "stream-consent-token-456"
    live_manager.register_session_consent(session_id, token)

    face_b64 = create_sample_face_b64()

    # Process first 3 frames successfully
    for i in range(3):
        res = await live_manager.process_frame(session_id, face_b64, token)
        assert res["status"] in ("ok", "insufficient_evidence", "model_unvalidated")
        assert res["is_definitive_claim"] is False

    # Revoke consent mid-stream
    live_manager.revoke_session_consent(session_id)

    # Next 3 frames must be rejected
    for i in range(3):
        res = await live_manager.process_frame(session_id, face_b64, token)
        assert res["status"] == "consent_rejected"
        assert "error" in res


@pytest.mark.asyncio
async def test_concurrent_session_isolation(live_manager: LiveSessionManager) -> None:
    """Verify that multiple concurrent streaming sessions do not leak consent or state."""
    session_a = "session-user-alice"
    session_b = "session-user-bob"
    token_a = "token-alice-111"
    token_b = "token-bob-222"

    live_manager.register_session_consent(session_a, token_a)
    live_manager.register_session_consent(session_b, token_b)

    face_b64 = create_sample_face_b64()

    # Both process successfully
    res_a = await live_manager.process_frame(session_a, face_b64, token_a)
    res_b = await live_manager.process_frame(session_b, face_b64, token_b)
    assert res_a["status"] in ("ok", "insufficient_evidence", "model_unvalidated")
    assert res_b["status"] in ("ok", "insufficient_evidence", "model_unvalidated")

    # Revoke Alice's consent only
    live_manager.revoke_session_consent(session_a)

    # Alice is rejected, Bob continues unimpeded
    res_a2 = await live_manager.process_frame(session_a, face_b64, token_a)
    res_b2 = await live_manager.process_frame(session_b, face_b64, token_b)
    assert res_a2["status"] == "consent_rejected"
    assert res_b2["status"] in ("ok", "insufficient_evidence", "model_unvalidated")


@pytest.mark.asyncio
async def test_zero_disk_retention_during_streaming(live_manager: LiveSessionManager) -> None:
    """Verify that processing high-frequency live frames and audio persists zero files to disk."""
    session_id = "zero-disk-session"
    token = "zero-disk-token"
    live_manager.register_session_consent(session_id, token)

    face_b64 = create_sample_face_b64()
    audio_b64 = create_sample_audio_b64()

    repo_dir = Path(".")

    def count_media_files(directory: Path) -> int:
        count = 0
        extensions = {".jpg", ".jpeg", ".png", ".wav", ".pcm", ".raw"}
        try:
            for root, _, files in os.walk(directory):
                # Ignore model directory containing approved model weights
                if "models" in root:
                    continue
                for f in files:
                    if Path(f).suffix.lower() in extensions:
                        count += 1
        except Exception:
            pass
        return count

    repo_media_before = count_media_files(repo_dir)

    # Ingest 20 frames and 20 audio chunks
    for _ in range(20):
        await live_manager.process_frame(session_id, face_b64, token)
        await live_manager.process_audio(session_id, audio_b64, 16000, token)

    repo_media_after = count_media_files(repo_dir)

    # Invariant: No media files were created on disk
    assert repo_media_after == repo_media_before, "Raw media payload was leaked to disk!"


@pytest.mark.asyncio
async def test_actuator_motion_command_prohibition(live_manager: LiveSessionManager) -> None:
    """Verify that live sensory pipeline strictly forbids generating actuator motion commands."""
    session_id = "safety-actuator-session"
    token = "safety-actuator-token"
    live_manager.register_session_consent(session_id, token)

    face_b64 = create_sample_face_b64()
    audio_b64 = create_sample_audio_b64()

    res_face = await live_manager.process_frame(session_id, face_b64, token)
    res_audio = await live_manager.process_audio(session_id, audio_b64, 16000, token)
    res_multi = await live_manager.process_multimodal_live(
        session_id=session_id,
        image_base64=face_b64,
        audio_base64=audio_b64,
        sample_rate=16000,
        consent_reference=token,
    )

    forbidden_keys = {
        "motor_command",
        "actuator",
        "joint_velocity",
        "trajectory",
        "movement",
        "arm_pose",
        "wheel_speed",
    }

    for res in (res_face, res_audio, res_multi):
        found_forbidden = forbidden_keys.intersection(res.keys())
        assert not found_forbidden, (
            f"Actuator command detected in observation output: {found_forbidden}"
        )


@pytest.mark.asyncio
async def test_epistemic_modesty_invariants(live_manager: LiveSessionManager) -> None:
    """Verify that all live outputs enforce is_definitive_claim = False."""
    session_id = "epistemic-session"
    token = "epistemic-token"
    live_manager.register_session_consent(session_id, token)

    face_b64 = create_sample_face_b64()
    audio_b64 = create_sample_audio_b64()

    res_face = await live_manager.process_frame(session_id, face_b64, token)
    res_audio = await live_manager.process_audio(session_id, audio_b64, 16000, token)
    res_multi = await live_manager.process_multimodal_live(
        session_id=session_id,
        image_base64=face_b64,
        audio_base64=audio_b64,
        sample_rate=16000,
        consent_reference=token,
    )

    assert res_face["is_definitive_claim"] is False
    assert res_audio["is_definitive_claim"] is False
    assert res_multi["is_definitive_claim"] is False
