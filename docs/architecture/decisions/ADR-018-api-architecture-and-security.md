# ADR-018: API Architecture, Technology Selection, and RBAC Security

**Document ID:** `EON-ADR-018`  
**Status:** Approved  
**Date:** 2026-11-23  
**Deciders:** Principal Software Architect, Founder, Engineering Leads  
**Related Requirements:** `EON-FR-045`, `EON-NFR-050`, `EON-SRS-105`, `EON-ARCH-API-001`

---

## 1. Context
External tools (robot fleet management, teleoperation consoles, administrative dashboards) require standard network interfaces to inspect robot emotional state, query system health, and reload configuration. However, exposing unrestricted internal interfaces over the network introduces critical security risks.

## 2. Problem
What API technologies, protocols, and security controls should OVIC EON adopt to expose administrative, diagnostic, and streaming interfaces without compromising edge performance or security?

## 3. Decision
Adopt a **FastAPI-Based REST and WebSocket API Architecture with RBAC**:
1. **FastAPI Framework:** Use FastAPI for OpenAPI-compliant REST endpoints and native asynchronous WebSocket handlers.
2. **Dual-Channel Protocol:** REST for transactional operations (health, configuration reload, session resets); WebSockets for streaming high-frequency event envelopes.
3. **Role-Based Access Control (RBAC):** Three explicit roles (`Viewer`, `Operator`, `Admin`) enforced via JWT Bearer tokens and machine API keys.
4. **RFC 7807 Error Contract:** Standardize all error responses to RFC 7807 Problem Details with unique `request_id` correlation tracking and internal stack trace redaction.
5. **Localhost Binding Default:** API server binds strictly to `127.0.0.1` by default to prevent unauthorized external network exposure on robot Wi-Fi networks unless explicitly configured.

## 4. Alternatives Considered
1. **gRPC Interface:** High performance, but requires protocol buffer compilation and lacks native web browser support without heavy Envoy gRPC-Web proxying.
2. **Custom Socket Server:** Avoided; writing custom HTTP/WS parsers is error-prone and lacks standard OpenAPI documentation tooling.

## 5. Consequences
- **Positive:** Interactive Swagger documentation; type-safe request/response validation using existing Pydantic schemas; native async event loop integration.
- **Negative:** Adds ASGI/FastAPI dependencies to Layer 9.

## 6. Risks and Mitigations
- **Risk:** High network connection counts exhausting edge memory.
- **Mitigation:** Strict WebSocket connection caps (maximum 5 concurrent streams) and token-bucket rate limiting (60 req/min).
