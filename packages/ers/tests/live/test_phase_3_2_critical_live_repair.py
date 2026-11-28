"""Regression tests for critical live consent lifecycle, device status, JS syntax, and auth parity."""

from __future__ import annotations

import json
import shutil
import subprocess
from html.parser import HTMLParser
from pathlib import Path

import pytest
from eon_ers.api.authentication import APIKeyAuthManager, Role
from eon_ers.config import ERSConfig
from eon_ers.engine import ERSEngine
from eon_ers.exceptions import ERSPrivacyConsentError
from eon_ers.live.dashboard import get_dashboard_html
from eon_ers.live.server import create_live_app
from eon_ers.privacy.consent import ConsentManager
from starlette.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from .conftest import create_sample_audio_b64, create_sample_face_b64


def test_revoked_consent_session_is_terminal_and_new_session_works() -> None:
    cm = ConsentManager(enforce_consent=True)
    cm.register_consent("sess-term-1", "tok-1")
    cm.validate_consent("sess-term-1", "tok-1")

    # Repeated revocation must remain cleanly revoked
    cm.revoke_consent("sess-term-1")
    cm.revoke_consent("sess-term-1")
    status = cm.get_status("sess-term-1")
    assert status["has_active_consent"] is False
    assert status["is_revoked"] is True

    # Reactivating the same revoked session ID must fail closed
    with pytest.raises(ERSPrivacyConsentError, match="revoked"):
        cm.register_consent("sess-term-1", "tok-2")

    # A brand new session ID can be granted fresh consent cleanly
    cm.register_consent("sess-term-2", "tok-2")
    cm.validate_consent("sess-term-2", "tok-2")


class _InlineScriptParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._inside_inline_script = False
        self.scripts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "script":
            self._inside_inline_script = not any(name == "src" for name, _ in attrs)

    def handle_endtag(self, tag: str) -> None:
        if tag == "script":
            self._inside_inline_script = False

    def handle_data(self, data: str) -> None:
        if self._inside_inline_script:
            self.scripts.append(data)


def test_dashboard_has_no_hardcoded_consent_and_valid_js_syntax(tmp_path: Path) -> None:
    html = get_dashboard_html()
    assert "explicit-user-consent-token" not in html
    assert 'consentReference: ""' in html
    assert 'id="live-consent-ref" type="password" value=""' in html
    assert "ensureActiveConsentForCapture()" in html
    assert "downsampleTo16k(" in html
    assert "startNewSession()" in html
    assert "apiRequest(" in html

    # Verify extracted client JavaScript parses cleanly with Node if installed
    parser = _InlineScriptParser()
    parser.feed(html)
    parser.close()
    assert len(parser.scripts) == 1
    js_file = tmp_path / "dashboard_check.js"
    js_file.write_text(parser.scripts[0], encoding="utf-8")
    node_bin = shutil.which("node")
    if node_bin:
        proc = subprocess.run([node_bin, "--check", str(js_file)], capture_output=True, text=True)
        assert proc.returncode == 0, f"Dashboard JS syntax error: {proc.stderr}"


def test_device_status_reflects_verified_capture_never_hardcoded() -> None:
    config = ERSConfig(
        facial_model_path="packages/ers/models/facial_emotion_model.onnx",
        speech_model_path="packages/ers/models/speech_emotion_model.onnx",
    )
    app = create_live_app(engine=ERSEngine(config))
    with TestClient(app) as client:
        # Initially no verified capture has started
        d0 = client.get("/api/devices").json()
        assert d0["camera_active"] is False
        assert d0["microphone_active"] is False
        assert d0["camera_state"] == "unknown"
        assert d0["microphone_state"] == "unknown"

        # Register explicit consent -> still inactive until real media arrives
        sid = "dev-status-sess"
        tok = "dev-status-tok"
        assert (
            client.post(
                "/api/consent/register", json={"session_id": sid, "consent_reference": tok}
            ).status_code
            == 200
        )
        d1 = client.get("/api/v1/devices").json()
        assert d1["has_consent"] is True
        assert d1["camera_active"] is False
        assert d1["microphone_active"] is False

        # Send real frame and audio over WS -> device telemetry turns active
        face_b64 = create_sample_face_b64()
        aud_b64 = create_sample_audio_b64()
        with client.websocket_connect(f"/ws/live/{sid}") as ws:
            ws.send_text(json.dumps({"type": "init", "session_id": sid}))
            _ = json.loads(ws.receive_text())
            ws.send_text(
                json.dumps(
                    {
                        "type": "frame",
                        "session_id": sid,
                        "consent_reference": tok,
                        "image_base64": face_b64,
                    }
                )
            )
            _ = json.loads(ws.receive_text())
            _ = json.loads(ws.receive_text())
            ws.send_text(
                json.dumps(
                    {
                        "type": "audio",
                        "session_id": sid,
                        "consent_reference": tok,
                        "sample_rate": 16000,
                        "audio_base64": aud_b64,
                    }
                )
            )
            _ = json.loads(ws.receive_text())
            _ = json.loads(ws.receive_text())

            d2 = client.get("/api/devices").json()
            assert d2["camera_active"] is True
            assert d2["microphone_active"] is True

            # Pause/revoke immediately drops verified active flags
            ws.send_text(json.dumps({"type": "revoke", "session_id": sid}))
            _ = json.loads(ws.receive_text())

        d3 = client.get("/api/devices").json()
        assert d3["camera_active"] is False
        assert d3["microphone_active"] is False

        # Revoked session ID cannot be re-registered via REST (409 Conflict)
        reuse_resp = client.post(
            "/api/consent/register", json={"session_id": sid, "consent_reference": "new-tok"}
        )
        assert reuse_resp.status_code == 409


def test_legacy_api_and_ws_enforce_auth_and_cors_when_enabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    auth = APIKeyAuthManager(require_auth=True)
    _, alice_key = auth.issue_key("alice", Role.OPERATOR)
    _, bob_key = auth.issue_key("bob", Role.OPERATOR)
    _, viewer_key = auth.issue_key("viewer", Role.VIEWER)

    config = ERSConfig(
        require_api_auth=True,
        facial_model_path="packages/ers/models/facial_emotion_model.onnx",
        speech_model_path="packages/ers/models/speech_emotion_model.onnx",
    )
    app = create_live_app(engine=ERSEngine(config), auth_manager=auth)
    with TestClient(app) as client:
        # Unauthenticated legacy /api/* requests must fail with 401
        assert client.get("/api/models").status_code == 401
        assert client.get("/api/devices").status_code == 401
        assert (
            client.post(
                "/api/consent/register", json={"session_id": "s", "consent_reference": "t"}
            ).status_code
            == 401
        )
        assert (
            client.post(
                "/api/process/frame", json={"session_id": "s", "image_base64": "x"}
            ).status_code
            == 401
        )

        # Viewer denied analyze/consent write (403)
        assert client.get("/api/models", headers={"X-API-Key": viewer_key}).status_code == 200
        assert (
            client.post(
                "/api/consent/register",
                headers={"X-API-Key": viewer_key},
                json={"session_id": "s", "consent_reference": "t"},
            ).status_code
            == 403
        )

        # Alice creates/registers session -> Bob cannot touch or read Alice's telemetry or consent
        assert (
            client.post(
                "/api/consent/register",
                headers={"X-API-Key": alice_key},
                json={"session_id": "alice-sec", "consent_reference": "a-tok"},
            ).status_code
            == 200
        )
        assert (
            client.get("/api/telemetry/alice-sec", headers={"X-API-Key": bob_key}).status_code
            == 403
        )
        assert (
            client.post(
                "/api/consent/revoke",
                headers={"X-API-Key": bob_key},
                json={"session_id": "alice-sec"},
            ).status_code
            == 403
        )

        # WebSocket rejects unauthenticated init
        with pytest.raises((WebSocketDisconnect, Exception)):
            with client.websocket_connect("/ws/live/alice-sec") as ws_bad:
                ws_bad.send_text(json.dumps({"type": "init", "session_id": "alice-sec"}))
                _ = json.loads(ws_bad.receive_text())
                _ = ws_bad.receive_text()

        # WebSocket first-message auth works cleanly for Alice
        with client.websocket_connect("/ws/live/alice-sec") as ws_ok:
            ws_ok.send_text(json.dumps({"type": "auth", "api_key": alice_key}))
            auth_reply = json.loads(ws_ok.receive_text())
            assert auth_reply["status"] == "authenticated"
            ws_ok.send_text(json.dumps({"type": "init", "session_id": "alice-sec"}))
            init_reply = json.loads(ws_ok.receive_text())
            assert init_reply["status"] == "session_initialized"

        # Disallowed origin must not get CORS Access-Control-Allow-Origin
        cors_bad = client.get("/health", headers={"Origin": "https://evil.example.com"})
        assert cors_bad.headers.get("access-control-allow-origin") != "*"
        assert cors_bad.headers.get("access-control-allow-origin") is None
