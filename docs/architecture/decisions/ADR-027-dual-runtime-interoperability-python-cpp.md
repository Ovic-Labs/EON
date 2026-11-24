# ADR-027: Dual-Runtime Interoperability (Python and C++ SDKs)

**Document ID:** `EON-ADR-027`  
**Date:** 2026-11-24  
**Status:** `APPROVED`  
**Deciders:** Antigravity Engineering Architecture Team  
**Scope:** Client SDKs, Runtime Interoperability, Cross-Language Contracts  

---

## 1. Context and Problem Statement

EON supports two first-class SDK runtimes: Python (`eon-sdk`) for agile development and C++ (`libeonsdk`) for real-time robotic nodes. Contract drift between these runtimes would fracture the developer ecosystem.

## 2. Decision

We decide to enforce strict **Dual-Runtime Interoperability**:
1. Both SDKs consume the identical underlying IPC transport contracts and Protocol Buffer / JSON event schemas.
2. Both SDKs expose the reconciled **7-State Operational Health Projection** (`UNINITIALIZED`, `INITIALIZING`, `ACTIVE`, `PAUSED`, `DEGRADED`, `STOPPED`, `FAULTED`).
3. Both SDKs enforce the mandatory non-authoritative motion proposal invariant (`is_authoritative = false`).
4. Both SDKs qualify sub-millisecond latency targets as provisional design expectations backed by the unified hardware benchmark protocol.

## 3. Alternatives Considered

- *Alternative A: Divergent Feature Sets.* Rejected: Breaks cross-language documentation and creates operational confusion.
- *Alternative B: Pure C++ Core with Thin Python ctypes Wrapper.* Rejected: Deprives Python developers of native Pythonic async/await idioms.

## 4. Consequences and Implications

- **Positive:** Uniform conceptual model across languages; seamless transition from Python prototyping to C++ deployment.
- **Negative:** Requires cross-language contract testing in CI.
- **Security Implications:** Identical authentication handshakes across both runtimes.
- **Privacy Implications:** Shared data minimization contracts.
- **Performance Implications:** C++ provides native zero-copy path; Python utilizes optimized memoryviews.
- **Related ADRs:** ADR-007, ADR-013, ADR-019, ADR-020.
- **Supersession History:** None.
