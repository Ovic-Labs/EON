# ADR-007: SDK and Client Integration Boundaries

**Document ID:** `EON-ADR-007`  
**Status:** Approved  
**Date:** 2026-11-23  
**Deciders:** Principal Software Architect, Founder, Engineering Leads  
**Related Requirements:** `EON-NFR-050`, `EON-SRS-100`, `EON-DEV-CORE-001`

---

## 1. Context
Robot manufacturers and application developers integrate EON into various software environments, ranging from single-process Python control scripts to complex distributed C++ autonomy stacks. The integration surface must be ergonomic, type-safe, and capable of both zero-overhead in-process operation and multi-process IPC.

## 2. Problem
How should the developer-facing SDK be structured to provide seamless integration while strictly protecting internal runtime invariants and preventing unauthorized internal state manipulation?

## 3. Decision
Establish **Layer 8 (SDK and Integration Layer)** with dual-mode client bindings:
1. **Dual Execution Modes:**
   - **In-Process Mode:** `EonClient` links directly to the local L5 Core Event Bus via Python memory queues, delivering zero-copy sub-millisecond dispatch.
   - **Out-of-Process IPC Mode:** `EonClient` communicates over Unix Domain Sockets or shared memory with an independently supervised EON daemon.
2. **Strict Schema Encapsulation:** The SDK exposes only validated Pydantic models (`ObservationPayload`, `EmotionEstimatePayload`, `ResponseProposalPayload`). Raw internal engine state or private bus structures are not exposed.
3. **Language Support:** Provide idiomatic AsyncIO (`AsyncEonClient`) and synchronous threaded (`EonClient`) interfaces in Python, with C++20 bindings for robotic middleware.

## 4. Alternatives Considered
1. **Exposing Raw Event Bus Directly to Developers:** Allowing developers to call `EventBus.publish()` directly. Rejected because it exposes internal routing mechanics and allows developers to bypass schema versioning and lifecycle controls.
2. **REST-Only SDK:** Requiring all SDK clients to use HTTP localhost REST calls. Rejected due to excessive latency (>3–8 ms per request) and high serialization overhead for real-time sensor streams.

## 5. Consequences
- **Positive:** Ergonomic developer experience; compile-time and runtime type safety; seamless switching between embedded in-process and daemon modes.
- **Negative:** Requires maintaining SDK wrapper layers synchronized with internal schema versioning.

## 6. Risks and Mitigations
- **Risk:** SDK versions becoming out-of-sync with core runtime versions.
- **Mitigation:** Strict schema handshake on client connection; version negotiation enforced via `validate_schema_version()`.
