# OVIC EON — API Error and Reliability Contract

**Document ID:** `EON-SPEC-API-004`  
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

This specification formalizes the standard error payload schema, HTTP status code mappings, and idempotency mechanisms for EON APIs.

---

## 2. Standardized Error Response Schema

Every 4xx and 5xx HTTP response returns a standardized JSON object conforming to RFC 7807 (Problem Details):

```json
{
  "type": "https://eon.oviclabs.com/errors/invalid_request",
  "title": "Invalid Request Payload",
  "status": 400,
  "detail": "Field 'valence' must be between -1.0 and 1.0",
  "instance": "/api/v1/observations",
  "error_code": "EON_ERR_SCHEMA_VALIDATION",
  "request_id": "req_8a7b6c5d-4e3f-2a1b",
  "timestamp": "2026-11-23T19:00:00Z"
}
```

### HTTP Status Code Mappings
- `200 OK`: Request succeeded.
- `202 Accepted`: Command enqueued for asynchronous processing.
- `400 Bad Request`: Payload validation failed.
- `401 Unauthorized`: Missing or invalid API key / Bearer token.
- `403 Forbidden`: Insufficient RBAC role privileges.
- `404 Not Found`: Resource or engine ID not found.
- `429 Too Many Requests`: Rate limit threshold exceeded.
- `500 Internal Error`: Isolated runtime exception; internal details scrubbed.
- `503 Service Unavailable`: Subsystem degraded or undergoing recovery.
