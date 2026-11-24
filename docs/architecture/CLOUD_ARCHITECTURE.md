# OVIC EON — Optional Cloud Architecture Specification

**Document ID:** `EON-ARCH-CLD-001`  
**Phase:** Phase 2 — System Architecture and Engineering Design (Sub-phase 2.15)  
**Status:** `DESIGNED — NOT IMPLEMENTED (Phase 2 Architecture Baseline)`  
**Target Audience:** Cloud Architects, Distributed Systems Engineers, Enterprise Integrators  
**Traceability:** PRD Section 4.5, SRS-ARCH-014, ADR-024, ADR-014, ADR-025  

---

## 1. Executive Summary and Non-Mandatory Cloud Policy

The **OVIC EON Cloud Architecture** defines the optional cloud control plane, fleet analytics, and synchronization backend for EON robotic deployments.

Crucially, this architecture adheres to three foundational mandates:
1. **Cloud is Strictly Optional:** EON Core and all seven intelligence engines run completely autonomously on edge robots. Disconnecting the internet never degrades core perception, empathy reasoning, or social interaction capabilities.
2. **Zero Mandatory External AI APIs:** The cloud backend never acts as an unvetted proxy to third-party proprietary LLMs (e.g., OpenAI, Anthropic, Gemini). Cloud services are limited to fleet management, model artifact distribution, and tenant-consented cross-robot memory synchronization.
3. **No Default Raw Media Transmission:** Raw camera images, video streams, and microphone audio recordings are **never uploaded to the cloud** by default. Only anonymized, non-reversible high-level telemetry and consented interaction metadata are synchronized.

---

## 2. Cloud System Topology

```text
+-------------------------------------------------------------------------+
|                  Robotic Edge Node (Local / Autonomous)                 |
|  - EON Core Service (ERS, EMS, ERE, PSE, SIE, ERG, HBU)                 |
|  - Local Encrypted SQLite (context.db)                                  |
|  - Edge Cloud Sync Agent (Store-and-forward queue)                      |
+-------------------------------------------------------------------------+
                                    |
                    (TLS 1.3 / mTLS / WireGuard VPN)
                                    v
+-------------------------------------------------------------------------+
|                      OVIC Cloud Platform (Optional)                     |
|                                                                         |
|  +---------------------------+       +-------------------------------+  |
|  |     API Gateway / Envoy   | <---> |   Identity & Access (OAuth2)  |  |
|  | (Rate limiting, mTLS auth)|       | (Per-tenant & per-robot certs)|  |
|  +---------------------------+       +-------------------------------+  |
|               |                                      |                  |
|               v                                      v                  |
|  +---------------------------+       +-------------------------------+  |
|  | Fleet Management Service  |       | Cross-Robot Context Sync      |  |
|  | (OTA updates, diagnostics)|       | (Vector clocks, CRDT sync)    |  |
|  +---------------------------+       +-------------------------------+  |
|               |                                      |                  |
|               v                                      v                  |
|  +---------------------------+       +-------------------------------+  |
|  | Time-Series Telemetry DB  |       | Encrypted Multi-Tenant DB     |  |
|  | (TimescaleDB / ClickHouse)|       | (PostgreSQL + Row-Level Sec)  |  |
|  +---------------------------+       +-------------------------------+  |
+-------------------------------------------------------------------------+
```

---

## 3. Separation of Local vs. Cloud Capabilities

| Capability | Local Edge Runtime | Optional Cloud Service |
|---|---|---|
| **Facial & Vocal Emotion Recognition** | **100% Local (Real-Time)** | None (Strictly Prohibited) |
| **Real-Time Social Response Generation** | **100% Local (Real-Time)** | None (Strictly Prohibited) |
| **Safety Interlocks & Non-Authoritative Check** | **100% Local (Real-Time)** | None (Strictly Prohibited) |
| **Ephemeral Session Context** | **100% Local (In-Memory)** | None |
| **Cross-Robot Episodic Knowledge Sync** | Local cache only | Fleet-wide federated sync (Consented) |
| **Fleet Health & Diagnostics Telemetry** | Local journald / CLI | Centralized monitoring dashboard |
| **Model Weight Distribution (OTA Updates)** | Local installation | Signed artifact repository & staging |

---

## 4. Traceability Matrix

| Requirement ID | Architectural Requirement | Specification Document |
|---|---|---|
| `PRD-REQ-008` | Optional cloud connectivity without cloud dependency | `CLOUD_EDGE_SYNCHRONIZATION.md` |
| `SRS-ARCH-014` | Secure multi-tenant cloud control plane | `CLOUD_TENANT_ISOLATION.md` |
| `ADR-024` | Architecture Decision Record: Optional Cloud Architecture | `ADR-024-optional-cloud-architecture-and-sync.md` |
