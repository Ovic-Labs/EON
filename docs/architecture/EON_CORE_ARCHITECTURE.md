# OVIC EON — EON Core Architecture Specification

**Document ID:** `EON-ARCH-CORE-004`  
**Phase:** Phase 2 — System Architecture and Engineering Design  
**Sub-phase:** 2.3 — Design EON Core  
**Status:** Approved Engineering Architecture Specification  
**Version:** 1.0.0  
**Classification:** Technical Architecture Specification  
**Document Owner:** Principal Software Architect  
**Related Documents:**
- `docs/architecture/SYSTEM_LAYERED_ARCHITECTURE.md` (`EON-ARCH-LAYERS-001`)
- `docs/architecture/EON_CORE_COMPONENTS.md` (`EON-ARCH-CORE-005`)
- `docs/architecture/EON_CORE_INITIALIZATION.md` (`EON-ARCH-CORE-006`)
- `docs/architecture/EON_CORE_STATE_MODEL.md` (`EON-ARCH-CORE-007`)
- `docs/architecture/EON_CORE_FAILURE_HANDLING.md` (`EON-ARCH-CORE-008`)
- `docs/architecture/decisions/ADR-012-eon-core-architecture.md` (`EON-ADR-012`)

---

## 1. Executive Summary

This specification defines the central orchestration, supervision, and coordination architecture of **EON Core** (Layer 5 of the OVIC EON layered system architecture).

EON Core is the operational backbone of OVIC EON. It is **not** an eighth intelligence engine; rather, it is the domain-neutral platform substrate that coordinates the seven intelligence engines (ERS, EMS, ERE, PSE, SIE, ERG, HBU), manages platform lifecycle transitions, brokers asynchronous event communication, mediates shared context and model adapter services, monitors subsystem health, isolates runtime failures, and enforces system-wide safety and privacy policies.

---

## 2. Core Architectural Responsibilities

EON Core owns twelve non-delegable platform responsibilities:

1. **System Initialization:** Sequenced bootstrap from configuration verification to readiness declaration.
2. **Component & Engine Registration:** Dynamic discovery, registration, and contract validation of engines and platform extensions.
3. **Engine Orchestration:** Dependency-ordered lifecycle transitions (`CREATED` -> `RUNNING` -> `PAUSED` -> `STOPPED`) without direct engine-to-engine coupling.
4. **Configuration Management:** Hierarchical configuration loading, schema validation, environment substitution, and hot-reload coordination.
5. **Event Routing Integration:** High-performance, priority-scheduled, asynchronous in-memory event bus mediation.
6. **Shared Context Integration:** Mediating access to session context, working memory, and consent-gated persistent storage SPIs.
7. **Model Adapter Integration:** Coordinating local machine learning inference runtimes (ONNX, `llama.cpp`, Piper) and hardware acceleration discovery.
8. **Health Monitoring & Supervision:** Periodic heartbeats, watchdog tracking, and aggregated system health state assessment.
9. **Failure Handling & Blast Radius Containment:** Isolating engine crashes, queue overflows, and model failures without terminating the host process.
10. **Graceful Shutdown Coordination:** Deterministic queue draining, task cancellation, and resource release within bounded deadlines.
11. **System-Wide Policy Enforcement:** Enforcing non-authoritative actuation invariants (`is_authoritative_stop=False`), schema versioning, and privacy data scrubbing.
12. **Observability & Diagnostics:** Structured JSON telemetry, OpenTelemetry-compatible tracing, and Prometheus-compatible metrics export.

---

## 3. High-Level Core Substrate Architecture

```text
+===================================================================================+
|                                    EON CORE (L5)                                  |
+===================================================================================+
|  +-----------------------------------------------------------------------------+  |
|  |                           Core Application Manager                          |  |
|  |     (Top-level orchestrator, startup sequencer, shutdown coordinator)       |  |
|  +-----------------------------------------------------------------------------+  |
|         │                        │                        │                       |
|         ▼                        ▼                        ▼                       |
|  +---------------+      +------------------+      +------------------------+      |
|  | Configuration |      | Health Manager & |      |   Policy Enforcement   |      |
|  |    Manager    |      | Supervisor       |      |   Gatekeeper           |      |
|  +---------------+      +------------------+      +------------------------+      |
|         │                        │                        │                       |
|  +-----------------------------------------------------------------------------+  |
|  |                     Engine Registry & Lifecycle Coordinator                 |  |
|  |       (Engine discovery, dependency resolver, state machine management)     |  |
|  +-----------------------------------------------------------------------------+  |
|         │                        │                        │                       |
|         ▼                        ▼                        ▼                       |
|  +---------------+      +------------------+      +------------------------+      |
|  |  Event Router |      | Context Service  |      | Model Adapter Registry |      |
|  | & Event Bus   |      | Interface        |      | & Hardware Discovery   |      |
|  +---------------+      +------------------+      +------------------------+      |
+===================================================================================+
```

---

## 4. Architectural Boundaries and Non-Goals

### What EON Core Does NOT Do
- **No Domain Emotion Reasoning:** Core does not calculate valence, arousal, empathy strategies, or conversation turns; these belong strictly to L4 engines.
- **No Direct Physical Actuation:** Core never commands robot hardware motors, joints, or emergency brakes. All outgoing proposals carry `is_authoritative_stop=False`.
- **No Direct Media Ingestion:** Core does not read camera devices or microphones; sensor streams are ingested and normalized in L2 HAL and L3 Perception.
- **No Mandatory External Network Egress:** Core functions entirely offline on edge hardware without external cloud connectivity.
