# OVIC EON — EON Core State Model Specification

**Document ID:** `EON-ARCH-CORE-007`  
**Phase:** Phase 2 — System Architecture and Engineering Design  
**Sub-phase:** 2.3 — Design EON Core  
**Status:** Approved Engineering Architecture Specification  
**Version:** 1.0.0  
**Classification:** Technical Architecture Specification  
**Document Owner:** Principal Software Architect  
**Related Documents:**
- `docs/architecture/EON_CORE_ARCHITECTURE.md` (`EON-ARCH-CORE-004`)
- `docs/architecture/EON_CORE_INITIALIZATION.md` (`EON-ARCH-CORE-006`)
- `docs/architecture/EON_CORE_FAILURE_HANDLING.md` (`EON-ARCH-CORE-008`)

---

## 1. Executive Summary

This specification establishes the formal finite state machine (FSM) governing **EON Core**. It defines all system-level operational states, valid state transitions, transition triggers, and prohibited transitions.

---

## 2. Core State Definitions

```text
+=======================================================================================+
| Core State       | Operational Semantics                                              |
+=======================================================================================+
| `UNINITIALIZED`  | Process started; configuration and components not yet loaded.      |
| `INITIALIZING`   | Executing the 12-step initialization sequence.                     |
| `READY`          | Fully operational; all required engines active; accepting events.  |
| `DEGRADED`       | Operational with reduced capacity (non-critical engine/model down).|
| `RECOVERING`     | Attempting restart or fallback configuration for failed component. |
| `SHUTTING_DOWN`  | Draining event queues and releasing subsystem resources.           |
| `STOPPED`        | Orderly shutdown complete; process ready to exit.                  |
| `FAILED`         | Fatal unrecoverable error encountered; process halting.            |
+=======================================================================================+
```

---

## 3. State Transition Matrix

```text
+-------------------+-----------------+-------------------+-----------------------------------------+
| Source State      | Target State    | Trigger Event     | Guard Condition                         |
+-------------------+-----------------+-------------------+-----------------------------------------+
| UNINITIALIZED     | INITIALIZING    | initialize()      | None                                    |
| INITIALIZING      | READY           | preflight_ok      | All critical components healthy         |
| INITIALIZING      | DEGRADED        | non_critical_fail | Non-critical component failed check     |
| INITIALIZING      | FAILED          | fatal_error       | Critical dependency or config failure   |
| READY             | DEGRADED        | component_degrade | Non-critical engine/model crash         |
| READY             | SHUTTING_DOWN   | stop() / SIGTERM  | Graceful shutdown initiated             |
| DEGRADED          | RECOVERING      | trigger_recovery  | Recovery attempt started                |
| DEGRADED          | SHUTTING_DOWN   | stop() / SIGTERM  | Shutdown initiated                      |
| RECOVERING        | READY           | recovery_success  | Component restored to healthy state     |
| RECOVERING        | DEGRADED        | recovery_failed   | Recovery failed; remaining degraded     |
| SHUTTING_DOWN     | STOPPED         | drain_complete    | All queues drained and resources freed  |
| Any State         | FAILED          | unhandled_panic   | Critical infrastructure failure         |
+-------------------+-----------------+-------------------+-----------------------------------------+
```

### Prohibited State Transitions
- `STOPPED` -> `READY`: Prohibited; requires fresh process instantiation.
- `FAILED` -> `READY`: Prohibited; a failed system cannot declare readiness without restart.
- `UNINITIALIZED` -> `READY`: Prohibited; cannot bypass `INITIALIZING`.
