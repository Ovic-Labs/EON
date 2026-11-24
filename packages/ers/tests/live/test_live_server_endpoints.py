"""Live API and WebSocket server endpoint integration tests for Phase 3.1.3."""

from __future__ import annotations

import json
from typing import Generator

import pytest
from eon_ers.config import ERSConfig
from eon_ers.engine import ERSEngine
from eon_ers.live.manager import LiveSessionManager
from eon_ers.live.server import create_live_app
from starlette.testclient import TestClient


@pytest.fixture
def test_client() -> Generator[TestClient, None, None]:
    """TestClient fixture with live server instance."""
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
    with TestClient(app) as client:
        yield client


def test_api_models_endpoint(test_client: TestClient) -> None:
    """Verify /api/models returns detailed audit states for loaded models."""
    res = test_client.get("/api/models")
    assert res.status_code == 200
    data = res.json()
    assert "models" in data
    assert "overall_qualification" in data
    assert isinstance(data["models"], list)

    for m in data["models"]:
        assert "model_id" in m
        assert "state" in m
        assert "is_validated" in m
        assert "license" in m
        assert "provenance" in m


def test_api_devices_endpoint(test_client: TestClient) -> None:
    """Verify /api/devices returns audio/video hardware detection schema."""
    res = test_client.get("/api/devices")
    assert res.status_code == 200
    data = res.json()
    assert "camera_active" in data
    assert "microphone_active" in data
    assert "has_consent" in data


def test_api_telemetry_endpoint(test_client: TestClient) -> None:
    """Verify /api/telemetry/{session_id} returns performance latency metrics."""
    res = test_client.get("/api/telemetry/sample-session-123")
    assert res.status_code == 200
    data = res.json()
    assert data["session_id"] == "sample-session-123"
    assert "p50_ms" in data
    assert "p95_ms" in data
    assert "p99_ms" in data


def test_websocket_payload_bounds_and_safety(test_client: TestClient) -> None:
    """Verify WebSocket rejects payloads exceeding 5MB bound and unknown message types."""
    with test_client.websocket_connect("/ws/stream") as ws:
        # 1. Unknown message type rejection
        ws.send_text(json.dumps({"type": "unknown_action", "session_id": "test"}))
        res1 = json.loads(ws.receive_text())
        assert res1["type"] == "error"
        assert "Unsupported message type" in res1["error"]

        # 2. Oversized payload (> 5MB)
        large_junk = "a" * (5 * 1024 * 1024 + 100)
        ws.send_text(large_junk)
        res2 = json.loads(ws.receive_text())
        assert res2["type"] == "error"
        assert "exceeds maximum allowed size" in res2["error"]
