# OVIC EON — Cloud API Gateway Specification

**Document ID:** `EON-SPEC-CLD-002`  
**Phase:** Phase 2 — System Architecture and Engineering Design (Sub-phase 2.15)  
**Status:** `DESIGNED — NOT IMPLEMENTED (Phase 2 Architecture Baseline)`  
**Target Audience:** Cloud Infrastructure Engineers, API Architects  
**Traceability:** `EON-ARCH-CLD-001`, ADR-024  

---

## 1. API Gateway Responsibilities

The cloud entrance point is an Envoy-based API Gateway handling edge robot connections and enterprise management clients:
- **Mutual TLS (mTLS) Termination:** Validates client certificates issued to registered robots. Unauthenticated TLS handshakes are terminated immediately.
- **Dynamic Rate Limiting:** Enforces token bucket rate limits per robot (e.g., max 10 sync requests per minute, 50 KB/s telemetry bandwidth).
- **Tenant Routing:** Routes incoming payloads to tenant-isolated microservices based on the verified tenant claim in the robot certificate.

---

## 2. Gateway Endpoints

| Route | Protocol | Auth | Purpose |
|---|---|---|---|
| `/api/v1/sync/events` | HTTPS POST / gRPC | mTLS (Robot Cert) | Ingests queued edge context sync events |
| `/api/v1/fleet/heartbeat` | HTTPS POST | mTLS (Robot Cert) | Lightweight telemetry and status ping |
| `/api/v1/ota/manifest` | HTTPS GET | mTLS (Robot Cert) | Checks for signed firmware/model updates |
| `/api/v1/admin/tenants` | HTTPS REST | OAuth 2.0 (JWT) | Multi-tenant organization administration |
