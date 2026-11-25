# ERS API Reference

Interactive Swagger and ReDoc schemas are served at `/docs`, `/redoc`, and `/openapi.json` when running `eon-ers-live` or `uvicorn eon_ers.live.server:create_live_app --factory`.

## System Endpoints
- `GET /health` — Process & engine liveness status.
- `GET /ready` — Readiness probe separating runtime liveness (`ready`) from empirically validated classification (`qualified_inference_ready`).
- `GET /version` — Engine, API, schema, and WebSocket protocol versions.
- `GET /capabilities` — Active modalities, auth status, byte/frame limits, readiness.
- `GET /metrics` — JSON telemetry or Prometheus text format (`?format=prometheus`).

## Versioned REST API (`/api/v1/*`)
When `ERSConfig(require_api_auth=True)` is active, pass `X-API-Key: <key>` or `Authorization: Bearer <key>`.

### Models
- `GET /api/v1/models` — List discovered registry models, SHA-256 checksums, qualification state.
- `GET /api/v1/models/{model_id}` — Detailed model entry & validation record.
- `GET /api/v1/models/{model_id}/status` — Activation eligibility and revocation status.
- `POST /api/v1/models/{model_id}/activate` — Activate model (fails with HTTP 409 unless `MODEL_VALIDATED`).

### Analysis
- `POST /api/v1/analyze/image` & `POST /api/v1/analyze/facial` — Facial expression observation (`ProcessObservationRequest`).
- `POST /api/v1/analyze/audio` & `POST /api/v1/analyze/vocal` — Vocal affect + VAD observation (`ProcessObservationRequest`).
- `POST /api/v1/analyze/text` — Distinct UTF-8 text affect & `text_sentiment` (`TextAnalyzeRequest`).
- `POST /api/v1/analyze/video` — Bounded video analysis job (`VideoAnalyzeRequest`).
- `GET /api/v1/analyze/video/{job_id}` & `DELETE /api/v1/analyze/video/{job_id}` — Poll or cancel video analysis.
- `POST /api/v1/analyze/multimodal` — 1-, 2-, or 3-modality fusion (`MultimodalAnalyzeRequest`).

### Live Sessions & Consent
- `POST /api/v1/live/sessions`, `GET /api/v1/live/sessions`, `GET /api/v1/live/sessions/{session_id}`
- `POST /api/v1/live/sessions/{session_id}/pause`, `POST /api/v1/live/sessions/{session_id}/resume`
- `DELETE /api/v1/live/sessions/{session_id}`
- `WS /api/v1/live/sessions/{session_id}/stream` (also `/ws/live/{session_id}`, `/ws/stream/{session_id}`)
- `POST /api/v1/consent`, `GET /api/v1/consent/{session_id}`, `DELETE /api/v1/consent/{session_id}`

### Diagnostics, Datasets & Evaluation
- `GET /api/v1/diagnostics` — CPU%, RSS MB, ORT providers, latency telemetry.
- `GET /api/v1/datasets` — Registered provenance & license ledger.
- `GET /api/v1/evaluation/reports` — Validation & calibration reports.

## Backward-Compatible Legacy Routes (`/api/*`)
Retained for existing integrations: `/api/health`, `/api/models`, `/api/devices`, `/api/telemetry/{session_id}`, `/api/consent/register`, `/api/consent/revoke`, `/api/consent/status/{session_id}`, `/api/process/unimodal`, `/api/process/frame`, `/api/process/audio`, `/api/process/multimodal`, `/api/session/reset`.
