# OVIC EON — Edge Monitoring and Diagnostics Specification

**Document ID:** `EON-SPEC-EDGE-007`  
**Phase:** Phase 2 — System Architecture and Engineering Design (Sub-phase 2.14)  
**Status:** `DESIGNED — NOT IMPLEMENTED (Phase 2 Architecture Baseline)`  
**Target Audience:** Observability Engineers, Systems Administrators  
**Traceability:** `EON-ARCH-EDGE-001`, ADR-023  

---

## 1. Diagnostic Endpoints and Telemetry Streams

1. **Local CLI Diagnostics (`eon-cli status`):** Provides operators and robot maintenance technicians with a real-time console dashboard displaying engine states, FPS, memory usage, and dropped event counts.
2. **REST Health Endpoint (`GET /api/v1/system/health`):** Returns high-level operational health for host robot dashboard integration.
3. **Structured Journald Logging:** All logs are output in structured key-value format to `systemd-journald` with syslog severity levels. Raw images, audio buffers, and personally identifiable names are strictly scrubbed from log outputs.

---

## 2. Key Observability Metrics

| Metric Name | Type | Target Threshold | Alert Condition |
|---|---|---|---|
| `eon_engine_state` | Gauge | `ACTIVE` (2) | State is `FAULTED` (6) or `DEGRADED` (4) |
| `eon_event_drop_count` | Counter | 0 drops | $\gt 10\text{ drops/sec}$ over 5 seconds |
| `eon_ipc_latency_ms` | Histogram | $p_{99} \le 0.5\text{ ms}$ | $p_{99} \gt 5.0\text{ ms}$ |
| `eon_memory_rss_bytes` | Gauge | $\le 2048\text{ MB}$ | Memory reaches `MemoryHigh` (1800 MB) |
| `eon_sensor_fps` | Gauge | $\ge 15.0\text{ FPS}$ | FPS drops below 5.0 for $> 3\text{ seconds}$ |
