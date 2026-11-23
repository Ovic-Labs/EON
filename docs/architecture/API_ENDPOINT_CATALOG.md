# OVIC EON — API Endpoint Catalog Specification

**Document ID:** `EON-SPEC-API-001`  
**Phase:** Phase 2 — System Architecture and Engineering Design  
**Sub-phase:** 2.9 — Design API Architecture  
**Status:** Approved Engineering Architecture Specification  
**Version:** 2.0.0 (Reconciled Baseline)  
**Classification:** Technical Architecture Specification  
**Document Owner:** Principal Software Architect  
**Related Documents:**  
- `docs/architecture/API_ARCHITECTURE.md` (`EON-ARCH-API-001`)  
- `docs/architecture/API_AUTHENTICATION_AND_AUTHORIZATION.md` (`EON-SPEC-API-002`)  
- `docs/architecture/API_SECURITY.md` (`EON-POL-API-001`)  
- `docs/architecture/API_ERROR_AND_RELIABILITY_CONTRACT.md` (`EON-SPEC-API-004`)  

---

## 1. Executive Summary & Inventory Reconciliation

This specification formalizes the public REST endpoints and WebSocket channels exposed by the EON API server (`/api/v1/`).

> [!IMPORTANT]
> **RECONCILED BASELINE NOTICE:**  
> The authoritative EON API architecture comprises exactly **11 REST endpoints and 1 WebSocket streaming channel** (12 API interfaces total). Earlier summary references mentioning 24 REST endpoints and 4 WebSocket channels represented an unreconciled projection. This catalog constitutes the definitive, implementation-ready architectural inventory.
>
> **Implementation Boundary:** All endpoints specified herein are `DESIGNED — NOT IMPLEMENTED (Phase 2 Architecture Specification Baseline)`. Production runtime endpoints are not implemented within Phase 2.

---

## 2. Master Endpoint Inventory Matrix

```text
+==================================================================================================================+
| Method & Path                 | Transport | Auth Required | Role       | Rate Limit | Implementation Status      |
+==================================================================================================================+
| GET  /api/v1/health           | HTTP/REST | Optional      | Public     | 120 req/m  | DESIGNED — NOT IMPLEMENTED |
| GET  /api/v1/ready            | HTTP/REST | Optional      | Public     | 120 req/m  | DESIGNED — NOT IMPLEMENTED |
| GET  /api/v1/metrics          | HTTP/REST | Bearer / Key  | Operator   | 60 req/m   | DESIGNED — NOT IMPLEMENTED |
| GET  /api/v1/engines          | HTTP/REST | Bearer / Key  | Viewer     | 60 req/m   | DESIGNED — NOT IMPLEMENTED |
| GET  /api/v1/engines/{id}     | HTTP/REST | Bearer / Key  | Viewer     | 60 req/m   | DESIGNED — NOT IMPLEMENTED |
| POST /api/v1/engines/{id}/reset| HTTP/REST | Bearer / Key  | Admin      | 10 req/m   | DESIGNED — NOT IMPLEMENTED |
| GET  /api/v1/session/current  | HTTP/REST | Bearer / Key  | Operator   | 60 req/m   | DESIGNED — NOT IMPLEMENTED |
| POST /api/v1/session/reset    | HTTP/REST | Bearer / Key  | Operator   | 10 req/m   | DESIGNED — NOT IMPLEMENTED |
| POST /api/v1/memory/purge     | HTTP/REST | Bearer / Key  | Admin      | 5 req/m    | DESIGNED — NOT IMPLEMENTED |
| GET  /api/v1/models           | HTTP/REST | Bearer / Key  | Viewer     | 30 req/m   | DESIGNED — NOT IMPLEMENTED |
| POST /api/v1/config/reload    | HTTP/REST | Bearer / Key  | Admin      | 5 req/m    | DESIGNED — NOT IMPLEMENTED |
| WS   /api/v1/events/stream    | WebSocket | Bearer / Key  | Operator   | Max 5 conn | DESIGNED — NOT IMPLEMENTED |
+==================================================================================================================+
```

---

## 3. Exhaustive Endpoint Specifications

### 3.1 `GET /api/v1/health`
- **Method / Transport:** `GET` (HTTP/1.1, HTTP/2)
- **Path:** `/api/v1/health`
- **Purpose:** System liveness and high-level health probe for container orchestrators and supervisory watchdog timers.
- **Authentication:** Optional (accessible without credentials if configured for local container healthchecks).
- **Authorization:** `Public`
- **Request Contract:**
  - Headers: Standard HTTP headers.
  - Query Params: None.
  - Body: None.
- **Response Contract (200 OK):**
  ```json
  {
    "status": "HEALTHY",
    "timestamp": "2026-11-23T12:00:00.000000Z",
    "uptime_seconds": 3612.45,
    "version": "0.1.0"
  }
  ```
- **Error Conditions:**
  - `503 Service Unavailable`: Internal kernel supervisor or event bus thread deadlocked.
- **Versioning:** URL path `v1`.
- **Rate Limit:** 120 req/minute per IP.
- **Implementation Status:** `DESIGNED — NOT IMPLEMENTED`.

---

### 3.2 `GET /api/v1/ready`
- **Method / Transport:** `GET` (HTTP/1.1, HTTP/2)
- **Path:** `/api/v1/ready`
- **Purpose:** Readiness probe verifying that all mandatory startup dependencies and configured intelligence engines have achieved operational state.
- **Authentication:** Optional.
- **Authorization:** `Public`
- **Request Contract:**
  - Headers: Standard HTTP headers.
  - Body: None.
- **Response Contract (200 OK):**
  ```json
  {
    "ready": true,
    "engines_ready": 7,
    "engines_total": 7,
    "bus_online": true
  }
  ```
- **Error Conditions:**
  - `503 Service Unavailable`: Core runtime still initializing, or required engines degraded/failed.
- **Versioning:** URL path `v1`.
- **Rate Limit:** 120 req/minute per IP.
- **Implementation Status:** `DESIGNED — NOT IMPLEMENTED`.

---

### 3.3 `GET /api/v1/metrics`
- **Method / Transport:** `GET` (HTTP/1.1, HTTP/2)
- **Path:** `/api/v1/metrics`
- **Purpose:** Prometheus / OpenTelemetry format metrics scrape endpoint exposing queue depths, latencies, drop counts, and engine transition metrics.
- **Authentication:** Mandatory (`Bearer <token>` or `X-API-Key`).
- **Authorization:** `Operator`, `Admin`
- **Request Contract:**
  - Headers: `Authorization: Bearer <jwt>` or `X-API-Key: <key>`.
- **Response Contract (200 OK):**
  - Content-Type: `text/plain; version=0.0.4; charset=utf-8`
  - Textual Prometheus exposition format (e.g., `eon_bus_published_events_total`, `eon_bus_dropped_events_total`, `eon_engine_status`).
- **Error Conditions:**
  - `401 Unauthorized`: Missing or invalid credentials.
  - `403 Forbidden`: Insufficient role permissions (`Viewer` cannot read metrics).
- **Versioning:** URL path `v1`.
- **Rate Limit:** 60 req/minute.
- **Implementation Status:** `DESIGNED — NOT IMPLEMENTED`.

---

### 3.4 `GET /api/v1/engines`
- **Method / Transport:** `GET` (HTTP/1.1, HTTP/2)
- **Path:** `/api/v1/engines`
- **Purpose:** Enumerate all registered intelligence engines, their operational health states, version numbers, and uptime.
- **Authentication:** Mandatory (`Bearer <token>` or `X-API-Key`).
- **Authorization:** `Viewer`, `Operator`, `Admin`
- **Request Contract:**
  - Headers: `Authorization: Bearer <jwt>`.
- **Response Contract (200 OK):**
  ```json
  {
    "engines": [
      {
        "engine_id": "ERS",
        "engine_name": "Emotion Recognition System",
        "lifecycle_state": "RUNNING",
        "operational_health": "ACTIVE",
        "version": "0.1.0",
        "uptime_seconds": 1240.2
      }
    ]
  }
  ```
- **Error Conditions:**
  - `401 Unauthorized`: Missing or expired token.
  - `403 Forbidden`: Lacking read capability.
- **Versioning:** URL path `v1`.
- **Rate Limit:** 60 req/minute.
- **Implementation Status:** `DESIGNED — NOT IMPLEMENTED`.

---

### 3.5 `GET /api/v1/engines/{id}`
- **Method / Transport:** `GET` (HTTP/1.1, HTTP/2)
- **Path:** `/api/v1/engines/{id}`
- **Purpose:** Retrieve comprehensive diagnostics for a single engine, including internal 11-state FSM state, resource consumption (CPU/RAM/VRAM), and topic subscriptions.
- **Authentication:** Mandatory (`Bearer <token>` or `X-API-Key`).
- **Authorization:** `Viewer`, `Operator`, `Admin`
- **Request Contract:**
  - Path Param: `id` (one of `ERS`, `EMS`, `ERE`, `PSE`, `SIE`, `ERG`, `HBU`).
- **Response Contract (200 OK):**
  ```json
  {
    "engine_id": "EMS",
    "lifecycle_state": "RUNNING",
    "operational_health": "ACTIVE",
    "memory_rss_bytes": 104857600,
    "cpu_percent": 3.4,
    "error_rate_5m": 0.0,
    "subscribed_topics": ["eon.ers.*", "eon.sie.*"]
  }
  ```
- **Error Conditions:**
  - `401 Unauthorized`: Authentication failure.
  - `404 Not Found`: Unknown engine identifier.
- **Versioning:** URL path `v1`.
- **Rate Limit:** 60 req/minute.
- **Implementation Status:** `DESIGNED — NOT IMPLEMENTED`.

---

### 3.6 `POST /api/v1/engines/{id}/reset` (Alias: `/rst`)
- **Method / Transport:** `POST` (HTTP/1.1, HTTP/2)
- **Path:** `/api/v1/engines/{id}/reset` (with legacy shorthand alias `/rst`)
- **Purpose:** Trigger a controlled restart and recovery sequence for a DEGRADED or FAULTED engine.
- **Authentication:** Mandatory (`Bearer <token>` or `X-API-Key`).
- **Authorization:** `Admin`
- **Request Contract:**
  - Path Param: `id` (Target engine ID).
  - Body:
    ```json
    {
      "reason": "manual_operator_reset",
      "timeout_seconds": 5.0
    }
    ```
- **Response Contract (200 OK):**
  ```json
  {
    "engine_id": "ERS",
    "transition": "RECOVERY_INITIATED",
    "previous_state": "DEGRADED",
    "current_state": "INITIALIZING"
  }
  ```
- **Error Conditions:**
  - `401 Unauthorized`, `403 Forbidden` (non-admin).
  - `404 Not Found`: Unknown engine ID.
  - `409 Conflict`: Engine currently in valid `RUNNING` or `STOPPING` state.
- **Versioning:** URL path `v1`.
- **Rate Limit:** 10 req/minute.
- **Implementation Status:** `DESIGNED — NOT IMPLEMENTED`.

---

### 3.7 `GET /api/v1/session/current`
- **Method / Transport:** `GET` (HTTP/1.1, HTTP/2)
- **Path:** `/api/v1/session/current`
- **Purpose:** Inspect active human-robot interaction session context, turn counts, and continuous presence tracking.
- **Authentication:** Mandatory (`Bearer <token>` or `X-API-Key`).
- **Authorization:** `Operator`, `Admin`
- **Request Contract:**
  - Headers: Standard authentication headers.
- **Response Contract (200 OK):**
  ```json
  {
    "session_id": "sess_89f02a",
    "subject_id": "usr_491a",
    "turn_count": 4,
    "session_duration_seconds": 182.1,
    "last_interaction_timestamp": "2026-11-23T12:05:14.120000Z"
  }
  ```
- **Error Conditions:**
  - `401 Unauthorized`, `403 Forbidden`.
  - `404 Not Found`: No active interaction session.
- **Versioning:** URL path `v1`.
- **Rate Limit:** 60 req/minute.
- **Implementation Status:** `DESIGNED — NOT IMPLEMENTED`.

---

### 3.8 `POST /api/v1/session/reset`
- **Method / Transport:** `POST` (HTTP/1.1, HTTP/2)
- **Path:** `/api/v1/session/reset`
- **Purpose:** Explicitly terminate the active conversation session, flush working memory, and reset dialogue state to idle.
- **Authentication:** Mandatory (`Bearer <token>` or `X-API-Key`).
- **Authorization:** `Operator`, `Admin`
- **Request Contract:**
  - Body:
    ```json
    {
      "reason": "user_departed",
      "flush_working_memory": true
    }
    ```
- **Response Contract (200 OK):**
  ```json
  {
    "previous_session_id": "sess_89f02a",
    "status": "TERMINATED",
    "timestamp": "2026-11-23T12:06:00.000000Z"
  }
  ```
- **Error Conditions:**
  - `401 Unauthorized`, `403 Forbidden`.
- **Versioning:** URL path `v1`.
- **Rate Limit:** 10 req/minute.
- **Implementation Status:** `DESIGNED — NOT IMPLEMENTED`.

---

### 3.9 `POST /api/v1/memory/purge`
- **Method / Transport:** `POST` (HTTP/1.1, HTTP/2)
- **Path:** `/api/v1/memory/purge`
- **Purpose:** Execute a verifiable GDPR / CCPA right-to-be-forgotten data erasure request by initiating cryptographic shredding of the subject's Data Encryption Key (DEK).
- **Authentication:** Mandatory (`Bearer <token>` or `X-API-Key`).
- **Authorization:** `Admin`
- **Request Contract:**
  - Body:
    ```json
    {
      "subject_id": "usr_491a",
      "confirmation_token": "CONFIRM_DELETE_usr_491a"
    }
    ```
- **Response Contract (200 OK):**
  ```json
  {
    "subject_id": "usr_491a",
    "status": "KEY_DESTROYED",
    "erasure_method": "CRYPTOGRAPHIC_SHREDDING",
    "shredded_key_id": "dek_usr_491a",
    "mathematical_unrecoverability_guaranteed": true,
    "timestamp": "2026-11-23T12:07:00.000000Z"
  }
  ```
- **Error Conditions:**
  - `401 Unauthorized`, `403 Forbidden` (strictly Admin).
  - `400 Bad Request`: Missing or invalid confirmation token.
  - `404 Not Found`: Subject ID not recognized in keystore.
- **Versioning:** URL path `v1`.
- **Rate Limit:** 5 req/minute.
- **Implementation Status:** `DESIGNED — NOT IMPLEMENTED`.

---

### 3.10 `GET /api/v1/models`
- **Method / Transport:** `GET` (HTTP/1.1, HTTP/2)
- **Path:** `/api/v1/models`
- **Purpose:** Enumerate loaded neural network model adapters, execution backends (ONNX, TensorRT, PyTorch), hardware devices, and memory consumption.
- **Authentication:** Mandatory (`Bearer <token>` or `X-API-Key`).
- **Authorization:** `Viewer`, `Operator`, `Admin`
- **Request Contract:** Standard authentication headers.
- **Response Contract (200 OK):**
  ```json
  {
    "models": [
      {
        "model_id": "ser_distilhubert_v1",
        "engine": "ERS",
        "backend": "ONNX_RUNTIME",
        "device": "CPU",
        "memory_allocated_bytes": 94371840,
        "is_fallback": false
      }
    ]
  }
  ```
- **Error Conditions:**
  - `401 Unauthorized`, `403 Forbidden`.
- **Versioning:** URL path `v1`.
- **Rate Limit:** 30 req/minute.
- **Implementation Status:** `DESIGNED — NOT IMPLEMENTED`.

---

### 3.11 `POST /api/v1/config/reload`
- **Method / Transport:** `POST` (HTTP/1.1, HTTP/2)
- **Path:** `/api/v1/config/reload`
- **Purpose:** Trigger safe hot-reload of non-breaking configuration values (logging levels, timeout thresholds, rate limits) without restarting the kernel.
- **Authentication:** Mandatory (`Bearer <token>` or `X-API-Key`).
- **Authorization:** `Admin`
- **Request Contract:**
  - Body:
    ```json
    {
      "config_file": "/etc/eon/runtime.yaml"
    }
    ```
- **Response Contract (200 OK):**
  ```json
  {
    "status": "RELOADED",
    "applied_changes": ["logging.level: DEBUG -> INFO"],
    "timestamp": "2026-11-23T12:08:00.000000Z"
  }
  ```
- **Error Conditions:**
  - `400 Bad Request`: Schema validation failure in new configuration.
  - `401 Unauthorized`, `403 Forbidden`.
- **Versioning:** URL path `v1`.
- **Rate Limit:** 5 req/minute.
- **Implementation Status:** `DESIGNED — NOT IMPLEMENTED`.

---

### 3.12 `WS /api/v1/events/stream`
- **Method / Transport:** `WebSocket` (RFC 6455 over WSS/WS)
- **Path:** `/api/v1/events/stream`
- **Purpose:** Full-duplex real-time streaming channel for subscribing to EventBroker topics (`CloudEvents` v1.0.2 / `EON-SPEC-ENV-001` v2.0.0 envelopes).
- **Authentication:** Mandatory (Query param `?token=<jwt>` or initial handshake header).
- **Authorization:** `Operator`, `Admin`
- **Handshake Protocol:**
  - Client initiates WebSocket upgrade with Bearer token.
  - Upon acceptance, client sends subscription frame:
    ```json
    {
      "action": "subscribe",
      "topics": ["eon.perception.face.*", "eon.lifecycle.*"]
    }
    ```
- **Stream Message Contract (Server -> Client):**
  - JSON-serialized `EventEnvelope` frame (`specversion: "2.0.0"`, `type`, `source`, `id`, `time`, `data`).
- **Connection Caps & Throttling:**
  - Maximum 5 concurrent WebSocket connections system-wide to prevent memory starvation on edge compute boards.
- **Error Conditions:**
  - `WS Close Code 4401`: Unauthorized / invalid token.
  - `WS Close Code 4429`: Connection pool exhausted (exceeds 5 concurrent streams).
- **Versioning:** URL path `v1`.
- **Implementation Status:** `DESIGNED — NOT IMPLEMENTED`.
