# ADR-013: Unified Engine Lifecycle Contract and Coordination Model

**Document ID:** `EON-ADR-013`  
**Status:** Approved  
**Date:** 2026-11-23  
**Deciders:** Principal Software Architect, Founder, Engineering Leads  
**Related Requirements:** `EON-FR-001`, `EON-NFR-005`, `EON-SRS-010`, `EON-ARCH-LIFE-001`

---

## 1. Context
The seven intelligence engines have differing computational workloads, model sizes, and frequencies: ERS and HBU process 30 fps sensory frames; SIE runs a 20 Hz interaction state machine; ERE and PSE are event-driven; ERG streams speech audio; and EMS writes to encrypted storage. Without a standardized lifecycle contract, managing startup order, health tracking, degraded execution, and shutdown leads to race conditions and stalled processes.

## 2. Problem
How can OVIC EON govern engine lifecycles through a single, consistent protocol while accommodating diverse operational frequencies, resource budgets, and failure modes?

## 3. Decision
Adopt a **Unified 11-State Engine Lifecycle Contract (`EonEngineContract`)**:
1. **11-State Formal State Machine & 7-State Operational Health Projection:** Standardize internal engine state transitions (`DISCOVERED` -> `REGISTERED` -> `VALIDATING` -> `INITIALIZING` -> `INITIALIZED` -> `STARTING` -> `RUNNING` -> `DEGRADED` -> `PAUSED` -> `STOPPING` -> `STOPPED` with terminal `FAILED`), and project external health onto a 7-state operational view (`UNINITIALIZED`, `INITIALIZING`, `ACTIVE`, `PAUSED`, `DEGRADED`, `STOPPED`, `FAULTED`) for external APIs and the Python SDK.
2. **Topological Startup & Reverse Shutdown:** Core starts engines in forward topological order (Tier 1: HBU/ERS -> Tier 2: EMS/SIE -> Tier 3: ERE/PSE -> Tier 4: ERG) and shuts them down in exact reverse order, preventing broken event pipelines.
3. **Automated Exponential Backoff Recovery:** An engine entering `DEGRADED` or `FAILED` is granted up to 3 automated recovery attempts before being permanently quarantined, preserving platform stability.
4. **Explicit Resource Declarations:** Engines must declare thread limits, memory budgets, queue capacities, and backpressure policies at registration time.

## 4. Alternatives Considered
1. **Ad-Hoc Unordered Startup:** Starting all engines concurrently in background tasks. Rejected because cognitive engines crash if they receive observations before their internal rule models or context handlers are initialized.
2. **Crash-the-World on Any Engine Failure:** Terminating the entire EON process if any engine throws an unhandled error. Rejected because robots must remain responsive to safety and navigational cues even if conversational dialogue degrades.

## 5. Consequences
- **Positive:** Deterministic startup/shutdown; zero race conditions; clear isolation of failed engines; predictable resource utilization.
- **Negative:** Engines must implement all lifecycle SPI methods, including self-healing `recover()` routines.

## 6. Risks and Mitigations
- **Risk:** An engine hanging during `stop()`, blocking system shutdown.
- **Mitigation:** Strict `timeout_seconds` (default 5.0s) enforced on `stop()`, after which Core forcefully terminates tasks and transitions the engine to `FAILED`.
