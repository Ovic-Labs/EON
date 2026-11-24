"""Security and failure isolation tests for ERS."""

import pytest
from eon_ers.config import ERSConfig
from eon_ers.contracts import ERSInput
from eon_ers.core.adapter import CoreEventBusAdapter
from eon_ers.engine import ERSEngine
from eon_ers.exceptions import ERSModelIntegrityError
from eon_ers.models.loader import ModelLoader
from eon_ers.models.manifest import ModelManifest
from eon_ers.types import Modality, ObservationStatus


@pytest.mark.asyncio
async def test_malformed_image_graceful_handling() -> None:
    config = ERSConfig()
    async with ERSEngine(config) as engine:
        engine.register_consent("session-sec-1", "sec-token")
        inp = ERSInput(
            session_id="session-sec-1",
            modality=Modality.FACIAL,
            consent_reference="sec-token",
            image_payload=b"\x00\xff\xaa\xbb\xcc\xdd" * 50,  # Corrupted non-image bytes
        )
        obs = await engine.process_facial(inp)
        assert obs.status == ObservationStatus.INSUFFICIENT_EVIDENCE
        assert obs.confidence == 0.0
        assert obs.is_definitive_claim is False
        assert any("decode failed" in r for r in obs.limitations)


@pytest.mark.asyncio
async def test_malformed_audio_graceful_handling() -> None:
    config = ERSConfig()
    async with ERSEngine(config) as engine:
        engine.register_consent("session-sec-2", "sec-token")
        inp = ERSInput(
            session_id="session-sec-2",
            modality=Modality.SPEECH,
            consent_reference="sec-token",
            audio_payload=b"RIFF\x00\x00\x00\x00WAVEfmt ",  # Incomplete truncated WAV header
            sample_rate=16000,
        )
        obs = await engine.process_speech(inp)
        assert obs.status == ObservationStatus.INSUFFICIENT_EVIDENCE
        assert obs.is_definitive_claim is False


def test_model_checksum_verification_mismatch_raises() -> None:
    manifest = ModelManifest(
        model_id="tampered-model",
        name="Tampered Model",
        version="1.0.0",
        modality=Modality.FACIAL,
        framework="onnx",
        artifact_path="packages/ers/models/facial_emotion_model.onnx",
        sha256_checksum="0" * 64,  # Intentionally falsified checksum
        license="UNVERIFIED",
        commercial_use_allowed=False,
        source="unit-test",
        input_specification={"name": "input_image", "shape": [1, 1, 64, 64], "dtype": "float32"},
        output_specification={"name": "logits", "shape": [1, 7], "classes": []},
    )

    with pytest.raises(ERSModelIntegrityError) as exc_info:
        ModelLoader.load_onnx_session(manifest)
    assert "SHA-256 digest mismatch" in str(exc_info.value)


def test_model_tensor_contract_mismatch_raises() -> None:
    # Use real checksum of facial model but bogus input shape specification
    manifest = ModelManifest(
        model_id="shape-mismatch-model",
        name="Shape Mismatch Model",
        version="1.0.0",
        modality=Modality.FACIAL,
        framework="onnx",
        artifact_path="packages/ers/models/facial_emotion_model.onnx",
        sha256_checksum="0e8955c5187b2b9f69f9638e005b09abdbb1412951024e535fdefef48cc7d81b",
        license="UNVERIFIED",
        commercial_use_allowed=False,
        source="unit-test",
        input_specification={"name": "input_image", "shape": [1, 1, 32, 32], "dtype": "float32"},
        output_specification={"name": "logits", "shape": [1, 7], "classes": []},
    )

    with pytest.raises(ERSModelIntegrityError) as exc_info:
        ModelLoader.load_onnx_session(manifest)
    assert "tensor contract violation" in str(exc_info.value)


@pytest.mark.asyncio
async def test_robot_motion_command_prohibition() -> None:
    bus = CoreEventBusAdapter()
    # Emitting a payload with forbidden motion/actuator keys must raise a security/safety error
    with pytest.raises(RuntimeError) as exc_info:
        await bus.publish("ers.output", {"cmd_vel": [1.0, 0.0, 0.0]})
    assert "Safety violation" in str(exc_info.value)
    assert "actuator commands" in str(exc_info.value)
