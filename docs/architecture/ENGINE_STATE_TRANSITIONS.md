# OVIC EON — Engine State Transitions Specification

**Document ID:** `EON-ARCH-LIFE-002`  
**Phase:** Phase 2 — System Architecture and Engineering Design  
**Sub-phase:** 2.4 — Design Engine Lifecycle  
**Status:** Approved Engineering Architecture Specification  
**Version:** 2.0.0 (Authoritative Reconciled Baseline)  
**Classification:** Technical Architecture Specification  
**Document Owner:** Principal Software Architect  
**Related Documents:**  
- `docs/architecture/ENGINE_LIFECYCLE_ARCHITECTURE.md` (`EON-ARCH-LIFE-001`)  
- `docs/architecture/ENGINE_LIFECYCLE_CONTRACT.md` (`EON-SPEC-LIFE-001`)  
- `docs/architecture/ENGINE_RECOVERY_AND_FAILURE_POLICIES.md` (`EON-POL-LIFE-001`)  

---

## 1. Executive Summary

This specification establishes the exhaustive state transition matrix, guard conditions, preconditions, postconditions, and prohibited transitions for the authoritative 11-state engine lifecycle model.

---

## 2. Exhaustive State Transition Matrix

```text
+================+===============+===================+=========================+=========================+==========================================+
| Current State  | Next State    | Operation/Trigger | Preconditions           | Postconditions          | Guard Conditions                         |
+================+===============+===================+=========================+=========================+==========================================+
| DISCOVERED     | REGISTERED    | register()        | Engine metadata loaded  | Engine present in reg   | Valid engine_id; required interfaces met |
| REGISTERED     | VALIDATING    | validate()        | Engine in REGISTERED    | Config loaded in memory | None                                     |
| VALIDATING     | INITIALIZING  | validation_ok     | Engine in VALIDATING    | Config schema valid     | All schema parameters pass validation    |
| VALIDATING     | FAILED        | validation_error  | Engine in VALIDATING    | Failure error logged    | Schema violation or missing dependency   |
| INITIALIZING   | INITIALIZED   | initialize() OK   | Engine in INITIALIZING  | Queues/buffers allocated| Resource budget respected (< RAM limit)  |
| INITIALIZING   | FAILED        | init_error        | Engine in INITIALIZING  | Error diagnostics stored| Alloc failure or model load timeout      |
| INITIALIZED    | STARTING      | start()           | Engine in INITIALIZED   | Workers thread created  | Upstream dependency engines INITIALIZED  |
| STARTING       | RUNNING       | workers_active    | Engine in STARTING      | Subscriptions listening | Worker loop handshake verified < 1000ms  |
| STARTING       | FAILED        | start_timeout     | Engine in STARTING      | Dead workers joined     | Startup timeout exceeded (default 5000ms)|
| RUNNING        | DEGRADED      | anomaly_detected  | Engine in RUNNING       | Fallback flag raised    | Latency > P95 target OR error_rate > 5%  |
| RUNNING        | PAUSED        | pause()           | Engine in RUNNING       | Workers asleep; Q held  | Pause command issued by Core supervisor  |
| PAUSED         | RUNNING       | resume()          | Engine in PAUSED        | Workers active; Q proc  | Resume command issued; bus ready         |
| DEGRADED       | RUNNING       | recover() OK      | Engine in DEGRADED      | Normal pipeline restored| Error rate < 1% for 30 consecutive sec   |
| DEGRADED       | FAILED        | recovery_failed   | Engine in DEGRADED      | Engine isolated from bus| 3 consecutive recovery attempts failed   |
| RUNNING        | STOPPING      | stop()            | Engine in RUNNING       | New arrivals rejected   | Teardown deadline configured             |
| PAUSED         | STOPPING      | stop()            | Engine in PAUSED        | Queues unpaused to drain| Teardown deadline configured             |
| DEGRADED       | STOPPING      | stop()            | Engine in DEGRADED      | In-flight work aborted  | Teardown deadline configured             |
| STOPPING       | STOPPED       | drain_complete    | Engine in STOPPING      | All resources released  | In-flight queue count == 0               |
| STOPPING       | FAILED        | stop_timeout      | Engine in STOPPING      | Threads hard-terminated | Drain timeout exceeded (> 5000ms)        |
| Any State      | FAILED        | unhandled_panic   | Any non-terminal state  | Core crash log written  | Unhandled exception, OOM, SIGSEGV        |
+================+===============+===================+=========================+=========================+==========================================+
```

---

## 3. Strictly Prohibited (Invalid) Transitions

The EON Core kernel supervisor rejects the following transitions, raising `EonEngineStateError`:

1. **`STOPPED` -> `RUNNING`:** Engines cannot bypass the re-initialization sequence. A stopped engine must re-enter via `REGISTERED` -> `VALIDATING` -> `INITIALIZING` -> `INITIALIZED` -> `STARTING` -> `RUNNING`.
2. **`FAILED` -> `RUNNING`:** A failed engine cannot directly resume execution. It must be explicitly reset via `recover()` or completely re-instantiated.
3. **`DISCOVERED` -> `INITIALIZING`:** Bypassing schema and dependency validation is prohibited.
4. **`RUNNING` -> `INITIALIZING`:** Hot re-initialization while active is prohibited; the engine must be transitioned through `STOPPING` -> `STOPPED` first.
5. **`PAUSED` -> `INITIALIZING`:** Prohibited; must be stopped before memory and queue structures can be reallocated.
6. **`INITIALIZED` -> `DEGRADED`:** An engine cannot degrade before it has commenced worker execution.

---

## 4. Mapping to 7-State Operational Health Projection

```text
Internal 11-State Engine FSM State               External 7-State Operational Projection
-----------------------------------               ---------------------------------------
DISCOVERED, REGISTERED                     --->   UNINITIALIZED
VALIDATING, INITIALIZING, INITIALIZED, STARTING ---> INITIALIZING
RUNNING                                    --->   ACTIVE
PAUSED                                     --->   PAUSED
DEGRADED                                   --->   DEGRADED
STOPPING, STOPPED                          --->   STOPPED
FAILED                                     --->   FAULTED
```
