"""Shared fixtures and payload generators for live input tests."""

from __future__ import annotations

import base64
import io
import wave
from typing import Generator

import numpy as np
import pytest
from eon_ers.config import ERSConfig
from eon_ers.engine import ERSEngine
from eon_ers.live.manager import LiveSessionManager
from eon_ers.live.server import create_live_app
from PIL import Image
from starlette.testclient import TestClient


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


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """TestClient fixture with initialized application lifespan."""
    config = ERSConfig(
        enable_facial=True,
        enable_speech=True,
        enable_multimodal_fusion=True,
        facial_model_path="packages/ers/models/facial_emotion_model.onnx",
        speech_model_path="packages/ers/models/speech_emotion_model.onnx",
    )
    engine = ERSEngine(config)
    manager = LiveSessionManager(engine)
    app = create_live_app(engine=engine, session_manager=manager)

    with TestClient(app) as test_client:
        yield test_client
