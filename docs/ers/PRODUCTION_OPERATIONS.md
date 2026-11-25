# Production Operations & Monitoring Runbook

## Probes & Telemetry
- **Liveness (`/health`):** Confirm engine process state (`RUNNING` / `DEGRADED`).
- **Readiness (`/ready`):** Separately verify `ready` vs `qualified_inference_ready` (validated models loaded).
- **Metrics (`/metrics?format=prometheus`):** Export `eon_ers_processed_total`, `eon_ers_errors_total`, `eon_ers_dropped_frames_total`, `eon_ers_ws_active_connections`, `eon_ers_memory_rss_mb`, and `eon_ers_latency_p95_ms`.
- **Structured Logging:** Enable `configure_structured_logging()` for single-line redacted JSON logs carrying `request_id` and `session_id` correlation context.

## Incident Response & Key Rotation
1. **Model Defect:** Immediately call `ModelRegistry.revoke_model(model_id, reason)` to prevent activation.
2. **Signing Key Compromise:** Call `TrustedKeyRegistry.rotate_key(old_key_id, new_key_id, new_pem_bytes)` and re-sign verified model proofs offline.
3. **API Key Leak:** Revoke key via `APIKeyAuthManager.revoke_key(key_id)` and issue a replacement key.
4. **Backup:** Back up only verified `models/*.json`, `*.onnx`, `*.validation.json`, public Ed25519 keys, and nginx/deploy config outside raw media paths (default raw media retention is zero).
