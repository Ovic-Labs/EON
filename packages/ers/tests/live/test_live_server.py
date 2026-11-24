"""Integration tests for FastAPI server and WebSocket streaming endpoints."""

from __future__ import annotations

import json
from typing import Generator

import pytest
from eon_ers.config import ERSConfig
from eon_ers.engine import ERSEngine
from eon_ers.live.manager import LiveSessionManager
from eon_ers.live.server import create_live_app
from starlette.testclient import TestClient

from .conftest import create_sample_audio_b64, create_sample_face_b64


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


def test_dashboard_endpoint(client: TestClient) -> None:
    """Verify root / serves the HTML demonstration dashboard."""
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "OVIC EON" in response.text
    assert "ERS Live Input Demonstration" in response.text
    assert "Epistemic Modesty" in response.text


def test_health_endpoint(client: TestClient) -> None:
    """Verify health endpoint reports correct component status and invariants."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "HEALTHY"
    assert data["is_running"] is True
    assert data["core_integration_status"] == "NOT_CONNECTED"
    assert "missing_dependencies" in data


def test_consent_endpoints_lifecycle(client: TestClient) -> None:
    """Verify registering, querying, and revoking consent via REST."""
    session_id = "rest-consent-session"
    token = "auth-token-consent-999"

    # Register consent
    reg_resp = client.post(
        "/api/consent/register",
        json={"session_id": session_id, "consent_reference": token},
    )
    assert reg_resp.status_code == 200
    assert reg_resp.json()["has_active_consent"] is True

    # Check status
    stat_resp = client.get(f"/api/consent/status/{session_id}")
    assert stat_resp.status_code == 200
    stat_data = stat_resp.json()
    assert stat_data["has_active_consent"] is True
    assert stat_data["is_revoked"] is False

    # Revoke consent
    rev_resp = client.post(
        "/api/consent/revoke",
        json={"session_id": session_id},
    )
    assert rev_resp.status_code == 200
    assert rev_resp.json()["has_active_consent"] is False
    assert rev_resp.json()["is_revoked"] is True


def test_process_frame_rest_endpoint(client: TestClient) -> None:
    """Verify REST frame processing with valid consent."""
    session_id = "rest-frame-session"
    token = "auth-token-frame-111"

    # Register consent
    client.post(
        "/api/consent/register",
        json={"session_id": session_id, "consent_reference": token},
    )

    face_b64 = create_sample_face_b64()
    resp = client.post(
        "/api/process/frame",
        json={
            "session_id": session_id,
            "modality": "facial",
            "image_base64": face_b64,
            "consent_reference": token,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] in ("ok", "insufficient_evidence")
    assert data["modality"] == "facial"
    assert data["is_definitive_claim"] is False
    assert "dominant_estimate" in data


def test_process_audio_rest_endpoint(client: TestClient) -> None:
    """Verify REST audio processing with valid consent."""
    session_id = "rest-audio-session"
    token = "auth-token-audio-222"

    client.post(
        "/api/consent/register",
        json={"session_id": session_id, "consent_reference": token},
    )

    audio_b64 = create_sample_audio_b64()
    resp = client.post(
        "/api/process/audio",
        json={
            "session_id": session_id,
            "modality": "speech",
            "audio_base64": audio_b64,
            "sample_rate": 16000,
            "consent_reference": token,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["modality"] == "speech"
    assert data["is_definitive_claim"] is False


def test_process_multimodal_rest_endpoint(client: TestClient) -> None:
    """Verify REST multimodal processing with concurrent face and audio."""
    session_id = "rest-multi-session"
    token = "auth-token-multi-333"

    client.post(
        "/api/consent/register",
        json={"session_id": session_id, "consent_reference": token},
    )

    face_b64 = create_sample_face_b64()
    audio_b64 = create_sample_audio_b64()
    resp = client.post(
        "/api/process/multimodal",
        json={
            "session_id": session_id,
            "image_base64": face_b64,
            "audio_base64": audio_b64,
            "sample_rate": 16000,
            "consent_reference": token,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "fused_probabilities" in data
    assert data["is_definitive_claim"] is False


def test_reset_session_rest_endpoint(client: TestClient) -> None:
    """Verify resetting session temporal ring buffer."""
    resp = client.post("/api/session/reset", json={"session_id": "test-reset-session"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "reset"


def test_websocket_stream_full_lifecycle(client: TestClient) -> None:
    """Verify WebSocket bi-directional streaming lifecycle."""
    session_id = "ws-session-stream-1"
    token = "ws-consent-token-123"
    face_b64 = create_sample_face_b64()
    audio_b64 = create_sample_audio_b64()

    with client.websocket_connect(f"/ws/live/{session_id}") as ws:
        # 1. Initialize session with consent token
        ws.send_text(
            json.dumps({"type": "init", "session_id": session_id, "consent_reference": token})
        )
        init_reply = json.loads(ws.receive_text())
        assert init_reply["type"] == "status"
        assert init_reply["status"] == "session_initialized"

        # 2. Ingest camera frame
        ws.send_text(
            json.dumps(
                {
                    "type": "frame",
                    "session_id": session_id,
                    "image_base64": face_b64,
                    "consent_reference": token,
                }
            )
        )
        frame_obs = json.loads(ws.receive_text())
        assert frame_obs["type"] == "observation"
        assert frame_obs["modality"] == "facial"
        assert frame_obs["data"]["is_definitive_claim"] is False

        # Ingested frame also synthesizes updated fusion
        fusion_msg = json.loads(ws.receive_text())
        assert fusion_msg["type"] == "fusion"
        assert fusion_msg["data"]["is_definitive_claim"] is False

        # 3. Ingest microphone audio chunk
        ws.send_text(
            json.dumps(
                {
                    "type": "audio",
                    "session_id": session_id,
                    "audio_base64": audio_b64,
                    "sample_rate": 16000,
                    "consent_reference": token,
                }
            )
        )
        audio_obs = json.loads(ws.receive_text())
        assert audio_obs["type"] == "observation"
        assert audio_obs["modality"] == "speech"
        assert audio_obs["data"]["is_definitive_claim"] is False

        audio_fusion = json.loads(ws.receive_text())
        assert audio_fusion["type"] == "fusion"

        # 4. Ingest multimodal frame
        ws.send_text(
            json.dumps(
                {
                    "type": "multimodal",
                    "session_id": session_id,
                    "image_base64": face_b64,
                    "audio_base64": audio_b64,
                    "consent_reference": token,
                }
            )
        )
        multi_reply = json.loads(ws.receive_text())
        assert multi_reply["type"] == "fusion"

        # 5. Revoke consent mid-stream
        ws.send_text(json.dumps({"type": "revoke", "session_id": session_id}))
        rev_reply = json.loads(ws.receive_text())
        assert rev_reply["type"] == "status"
        assert rev_reply["status"] == "consent_revoked"

        # 6. Subsequent frame must be rejected
        ws.send_text(
            json.dumps(
                {
                    "type": "frame",
                    "session_id": session_id,
                    "image_base64": face_b64,
                    "consent_reference": token,
                }
            )
        )
        rejected_reply = json.loads(ws.receive_text())
        assert rejected_reply["type"] == "observation"
        assert rejected_reply["data"]["status"] == "consent_rejected"


def test_websocket_malformed_json_handling(client: TestClient) -> None:
    """Verify WebSocket server safely handles malformed JSON without terminating."""
    with client.websocket_connect("/ws/live/ws-error-session") as ws:
        ws.send_text("THIS IS NOT JSON {{{{{")
        reply = json.loads(ws.receive_text())
        assert reply["type"] == "error"
        assert "Invalid JSON" in reply["error"]

        # Socket still responds to valid messages
        ws.send_text(json.dumps({"type": "init", "consent_reference": "ref"}))
        valid_reply = json.loads(ws.receive_text())
        assert valid_reply["type"] == "status"
