# OVIC EON — Engine State Transitions Specification

**Document ID:** `EON-ARCH-LIFE-002`  
**Phase:** Phase 2 — System Architecture and Engineering Design  
**Sub-phase:** 2.4 — Design Engine Lifecycle  
**Status:** Approved Engineering Architecture Specification  
**Version:** 1.0.0  
**Classification:** Technical Architecture Specification  
**Document Owner:** Principal Software Architect  
**Related Documents:**
- `docs/architecture/ENGINE_LIFECYCLE_ARCHITECTURE.md` (`EON-ARCH-LIFE-001`)
- `docs/architecture/ENGINE_LIFECYCLE_CONTRACT.md` (`EON-SPEC-LIFE-001`)

---

## 1. Executive Summary

This specification establishes the formal state transition table and transition guard conditions for the 11-state engine lifecycle model.

---

## 2. Complete State Transition Matrix

```text
+----------------+---------------+-------------------+-----------------------------------------+
| Current State  | Next State    | Operation / Event | Guard Condition                         |
+----------------+---------------+-------------------+-----------------------------------------+
| DISCOVERED     | REGISTERED    | register()        | Engine metadata valid; ID recognized    |
| REGISTERED     | VALIDATING    | validate()        | None                                    |
| VALIDATING     | INITIALIZING  | validation_ok     | Configuration schemas and contracts pass|
| VALIDATING     | FAILED        | validation_error  | Invalid configuration or missing req dep|
| INITIALIZING   | INITIALIZED   | initialize() OK   | Event bus and internal queues allocated |
| INITIALIZING   | FAILED        | init_error        | Model loading or resource alloc failed  |
| INITIALIZED    | STARTING      | start()           | System Core in INITIALIZING/READY state |
| STARTING       | RUNNING       | workers_active    | Event subscriptions active and healthy  |
| STARTING       | FAILED        | start_timeout     | Workers failed to start within timeout  |
| RUNNING        | DEGRADED      | anomaly_detected  | Model inference timeout or error rate>5%|
| RUNNING        | PAUSED        | pause()           | Robot docking, idling, or sleep mode    |
| PAUSED         | RUNNING       | resume()          | Wakeup signal received                  |
| DEGRADED       | RUNNING       | recover() OK      | Self-healing restored normal operation  |
| DEGRADED       | FAILED        | recovery_failed   | 3 consecutive recovery attempts failed  |
| RUNNING/PAUSED | STOPPING      | stop()            | Core initiating shutdown or maintenance |
| STOPPING       | STOPPED       | drain_complete    | In-flight queues drained, tasks canceled|
| STOPPING       | FAILED        | stop_timeout      | Tasks hung; forced kill required        |
| Any State      | FAILED        | unhandled_panic   | Memory exhaustion or unhandled exception|
+----------------+---------------+-------------------+-----------------------------------------+
```

### Prohibited Transitions
- `STOPPED` -> `RUNNING`: Direct restart prohibited without full re-initialization sequence.
- `FAILED` -> `RUNNING`: Must transition through `recover()` or clean restart.
- `DISCOVERED` -> `INITIALIZING`: Cannot skip validation phase.
