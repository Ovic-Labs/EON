# OVIC EON — API Endpoint Catalog

**Document ID:** `EON-SPEC-API-001`  
**Phase:** Phase 2 — System Architecture and Engineering Design  
**Sub-phase:** 2.9 — Design API Architecture  
**Status:** Approved Engineering Architecture Specification  
**Version:** 1.0.0  
**Classification:** Technical Architecture Specification  
**Document Owner:** Principal Software Architect  
**Related Documents:**
- `docs/architecture/API_ARCHITECTURE.md` (`EON-ARCH-API-001`)

---

## 1. Executive Summary

This specification formalizes the public REST endpoints and WebSocket channels exposed by the EON API server (`/api/v1/`).

---

## 2. Master Endpoint Catalog

```text
+=======================================================================================+
| Method & Path                 | Auth Required | Role       | Purpose & Response Schema|
+=======================================================================================+
| GET  /api/v1/health           | Optional      | Public     | System health status     |
| GET  /api/v1/ready            | Optional      | Public     | Kubernetes readiness ping|
| GET  /api/v1/metrics          | Bearer Token  | Operator   | Prometheus metrics export|
| GET  /api/v1/engines          | Bearer Token  | Viewer     | Engine status list       |
| GET  /api/v1/engines/{id}     | Bearer Token  | Viewer     | Engine detail & health   |
| POST /api/v1/engines/{id}/rst | Bearer Token  | Admin      | Self-healing engine reset|
| GET  /api/v1/session/current  | Bearer Token  | Operator   | Active session context   |
| POST /api/v1/session/reset    | Bearer Token  | Operator   | Reset conversational turn|
| POST /api/v1/memory/purge     | Bearer Token  | Admin      | GDPR user erasure request|
| GET  /api/v1/models           | Bearer Token  | Viewer     | Catalog of loaded models |
| POST /api/v1/config/reload    | Bearer Token  | Admin      | Hot-reload configuration |
| WS   /api/v1/events/stream    | Bearer / Key  | Operator   | Real-time event envelope |
+=======================================================================================+
```
