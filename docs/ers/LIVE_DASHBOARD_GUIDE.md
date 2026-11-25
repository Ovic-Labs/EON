# Live Enterprise Dashboard Guide

Launch the backend and console:

```bash
eon-ers-live --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000/` in a desktop or mobile browser.

## Integrated 15 Views
1. **Overview:** Liveness (`/health`), Readiness (`/ready`), qualified vs baseline models, throughput, host CPU/RSS.
2. **Live ERS:** Webcam + microphone real-time capture with explicit device selection (`devicechange` refresh), browser `AudioContext` resampling to `16000 Hz`, WebSocket backpressure guard, RMS level indicator, FPS control, pause/resume, and strict consent controls (no silent auto-consent or hardcoded consent tokens).
3. **Image Analysis:** File upload testing via `POST /api/v1/analyze/image`.
4. **Audio Analysis:** WAV/PCM upload testing via `POST /api/v1/analyze/audio`.
5. **Video Analysis:** RIFF AVI (MJPEG) & animated GIF/WEBP analysis via `POST /api/v1/analyze/video`.
6. **Text Analysis:** UTF-8 sentiment & lexical-affect separation via `POST /api/v1/analyze/text`.
7. **Multimodal Analysis:** Concurrent 1/2/3-modality fusion explorer (`POST /api/v1/analyze/multimodal`).
8. **Model Registry:** Model SHA-256 inspection and guarded activation (`POST /api/v1/models/{id}/activate`; unvalidated models return `409 Conflict`).
9. **Model Evaluation:** Real `validation.json` calibration & F1 audit reports (`/api/v1/evaluation/reports`).
10. **Dataset Management:** Benchmark dataset provenance & non-commercial license register (`/api/v1/datasets`).
11. **Session Management:** Live session FSM inspection, creation, and deletion (`/api/v1/live/sessions`).
12. **API Documentation:** Direct links to `/docs`, `/redoc`, `/openapi.json`, and health/metrics endpoints.
13. **System Health:** Live CPU, RSS, ORT provider, WebSocket, and latency percentile JSON diagnostics.
14. **Settings:** Light/dark theme switcher (`localStorage`), volatile in-page `X-API-Key` (never persisted to disk or passed in WebSocket URLs), and capture resolution settings.
15. **Privacy & Consent:** Explicit consent registration (`POST /api/consent/register`), backend status check (`GET /api/consent/status/{id}`), terminal consent revocation (`POST /api/consent/revoke`, returning `409 Conflict` on attempted reactivation without starting a new session via **New Session**), verified capture telemetry (`/api/devices` & `/api/v1/devices`), and Responsible AI guarantees (`is_definitive_claim = False`).
