# OVIC EON — Engine Recovery and Failure Policies

**Document ID:** `EON-POL-LIFE-001`  
**Phase:** Phase 2 — System Architecture and Engineering Design  
**Sub-phase:** 2.4 — Design Engine Lifecycle  
**Status:** Approved Engineering Architecture Specification  
**Version:** 1.0.0  
**Classification:** Technical Architecture Specification  
**Document Owner:** Principal Software Architect  
**Related Documents:**
- `docs/architecture/ENGINE_LIFECYCLE_ARCHITECTURE.md` (`EON-ARCH-LIFE-001`)
- `docs/architecture/EON_CORE_FAILURE_HANDLING.md` (`EON-ARCH-CORE-008`)

---

## 1. Executive Summary

This document specifies the fault detection, isolation, self-healing recovery, and restart policies governing failed or degraded intelligence engines.

---

## 2. Fault Classification and Recovery Hierarchy

```text
+=======================================================================================+
| Severity Level | Trigger Condition                    | Standard Recovery Procedure    |
+=======================================================================================+
| Level 1: Minor | Single model inference timeout (>25ms)| Drop frame, emit last EMA state|
| Level 2: Degr. | Consecutive timeouts (>3) or OOM err | Fallback to deterministic rule |
| Level 3: Crash | Unhandled engine worker task panic   | Cancel task, respawn worker pool|
| Level 4: Fatal | Persistent crash after 3 restarts    | Isolate engine, mark FAILED    |
+=======================================================================================+
```

---

## 3. Automated Self-Healing Policies

1. **Exponential Backoff Restart Policy:** When an engine enters `FAILED`, Core attempts automatic recovery up to 3 times with exponential backoff:
   - Attempt 1: Immediate retry ($0.5\text{ s}$ delay).
   - Attempt 2: Second retry ($2.0\text{ s}$ delay).
   - Attempt 3: Final retry ($5.0\text{ s}$ delay).
   - If Attempt 3 fails, the engine is permanently isolated in `FAILED` state until manual administrative intervention.
2. **Blast Radius Quarantine:** An isolated engine's subscriber queues are detached from the Core Event Bus, preventing dead-letter accumulation or queue lockup.
3. **Safety Notification:** Whenever an engine transitions to `DEGRADED` or `FAILED`, Core automatically publishes a `SafetyAdvisoryEvent` (`SafetyAdvisoryLevel.WARNING` or `ERROR`) to alert the host robot safety system.
