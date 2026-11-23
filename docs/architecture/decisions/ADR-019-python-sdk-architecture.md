# ADR-019: Dual-Mode Synchronous/Asynchronous Python SDK Architecture

**Document ID:** `EON-ADR-019`  
**Status:** `APPROVED`  
**Date:** `2026-11-23`  
**Author:** Multi-Disciplinary Architecture Team  
**Scope:** EON Phase 2.10 — Python SDK Architecture  
**Deciders:** Lead Systems Architect, Edge AI Engineer, Robotics Integration Lead  

---

## 1. Context & Problem Statement

The EON Emotional Intelligence Infrastructure requires a developer-facing client integration layer that bridges robotics applications, human-robot interaction (HRI) nodes, cloud services, and developer tooling.

The integration environment presents conflicting architectural requirements:
1. **Robotic Onboard Compute:** Requires sub-millisecond call latency, zero-copy memory transfers, and minimal serialization overhead when running directly alongside the EON Core kernel.
2. **Distributed & Remote Systems:** Requires secure, encrypted network transport (HTTPS, WebSocket, gRPC) across local-area robot networks or remote fleet management clouds via the EON API Gateway.
3. **Programming Paradigms:** High-throughput streaming and concurrency demand an asynchronous native coroutine model (`asyncio`), while standard scripting, notebooks, and legacy robotics frameworks demand simple, blocking synchronous semantics.
4. **Embedded Constraints:** Edge devices cannot tolerate heavy, bloated dependencies (such as heavy deep learning frameworks or complex distributed engines) inside a client SDK.

---

## 2. Decision

We decide to architect the EON Python SDK (`src/eon/`) with the following foundational patterns:

1. **Dual-Mode Client Design:**
   - **Local In-Process Mode:** Binds directly to the local Python interpreter memory space of the EON Core kernel (`eon.core`), bypassing serialization for sub-millisecond interaction.
   - **Remote Client Mode:** Dispatches strongly-typed requests across the network to the EON API Gateway using HTTP/1.1, HTTP/2, WebSocket, and optional gRPC transports.
2. **Async-Native Core with Ergonomic Sync Facade:**
   - Implement `AsyncEonClient` as the primary, high-concurrency client leveraging standard `asyncio`.
   - Provide `EonClient` as an ergonomic synchronous wrapper that delegates to an internal managed event loop, offering seamless context management and blocking calls.
3. **Layered Subsystem Clients:**
   - Structure top-level clients with dedicated subsystem accessors: `.engines`, `.events`, `.context`, `.models`, `.health`, and `.auth`.
4. **Lean Core Dependencies & Optional Feature Extras:**
   - Core SDK runtime relies strictly on `httpx`, `pydantic`, and `typing-extensions`.
   - Heavier drivers are separated into declarative optional extras: `[local]`, `[remote]`, `[grpc]`, and `[dev]`.
5. **Deterministic Error Handling & Resilient Backoff:**
   - Unify all SDK exceptions under `EonError`.
   - Implement full jitter exponential backoff for idempotent requests and automatic WebSocket reconnection.
6. **Strict Separation from Engine Inference Implementation:**
   - The SDK strictly contains client contracts, models, and transport drivers. Heavy neural network runtimes remain strictly separate in future engine packages.

---

## 3. Consequences

### Positive Consequences
- **Unified Developer Experience:** Developers use identical method signatures whether writing an on-robot script or an external cloud integration.
- **Maximum Edge Efficiency:** Zero IPC and zero serialization overhead in Local In-Process Mode ensures real-time performance on constrained edge hardware.
- **Type Safety & Reliability:** 100% type coverage with Pydantic domain models eliminates runtime type errors and enables IDE autocomplete.
- **Minimal Footprint:** Edge installations require less than 15 MB of core dependencies.

### Negative Consequences / Trade-offs
- **Maintenance of Dual Modes:** Transport abstractions require maintaining both direct memory binding and networked HTTP/WS transport layers.
- **Sync/Async Parallel Maintenance:** Maintaining both sync and async client facades requires rigorous test coverage to prevent API drift.

---

## 4. Compliance & Traceability

- Adheres to `EON-SRS-DEV-001` (Developer SDK Ergonomics)
- Adheres to `EON-SRS-PERF-003` (Edge Onboard Low-Latency Processing)
- Adheres to `EON-ARCH-CORE-004` (EON Core Architecture)
- Adheres to `EON-ARCH-API-001` (API Gateway Architecture)
