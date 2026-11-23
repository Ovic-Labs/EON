# OVIC EON — API Architecture Specification

**Document ID:** `EON-ARCH-API-001`  
**Phase:** Phase 2 — System Architecture and Engineering Design  
**Sub-phase:** 2.9 — Design API Architecture  
**Status:** Approved Engineering Architecture Specification  
**Version:** 1.0.0  
**Classification:** Technical Architecture Specification  
**Document Owner:** Principal Software Architect  
**Related Documents:**
- `docs/architecture/API_ENDPOINT_CATALOG.md` (`EON-SPEC-API-001`)
- `docs/architecture/API_AUTHENTICATION_AND_AUTHORIZATION.md` (`EON-SPEC-API-002`)
- `docs/architecture/API_SECURITY.md` (`EON-POL-API-001`)
- `docs/architecture/API_VERSIONING_AND_COMPATIBILITY.md` (`EON-SPEC-API-003`)
- `docs/architecture/API_ERROR_AND_RELIABILITY_CONTRACT.md` (`EON-SPEC-API-004`)
- `docs/architecture/decisions/ADR-018-api-architecture-and-security.md` (`EON-ADR-018`)

---

## 1. Executive Summary

This specification establishes the public and internal API architecture for OVIC EON (Layer 9 of the system architecture).

OVIC EON exposes standard network APIs using **FastAPI** for HTTP/REST services and asynchronous **WebSockets** for real-time telemetry and event streaming. The API layer bridges developer tooling, fleet management dashboards, and robot administration consoles while maintaining strict isolation from low-level sensory hardware and internal core state.

---

## 2. API Communication Technologies

```text
+=======================================================================================+
| Interface Type        | Protocol / Technology| Target Usage & Use Cases               |
+=======================================================================================+
| REST API              | HTTP/1.1 & HTTP/2    | Administrative configuration, health,  |
|                       | (FastAPI / ASGI)     | session management, and metrics polling|
+-----------------------+----------------------+----------------------------------------+
| Real-Time Streaming   | WebSockets (RFC 6455)| Low-latency event streaming, emotion   |
|                       | (FastAPI WS Handler) | trajectories, and active turn events   |
+-----------------------+----------------------+----------------------------------------+
| In-Process Python SDK | Direct Python AsyncIO| High-performance embedded integration  |
|                       | (eon.sdk.client)     | (<0.1ms dispatch; zero HTTP overhead)  |
+-----------------------+----------------------+----------------------------------------+
| Robotics Middleware   | ROS 2 Topics/Services| Standard robotic ecosystem integration |
|                       | (eon_ros2 node)      | (/eon/observations, /eon/emotions)     |
+=======================================================================================+
```
