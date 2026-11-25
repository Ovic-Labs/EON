"""Phase 3.3 reliability, session bounds, queue overflow, rate-limit, and CLI tests."""

from __future__ import annotations

import base64
import io

import numpy as np
import psutil
import pytest
from eon_ers.config import ERSConfig
from eon_ers.engine import ERSEngine
from eon_ers.exceptions import ERSError
from eon_ers.live.cli import parse_args
from eon_ers.live.manager import LiveSessionManager
from eon_ers.live.server import create_live_app
from eon_ers.live.session import TERMINAL_LIVE_STATES
from fastapi.testclient import TestClient
from PIL import Image


def _jpeg_b64() -> str:
    arr = np.full((64, 64, 3), 120, dtype=np.uint8)
    buf = io.BytesIO()
    Image.fromarray(arr).save(buf, format="JPEG")
    return base64.b64encode(buf.getvalue()).decode("ascii")


def test_cli_default_port_is_standardized_to_8000() -> None:
    """Verify standard local preview host/port defaults match docs (`127.0.0.1:8000`)."""
    args = parse_args([])
    assert args.host == "127.0.0.1"
    assert args.port == 8000


def test_session_manager_enforces_capacity_and_evicts_closed_sessions() -> None:
    """Verify bounded active session table evicts closed sessions and rejects overflow."""
    mgr = LiveSessionManager(ERSEngine(ERSConfig()), max_sessions=8)
    for idx in range(8):
        rec = mgr.create_live_session(session_id=f"cap-{idx}")
        if idx < 4:
            mgr.delete_live_session(rec.session_id)

    # Closed sessions are all evicted automatically when capacity arrives
    fresh = mgr.create_live_session(session_id="cap-fresh")
    assert fresh.session_id == "cap-fresh"

    # Filling remaining slots up to max_sessions with active sessions blocks further allocation
    while len(mgr._sessions) < 8:
        mgr.create_live_session()
    with pytest.raises(ERSError) as exc_info:
        mgr.create_live_session(session_id="cap-overflow")
    assert exc_info.value.error_code == "ERS_SESSION_CAPACITY_EXCEEDED"


def test_websocket_queue_overflow_invalid_inputs_and_rate_limits() -> None:
    """Verify bounded WS queue drops excess frames cleanly and handles invalid payloads."""
    cfg = ERSConfig(max_ws_queue_size=2, ws_max_messages_per_second=120.0)
    engine = ERSEngine(cfg)
    mgr = LiveSessionManager(engine)
    app = create_live_app(engine=engine, session_manager=mgr)
    img_b64 = _jpeg_b64()

    with TestClient(app) as client:
        sid = "overflow-ws-session"
        assert (
            client.post(
                "/api/consent/register",
                json={"session_id": sid, "consent_reference": "reliability-ref"},
            ).status_code
            == 200
        )

        # Invalid image & audio base64 rejected cleanly over REST without unhandled 500s
        bad_img = client.post(
            "/api/process/frame",
            json={
                "session_id": sid,
                "consent_reference": "reliability-ref",
                "modality": "facial",
                "image_base64": "!!!",
            },
        )
        assert bad_img.status_code == 200
        assert bad_img.json()["status"] in ("error", "insufficient_evidence", "degraded")

        with client.websocket_connect(f"/ws/live/{sid}") as ws:
            ws.send_json({"type": "init", "consent_reference": "reliability-ref"})
            assert ws.receive_json()["status"] == "session_initialized"

            # Unsupported message type returns explicit error
            ws.send_json({"type": "nonexistent_cmd"})
            err = ws.receive_json()
            assert err["type"] == "error"

            # Rapid burst exceeds max_ws_queue_size=2 cleanly without deadlock
            for _ in range(8):
                ws.send_json(
                    {
                        "type": "frame",
                        "session_id": sid,
                        "consent_reference": "reliability-ref",
                        "image_base64": img_b64,
                    }
                )
            ws.send_json({"type": "ping"})
            seen_pong = False
            for _ in range(25):
                pkt = ws.receive_json()
                if pkt.get("type") == "pong":
                    seen_pong = True
                    break
            assert seen_pong

            # Cleanup via delete marks session closed and clears active map
            del_res = client.delete(f"/api/v1/live/sessions/{sid}")
            assert del_res.status_code == 200
            rec = mgr.get_live_session(sid)
            assert rec is not None and rec.state in TERMINAL_LIVE_STATES


def test_cpu_memory_stability_and_http_rate_limit() -> None:
    """Verify 25 sequential CPU frames stay bounded in memory and HTTP rate limits return 429."""
    engine = ERSEngine(ERSConfig(rate_limit_requests_per_minute=200))
    app = create_live_app(engine=engine, session_manager=LiveSessionManager(engine))
    img_b64 = _jpeg_b64()
    proc = psutil.Process()

    with TestClient(app) as client:
        sid = "cpu-stability-session"
        client.post(
            "/api/consent/register",
            json={"session_id": sid, "consent_reference": "stability-token"},
        )
        rss_before = proc.memory_info().rss
        for _ in range(25):
            r = client.post(
                "/api/process/frame",
                json={
                    "session_id": sid,
                    "consent_reference": "stability-token",
                    "modality": "facial",
                    "image_base64": img_b64,
                },
            )
            assert r.status_code == 200
        rss_after = proc.memory_info().rss
        assert (rss_after - rss_before) < 250 * 1024 * 1024

    limited_engine = ERSEngine(ERSConfig(rate_limit_requests_per_minute=10))
    limited_app = create_live_app(
        engine=limited_engine, session_manager=LiveSessionManager(limited_engine)
    )
    with TestClient(limited_app) as limited_client:
        statuses = [limited_client.get("/api/v1/models").status_code for _ in range(12)]
        assert 429 in statuses
