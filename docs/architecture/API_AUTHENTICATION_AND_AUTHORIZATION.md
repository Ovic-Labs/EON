# OVIC EON — API Authentication and Authorization Specification

**Document ID:** `EON-SPEC-API-002`  
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

This specification establishes the authentication schemes, token lifecycles, and Role-Based Access Control (RBAC) governing access to EON network APIs.

---

## 2. Authentication Schemes

1. **Static API Keys:** For machine-to-machine local robot communication (`X-API-Key` header). Validated against `/etc/eon/api_keys.json` (SHA-256 hashed).
2. **JWT Bearer Tokens:** For human operators and remote web consoles (`Authorization: Bearer <token>`). Tokens signed via HMAC-SHA256 (`HS256`) with 1-hour expiration.

---

## 3. Role-Based Access Control (RBAC) Matrix

```text
+=======================================================================================+
| Role       | Permitted Operations                                                     |
+=======================================================================================+
| `Viewer`   | Read-only health, engine status, loaded model catalog.                   |
| `Operator` | Viewer permissions + session reset, metrics read, WebSocket stream tap.  |
| `Admin`    | Operator permissions + configuration reload, engine restarts, GDPR purge.|
+=======================================================================================+
```
