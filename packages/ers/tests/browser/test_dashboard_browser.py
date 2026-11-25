"""Automated Chromium/Chrome browser qualification suite for the live ERS dashboard.

NOTE ON HARDWARE vs SIMULATED MEDIA:
Tests marked `[SIMULATED_MEDIA]` configure Chromium with
`--use-fake-device-for-media-stream` and `--use-fake-ui-for-media-stream`
so automated CI runs deterministically without physical webcam/microphone hardware.
Those results verify browser JS/WebRTC/AudioContext/WebSocket integration under
simulated media streams and must NEVER be reported as physical hardware verification.
"""

from __future__ import annotations

import os
import pathlib
import socket
import threading
import time
from collections.abc import Generator
from typing import Any

import httpx
import pytest
import uvicorn

playwright_sync = pytest.importorskip("playwright.sync_api")

from eon_ers.config import ERSConfig  # noqa: E402
from eon_ers.engine import ERSEngine  # noqa: E402
from eon_ers.live.manager import LiveSessionManager  # noqa: E402
from eon_ers.live.server import create_live_app  # noqa: E402


def _find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


def _system_chrome_path() -> str | None:
    candidates = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        "/usr/bin/google-chrome",
        "/usr/bin/chromium",
        "/usr/bin/chromium-browser",
    ]
    for path in candidates:
        if pathlib.Path(path).exists():
            return path
    return None


def _launch_chromium(p: Any, *, fake_media: bool = False) -> Any:
    args = ["--headless=new", "--no-sandbox"]
    if fake_media:
        args.extend(
            [
                "--use-fake-device-for-media-stream",
                "--use-fake-ui-for-media-stream",
            ]
        )
    chrome_exe = _system_chrome_path()
    try:
        if chrome_exe and os.name == "nt":
            return p.chromium.launch(executable_path=chrome_exe, headless=True, args=args)
    except Exception:
        pass
    return p.chromium.launch(headless=True, args=args)


class _RunningUvicorn:
    """In-process real TCP uvicorn server for Playwright end-to-end tests."""

    def __init__(self, app: Any) -> None:
        self.port = _find_free_port()
        self.base_url = f"http://127.0.0.1:{self.port}"
        config = uvicorn.Config(app, host="127.0.0.1", port=self.port, log_level="warning")
        self._server = uvicorn.Server(config)
        self._thread = threading.Thread(target=self._server.run, daemon=True)

    def __enter__(self) -> _RunningUvicorn:
        self._thread.start()
        deadline = time.monotonic() + 15.0
        while time.monotonic() < deadline:
            try:
                r = httpx.get(f"{self.base_url}/health", timeout=1.0)
                if r.status_code == 200:
                    return self
            except Exception:
                time.sleep(0.1)
        raise RuntimeError("Timed out waiting for live uvicorn test server to become healthy.")

    def __exit__(self, *args: object) -> None:
        self._server.should_exit = True
        self._thread.join(timeout=5.0)


@pytest.fixture
def live_server() -> Generator[_RunningUvicorn, None, None]:
    engine = ERSEngine(ERSConfig())
    mgr = LiveSessionManager(engine)
    app = create_live_app(engine=engine, session_manager=mgr)
    with _RunningUvicorn(app) as srv:
        yield srv


def test_browser_simulated_full_live_lifecycle_and_device_telemetry(
    live_server: _RunningUvicorn,
) -> None:
    """[SIMULATED_MEDIA] Verify full browser UI, WebRTC fake cam/mic, WS telemetry, and revocation."""
    with playwright_sync.sync_playwright() as p:
        browser = _launch_chromium(p, fake_media=True)
        context = browser.new_context(
            viewport={"width": 1440, "height": 900},
            permissions=["camera", "microphone"],
        )
        page = context.new_page()
        console_errors: list[str] = []
        page_errors: list[str] = []
        http_5xx: list[str] = []

        page.on(
            "console",
            lambda msg: console_errors.append(msg.text) if msg.type == "error" else None,
        )
        page.on("pageerror", lambda exc: page_errors.append(str(exc)))
        page.on(
            "response",
            lambda res: http_5xx.append(f"{res.status} {res.url}") if res.status >= 500 else None,
        )

        # 1. Load dashboard & verify Overview initial state
        page.goto(live_server.base_url, wait_until="networkidle")
        assert page.title() == "OVIC EON — ERS Enterprise Console"
        page.wait_for_function(
            "() => document.getElementById('badge-health').textContent.includes('HEALTHY')"
        )
        assert "not granted" in page.locator("#badge-consent").inner_text().lower()
        assert "UNVALIDATED" in page.locator("#badge-qual").inner_text()
        assert page.locator("#btn-start-cam").is_disabled()
        assert page.locator("#btn-start-mic").is_disabled()
        assert page.locator("#btn-revoke-consent").is_disabled()

        # Verify /api/devices initially unknown/false
        dev0 = httpx.get(f"{live_server.base_url}/api/devices", timeout=5.0).json()
        assert dev0["camera_active"] is False
        assert dev0["microphone_active"] is False
        assert dev0["camera_state"] == "unknown"

        # 2. Switch to Live ERS & check empty consent rejection
        page.click('button[data-view="live"]')
        page.click("#btn-grant-consent")
        page.wait_for_function(
            "() => document.getElementById('global-err-banner').classList.contains('visible')"
        )
        assert "consent token" in page.locator("#global-err-text").inner_text().lower()

        # 3. Grant explicit user consent -> WS connects, cam/mic enable
        initial_sid = page.locator("#live-session-id").input_value()
        assert initial_sid.startswith("live-")
        page.fill("#live-consent-ref", "playwright-simulated-token-2026")
        page.click("#btn-grant-consent")
        page.wait_for_function(
            "() => document.getElementById('badge-consent').textContent.includes('ACTIVE')"
        )
        page.wait_for_function(
            "() => document.getElementById('badge-ws').textContent.includes('connected')"
        )
        assert not page.locator("#btn-start-cam").is_disabled()
        assert not page.locator("#btn-start-mic").is_disabled()
        assert not page.locator("#btn-revoke-consent").is_disabled()

        # 4. [SIMULATED_MEDIA] Start fake webcam -> verify video plays & backend receives frames
        page.click("#btn-start-cam")
        page.wait_for_function(
            """() => {
                const v = document.getElementById('webcam-video');
                return v && v.readyState >= 2 && v.videoWidth > 0;
            }""",
            timeout=10000,
        )
        assert "Active @" in page.locator("#live-cam-stats").inner_text()
        page.wait_for_function(
            "() => document.getElementById('res-face-dom').textContent !== '-'",
            timeout=10000,
        )
        dev_cam = httpx.get(f"{live_server.base_url}/api/devices", timeout=5.0).json()
        assert dev_cam["camera_active"] is True
        assert dev_cam["camera_state"] == "active"

        # Stop webcam -> tracks stopped & inactive telemetry
        page.click("#btn-stop-cam")
        page.wait_for_function(
            "() => document.getElementById('live-cam-stats').textContent === 'Inactive'"
        )
        dev_cam_stopped = httpx.get(f"{live_server.base_url}/api/devices", timeout=5.0).json()
        assert dev_cam_stopped["camera_active"] is False

        # 5. [SIMULATED_MEDIA] Start fake microphone -> verify AudioContext 16kHz & stop cleanup
        page.click("#btn-start-mic")
        page.wait_for_function(
            "() => Boolean(typeof state !== 'undefined' && state.micStream && state.audioCtx)",
            timeout=10000,
        )
        page.click("#btn-stop-mic")
        page.wait_for_function("() => state.micStream === null && state.audioCtx === null")
        assert "(Inactive)" in page.locator("#mic-silence-badge").inner_text()

        # 6. Model Registry activation guard (unvalidated model -> HTTP 409)
        page.click('button[data-view="registry"]')
        page.wait_for_selector("#reg-table button")
        page.locator("#reg-table button").first.click()
        page.wait_for_function(
            "() => document.getElementById('global-err-banner').classList.contains('visible')"
        )
        assert "409" in page.locator("#global-err-text").inner_text()

        # 7. Revoke Consent -> terminal lockout & HTTP 409 on re-grant
        page.click('button[data-view="live"]')
        page.click("#btn-revoke-consent")
        page.wait_for_function(
            "() => document.getElementById('badge-consent').textContent.includes('REVOKED')"
        )
        assert page.locator("#btn-start-cam").is_disabled()
        assert page.locator("#btn-grant-consent").is_disabled()
        # Attempt server-side registration against revoked SID must return 409
        regrant_res = httpx.post(
            f"{live_server.base_url}/api/consent/register",
            json={"session_id": initial_sid, "consent_reference": "reuse-attempt"},
            timeout=5.0,
        )
        assert regrant_res.status_code == 409

        # 8. New Session -> fresh ID & clean consent reset
        page.click("#btn-new-session")
        new_sid = page.locator("#live-session-id").input_value()
        assert new_sid != initial_sid
        assert "not granted" in page.locator("#badge-consent").inner_text().lower()

        # 9. Reload recovery -> zero errors, fresh unconsented state
        page.reload(wait_until="networkidle")
        page.wait_for_function(
            "() => document.getElementById('badge-health').textContent.includes('HEALTHY')"
        )
        assert "not granted" in page.locator("#badge-consent").inner_text().lower()

        assert not page_errors, f"Uncaught page errors: {page_errors}"
        assert not http_5xx, f"Server 5xx errors: {http_5xx}"
        unexpected_console = [c for c in console_errors if "409" not in c]
        assert not unexpected_console, f"Unexpected console errors: {unexpected_console}"
        browser.close()


def test_browser_media_permission_denied_recovery_and_ws_reconnect(
    live_server: _RunningUvicorn,
) -> None:
    """Verify clear instructions when camera/mic permissions are denied and WS reconnect works."""
    with playwright_sync.sync_playwright() as p:
        browser = _launch_chromium(p, fake_media=False)
        context = browser.new_context(viewport={"width": 1280, "height": 800})
        page = context.new_page()
        page_errors: list[str] = []
        page.on("pageerror", lambda exc: page_errors.append(str(exc)))

        # Deny getUserMedia deterministically in browser context to verify permission error UX
        page.add_init_script(
            """
            Object.defineProperty(navigator, 'mediaDevices', {
              value: {
                enumerateDevices: async () => [],
                addEventListener: () => {},
                getUserMedia: async () => {
                  const err = new Error('Permission denied by browser policy');
                  err.name = 'NotAllowedError';
                  throw err;
                }
              },
              configurable: true
            });
            """
        )

        page.goto(live_server.base_url, wait_until="networkidle")
        page.click('button[data-view="live"]')
        page.fill("#live-consent-ref", "perm-deny-token-2026")
        page.click("#btn-grant-consent")
        page.wait_for_function(
            "() => document.getElementById('badge-ws').textContent.includes('connected')"
        )

        # Trigger denied camera
        page.click("#btn-start-cam")
        page.wait_for_function(
            "() => document.getElementById('live-cam-stats').textContent === 'Permission Denied'"
        )
        cam_err = page.locator("#global-err-text").inner_text()
        assert "NotAllowedError" in cam_err and "site permissions" in cam_err

        # Trigger denied mic
        page.click("#btn-start-mic")
        page.wait_for_function(
            "() => document.getElementById('mic-silence-badge').textContent.includes('Permission Denied')"
        )
        mic_err = page.locator("#global-err-text").inner_text()
        assert "NotAllowedError" in mic_err and "site permissions" in mic_err

        # Simulate WS disconnect and manual reconnect
        page.evaluate("() => { if (typeof state !== 'undefined' && state.ws) state.ws.close(); }")
        page.wait_for_function(
            "() => document.getElementById('badge-ws').textContent.includes('disconnected')"
        )
        page.click("#btn-ws-reconnect")
        page.wait_for_function(
            "() => document.getElementById('badge-ws').textContent.includes('connected')"
        )

        assert not page_errors, f"Uncaught JS errors: {page_errors}"
        browser.close()


def test_browser_api_auth_and_responsive_desktop_mobile_layouts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify UI API-key auth enforcement and responsive desktop/mobile layout with zero overflow."""
    monkeypatch.setenv("EON_ERS_API_AUTH", "true")
    monkeypatch.setenv("EON_ERS_BOOTSTRAP_API_KEYS", "ui-admin:admin:phase33-secret-key")
    engine = ERSEngine(ERSConfig(require_api_auth=True))
    mgr = LiveSessionManager(engine)
    app = create_live_app(engine=engine, session_manager=mgr)

    with _RunningUvicorn(app) as srv, playwright_sync.sync_playwright() as p:
        browser = _launch_chromium(p, fake_media=False)
        for vp in ({"width": 1440, "height": 900}, {"width": 390, "height": 844}):
            ctx = browser.new_context(viewport=vp)
            page = ctx.new_page()
            page.goto(srv.base_url, wait_until="networkidle")
            # Responsive overflow check
            has_overflow = page.evaluate(
                "() => document.documentElement.scrollWidth > window.innerWidth + 2"
            )
            assert not has_overflow, f"Horizontal overflow detected at viewport {vp}"
            ctx.close()

        # Verify fail-closed auth before key entry -> succeeds after setting X-API-Key in Settings
        ctx = browser.new_context(viewport={"width": 1440, "height": 900})
        page = ctx.new_page()
        page.goto(srv.base_url, wait_until="networkidle")
        page.wait_for_function(
            "() => document.getElementById('global-err-banner').classList.contains('visible')"
        )
        assert "401" in page.locator("#global-err-text").inner_text()

        page.click('button[data-view="settings"]')
        page.fill("#cfg-api-key", "phase33-secret-key")
        page.locator("#cfg-api-key").dispatch_event("change")
        page.click('button[data-view="overview"]')
        page.wait_for_function(
            "() => document.getElementById('badge-health').textContent.includes('HEALTHY')"
        )

        # Grant consent & verify authenticated WS connection
        page.click('button[data-view="live"]')
        page.fill("#live-consent-ref", "auth-browser-consent")
        page.click("#btn-grant-consent")
        page.wait_for_function(
            "() => document.getElementById('badge-ws').textContent.includes('connected')"
        )
        ctx.close()
        browser.close()
