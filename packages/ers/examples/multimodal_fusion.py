"""Multimodal fusion and temporal smoothing example for ERS."""

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
        alignment_window_seconds=0.5,
    )

    async with ERSEngine(config) as engine:
        # Multimodal inputs
        face_input = ERSInput(
            session_id="session-multimodal",
            modality=Modality.FACIAL,
            consent_reference="consent-token-xyz-789",
            image_payload=create_sample_face(),
        )
        speech_input = ERSInput(
            session_id="session-multimodal",
            modality=Modality.SPEECH,
            consent_reference="consent-token-xyz-789",
            audio_payload=create_sample_speech(),
            sample_rate=16000,
        )

        fused_result = await engine.process_multimodal(face_input, speech_input)
        print("=== Multimodal Fusion Result ===")
        print("Dominant Estimate:", fused_result.dominant_estimate)
        print("Fused Confidence:", fused_result.confidence)
        print("Fused Uncertainty:", fused_result.uncertainty)
        print("Modality Weights:", fused_result.modality_weights)
        print("Conflicting Evidence:", fused_result.conflicting_evidence)
        print("Conflict Divergence Metric:", fused_result.conflict_metric)
        print("Is Definitive Claim:", fused_result.is_definitive_claim)


if __name__ == "__main__":
    asyncio.run(main())
