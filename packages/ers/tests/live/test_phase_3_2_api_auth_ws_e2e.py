"""End-to-end API v1, WebSocket streaming, RBAC auth, session isolation, and SDK tests."""

from __future__ import annotations

import base64
import io
import json
import struct

import numpy as np
from eon_ers.api.authentication import APIKeyAuthManager, Role
from eon_ers.config import ERSConfig
from eon_ers.engine import ERSEngine
from eon_ers.live.dashboard import get_dashboard_html
from eon_ers.live.server import create_live_app
from eon_ers.sdk.client import ERSClient
from PIL import Image
from starlette.testclient import TestClient

from .conftest import create_sample_audio_b64, create_sample_face_b64


def _make_mjpeg_avi_b64() -> str:
    jpg = base64.b64decode(create_sample_face_b64().split(",", 1)[1])
    movi = b"movi00dc" + struct.pack("<I", len(jpg)) + jpg + (b"\x00" if len(jpg) % 2 else b"")
    list_movi = b"LIST" + struct.pack("<I", len(movi)) + movi
    avih = b"avih" + struct.pack("<I", 4) + struct.pack("<I", 100_000)
    hdrl = b"hdrl" + avih
    list_hdrl = b"LIST" + struct.pack("<I", len(hdrl)) + hdrl
    riff = b"AVI " + list_hdrl + list_movi
    avi = b"RIFF" + struct.pack("<I", len(riff)) + riff
    return base64.b64encode(avi).decode("ascii")


def test_v1_system_analysis_video_text_and_dashboard() -> None:
    config = ERSConfig(
        enable_facial=True,
        enable_speech=True,
        enable_text=True,
        enable_video=True,
        enable_multimodal_fusion=True,
        facial_model_path="packages/ers/models/facial_emotion_model.onnx",
        speech_model_path="packages/ers/models/speech_emotion_model.onnx",
    )
    app = create_live_app(engine=ERSEngine(config))
    with TestClient(app) as client:
        assert client.get("/health").status_code == 200
        ready = client.get("/ready").json()
        assert ready["ready"] is True
        assert ready["qualified_inference_ready"] is False
        assert client.get("/version").json()["api_version"] == "v1"
        assert client.get("/capabilities").json()["modalities"]["text"] is True
        assert "eon_ers_processed_total" in client.get("/metrics?format=prometheus").text

        # Grant consent
        sess = "v1-e2e-session"
        tok = "v1-consent-secret"
        assert (
            client.post(
                "/api/v1/consent", json={"session_id": sess, "consent_reference": tok}
            ).status_code
            == 200
        )

        # Text analysis
        txt_res = client.post(
            "/api/v1/analyze/text",
            json={"session_id": sess, "consent_reference": tok, "text": "Great wonderful joy!"},
        )
        assert txt_res.status_code == 200
        assert txt_res.json()["modality"] == "text"
        assert txt_res.json()["is_definitive_claim"] is False

        # Image + Audio + 3-Modality fusion
        face_b64 = create_sample_face_b64()
        aud_b64 = create_sample_audio_b64()
        mm = client.post(
            "/api/v1/analyze/multimodal",
            json={
                "session_id": sess,
                "consent_reference": tok,
                "image_base64": face_b64,
                "audio_base64": aud_b64,
                "text": "I feel glad today",
            },
        ).json()
        assert mm["schema_version"] == "1.0"
        assert mm["is_definitive_claim"] is False

        # Video upload + job polling
        vid_res = client.post(
            "/api/v1/analyze/video",
            json={
                "session_id": sess,
                "consent_reference": tok,
                "video_base64": _make_mjpeg_avi_b64(),
            },
        )
        assert vid_res.status_code == 200
        job_id = vid_res.json()["job_id"]
        assert client.get(f"/api/v1/analyze/video/{job_id}").status_code == 200

        # Model activation blocked fail-closed for unvalidated baseline model
        act_res = client.post("/api/v1/models/ers-facial-onnx-cpu-v1/activate")
        assert act_res.status_code == 409

        # Datasets & Evaluation reports
        ds = client.get("/api/v1/datasets").json()
        assert len(ds["datasets"]) >= 5
        assert client.get("/api/v1/evaluation/reports").json()["total"] >= 2

        # Live session FSM + WebSocket v1 stream (capabilities, ping/pong, text, frame, revoke)
        created = client.post(
            "/api/v1/live/sessions",
            json={"session_id": "ws-v1-sess", "consent_reference": "ws-tok"},
        )
        assert created.status_code == 200
        assert created.json()["state"] == "READY"

        with client.websocket_connect("/api/v1/live/sessions/ws-v1-sess/stream") as ws:
            ws.send_text(json.dumps({"type": "capabilities", "session_id": "ws-v1-sess"}))
            caps = json.loads(ws.receive_text())
            assert caps["type"] == "capabilities"
            ws.send_text(json.dumps({"type": "ping", "session_id": "ws-v1-sess"}))
            assert json.loads(ws.receive_text())["type"] == "pong"
            ws.send_text(
                json.dumps(
                    {
                        "type": "text",
                        "session_id": "ws-v1-sess",
                        "consent_reference": "ws-tok",
                        "text": "Good morning",
                    }
                )
            )
            txt_ws = json.loads(ws.receive_text())
            assert txt_ws["modality"] == "text"
            ws.send_text(json.dumps({"type": "stop", "session_id": "ws-v1-sess"}))
            assert json.loads(ws.receive_text())["status"] == "stopped"

        assert client.delete("/api/v1/live/sessions/ws-v1-sess").status_code == 200

        # Verify 15-view UI sections present cleanly
        html = get_dashboard_html()
        assert "15. Privacy &amp; Consent" in html
        assert "nav-btn" in html


def test_rbac_auth_rate_limit_and_cross_user_isolation() -> None:
    auth = APIKeyAuthManager(require_auth=True)
    _, alice_key = auth.issue_key("alice", Role.OPERATOR)
    _, bob_key = auth.issue_key("bob", Role.OPERATOR)
    viewer_id, viewer_key = auth.issue_key("carol", Role.VIEWER)
    _, expired_key = auth.issue_key("dave", Role.OPERATOR, ttl_seconds=-1.0)

    config = ERSConfig(
        require_api_auth=True,
        rate_limit_requests_per_minute=20,
        facial_model_path="packages/ers/models/facial_emotion_model.onnx",
        speech_model_path="packages/ers/models/speech_emotion_model.onnx",
    )
    app = create_live_app(engine=ERSEngine(config), auth_manager=auth)

    with TestClient(app) as client:
        # Unauthenticated rejected with 401
        assert client.get("/api/v1/models").status_code == 401
        # Expired key rejected
        assert client.get("/api/v1/models", headers={"X-API-Key": expired_key}).status_code == 401
        # Viewer allowed models:read, denied analyze:run (403)
        assert client.get("/api/v1/models", headers={"X-API-Key": viewer_key}).status_code == 200
        assert (
            client.post(
                "/api/v1/analyze/text",
                headers={"X-API-Key": viewer_key},
                json={"session_id": "s1", "consent_reference": "c1", "text": "hello"},
            ).status_code
            == 403
        )
        # Revoked key rejected
        auth.revoke_key(viewer_id)
        assert client.get("/api/v1/models", headers={"X-API-Key": viewer_key}).status_code == 401

        # Cross-user session isolation: Alice creates session, Bob denied access
        create_alice = client.post(
            "/api/v1/live/sessions",
            headers={"X-API-Key": alice_key},
            json={"session_id": "alice-priv", "consent_reference": "alice-tok"},
        )
        assert create_alice.status_code == 200
        assert (
            client.get(
                "/api/v1/live/sessions/alice-priv", headers={"X-API-Key": bob_key}
            ).status_code
            == 403
        )
        assert (
            client.delete("/api/v1/consent/alice-priv", headers={"X-API-Key": bob_key}).status_code
            == 403
        )


def test_sdk_client_local_async() -> None:
    import asyncio

    async def _run() -> None:
        arr = np.random.randint(60, 220, size=(96, 96, 3), dtype=np.uint8)
        buf = io.BytesIO()
        Image.fromarray(arr).save(buf, format="JPEG")
        async with ERSClient(config=ERSConfig()) as sdk:
            await sdk.register_consent("sdk-s1", "sdk-tok")
            obs = await sdk.analyze_text("sdk-s1", "sdk-tok", "Hello happy friend!")
            assert getattr(obs, "modality").value == "text"
            fused = await sdk.analyze_multimodal(
                "sdk-s1", "sdk-tok", image_bytes=buf.getvalue(), text="Hello!"
            )
            assert getattr(fused, "is_definitive_claim") is False
            await sdk.revoke_consent("sdk-s1")

    asyncio.run(_run())
