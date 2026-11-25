# OVIC EON — Phase 3.3 Browser & Hardware Qualification Report

**Date:** 2026-11-25  
**Repository:** `https://github.com/Ovic-Labs/EON`  
**Branch:** `main`  
**Preview URL:** `http://127.0.0.1:8000/` (local preview only; no public deployment)  

---

## 1. Qualification Acceptance Table

| Area | Status | Evidence & Scope Boundary |
| --- | --- | --- |
| Dashboard startup | **PASS** | `eon-ers-live --host 127.0.0.1 --port 8000` (`parse_args([])` defaults `127.0.0.1:8000`) and `uvicorn eon_ers.live.server:create_live_app --factory` start cleanly in CPU mode (`http://127.0.0.1:8000/`). |
| Browser rendering | **PASS** | Verified in real Chrome (`1440x900` desktop & `390x844` mobile) via Playwright: zero uncaught `pageerror`, zero server `5xx`, inline `data:,` icon prevents `/favicon.ico` 404, zero horizontal scroll overflow. |
| API connectivity | **PASS** | `/health`, `/ready`, `/version`, `/capabilities`, `/metrics`, `/api/models`, `/api/devices`, `/api/v1/*`, `/api/consent/*` verified over live TCP HTTP. |
| WebSocket | **PASS** | Live `/ws/live/{session_id}` verified across `auth`, `init`, `heartbeat`, `media_state`, `frame`, `audio`, `revoke`, manual disconnect (`state.ws.close()`), and UI reconnect (`#btn-ws-reconnect`). |
| Consent lifecycle | **PASS** | No hardcoded consent token; empty consent rejected; explicit grant activates capture; revocation is terminal (`HTTP 409` on re-register); **New Session** and full page reload cleanly reset consent. |
| Camera automation | **PASS (SIMULATED)** | Playwright Chrome (`--use-fake-device-for-media-stream --use-fake-ui-for-media-stream`) verified `getUserMedia` video track acquisition, `video.play()` (`readyState >= 2`, `640x480`), `2 FPS` JPEG frame streaming over WS, live `Facial` observation updates, `/api/devices` `camera_active=true`, and clean `Stop Webcam` teardown (`camera_active=false`). |
| Physical camera | **BLOCKED (HEADLESS SANDBOX)** | Windows host detects `Camera AI Effect Opt-in` (`enumerateDevices()` sees `videoinput`), but unattended headless Chrome denies OS media prompts (`NotAllowedError`). UI accurately displays `"Permission Denied"` and site-permission instructions. Requires interactive desktop operator testing. |
| Microphone automation | **PASS (SIMULATED)** | Playwright Chrome (`[SIMULATED_MEDIA]`) verified `getUserMedia` audio acquisition, `AudioContext` creation, `ScriptProcessorNode` processing, `16000 Hz` `downsampleTo16k()` resampling, bounded PCM chunk buffering, WS `audio` frames, and full `Stop Microphone` node/track teardown. |
| Physical microphone | **BLOCKED (HEADLESS SANDBOX)** | Windows host detects `Microphone (Realtek(R) Audio)` (`enumerateDevices()` sees `audioinput`), but unattended headless Chrome denies interactive OS microphone prompts (`NotAllowedError`). Requires interactive desktop operator testing. |
| Privacy and security | **PASS** | `EON_ERS_API_AUTH=true` + `X-API-Key` verified fail-closed (`401`) then authenticated in Settings UI (`WS: connected`); query-string secrets rejected; `pip-audit --desc` clean (`0` known CVEs); zero raw media retention on disk. |
| CPU-only operation | **PASS** | Executes on `CPUExecutionProvider` (`onnxruntime`, `num_threads=4`, bounded `max_sessions=256`, bounded `max_ws_queue_size=32`, per-op `processing_timeout_seconds=10.0`). |
| Scientific model validation | **BLOCKED** | Loaded baseline models remain `UNVALIDATED_BASELINE` (`MODEL_EXPERIMENTAL`, `is_validated=false`, `activated=false`, `HTTP 409` on activation). No external datasets (`AffectNet`, `RAF-DB`, `FER2013`, `RAVDESS`, `CREMA-D`) are present. |
| Production deployment | **NOT DEPLOYED** | No public URL deployed; hardened container/Nginx configuration (`Dockerfile`, `docker-compose.yml`, `deploy/nginx.conf`) verified via CI `docker-build`. |

---

## 2. Simulated vs. Physical Hardware Separation

1. **Automated Simulated Browser Verification (`test_dashboard_browser.py`):**
   - Explicitly marked `[SIMULATED_MEDIA]` using Chromium fake media stream flags (`--use-fake-device-for-media-stream --use-fake-ui-for-media-stream`).
   - Proves browser UI wiring, `getUserMedia` Promise handling, `<video>` playback, `canvas` JPEG encoding, `AudioContext` -> `downsampleTo16k()` PCM encoding, WS backpressure/transmission, backend pipeline execution, and device track cleanup.
   - **Must not** be treated as proof of physical webcam sensor optics or physical room microphone acoustics.
2. **Real Non-Fake-Media Chrome Probe (`http://127.0.0.1:8000/`):**
   - `navigator.mediaDevices.enumerateDevices()` reported host `audioinput`, `videoinput`, and `audiooutput` entries.
   - Calling `Start Webcam` without fake-media overrides in headless Chrome triggered `NotAllowedError`, validating the dashboard's fail-closed `"Permission Denied"` UI badge and recovery instructions.

---

## 3. Manual Operator Test Instructions (Physical Webcam & Microphone)

1. Ensure no stale server occupies port `8000`, then launch from repository root:
   ```powershell
   eon-ers-live --host 127.0.0.1 --port 8000
   ```
2. Open `http://127.0.0.1:8000/` in desktop **Google Chrome** or **Microsoft Edge**.
3. Verify top badges show `Engine: HEALTHY`, `Qualification: UNVALIDATED_BASELINE`, and `Consent: not granted`.
4. Navigate to **2. Live ERS**, enter a custom consent token (e.g., `operator-test-01`), and click **Grant Consent**. Verify `Consent: ACTIVE` and `WS: connected`.
5. Click **Start Webcam**, click **Allow** on the browser camera prompt, select `Camera AI Effect Opt-in` if multiple cameras exist, and confirm your live video feed plays smoothly alongside updating **Live Observations** (`is_definitive_claim = False`).
6. Click **Start Microphone**, click **Allow** on the browser microphone prompt, speak briefly, and verify the **Microphone RMS Energy Level** bar responds above `(Silence)` to `(Active)`.
7. Verify `GET http://127.0.0.1:8000/api/devices` reports `camera_active: true` / `microphone_active: true` while actively streaming.
8. Click **Stop Webcam** and **Stop Microphone**; verify hardware indicator LEDs turn off and `/api/devices` flips back to inactive.
9. Click **Revoke Consent**; verify capture buttons lock cleanly (`Consent: REVOKED (Terminal Session)`), and verify clicking **Grant Consent** again on the same session ID returns `HTTP 409 Conflict`. Click **New Session** to create a clean session.
