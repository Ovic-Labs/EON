"""Quickstart example for OVIC EON Emotion Recognition System (ERS)."""

import asyncio
import io
import wave

import numpy as np
from eon_ers import ERSConfig, ERSEngine, ERSInput, Modality
from PIL import Image


def create_sample_face() -> bytes:
    img = Image.new("RGB", (128, 128), color=(210, 180, 160))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def create_sample_speech() -> bytes:
    sr = 16000
    t = np.linspace(0, 1.0, sr, endpoint=False)
    audio = 0.3 * np.sin(2 * np.pi * 200 * t)
    audio_int16 = (audio * 32767).astype(np.int16)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(audio_int16.tobytes())
    return buf.getvalue()


async def main() -> None:
    config = ERSConfig(
        enable_facial=True,
        enable_speech=True,
        enable_multimodal_fusion=True,
        facial_model_path="packages/ers/models/facial_emotion_model.onnx",
        speech_model_path="packages/ers/models/speech_emotion_model.onnx",
    )

    async with ERSEngine(config) as engine:
        print("ERS Engine running. State:", engine.state.value)

        # 1. Process Facial Observation
        face_input = ERSInput(
            session_id="user-session-001",
            modality=Modality.FACIAL,
            consent_reference="consent-token-abc-123",
            image_payload=create_sample_face(),
        )
        face_obs = await engine.process_facial(face_input)
        print("\n[Facial Observation]")
        print("Dominant Estimate:", face_obs.dominant_estimate)
        print("Confidence:", face_obs.confidence)
        print("Uncertainty:", face_obs.uncertainty)
        print("Latency (ms):", face_obs.processing_latency_ms)
        print("Is Definitive Claim:", face_obs.is_definitive_claim)

        # 2. Process Speech Observation
        speech_input = ERSInput(
            session_id="user-session-001",
            modality=Modality.SPEECH,
            consent_reference="consent-token-abc-123",
            audio_payload=create_sample_speech(),
            sample_rate=16000,
        )
        speech_obs = await engine.process_speech(speech_input)
        print("\n[Speech Observation]")
        print("Dominant Estimate:", speech_obs.dominant_estimate)
        print("Confidence:", speech_obs.confidence)
        print("Uncertainty:", speech_obs.uncertainty)
        print("Latency (ms):", speech_obs.processing_latency_ms)


if __name__ == "__main__":
    asyncio.run(main())
