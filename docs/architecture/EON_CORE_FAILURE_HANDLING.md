# OVIC EON — EON Core Failure Handling and Isolation Specification

**Document ID:** `EON-ARCH-CORE-008`  
**Phase:** Phase 2 — System Architecture and Engineering Design  
**Sub-phase:** 2.3 — Design EON Core  
**Status:** Approved Engineering Architecture Specification  
**Version:** 1.0.0  
**Classification:** Technical Architecture Specification  
**Document Owner:** Principal Software Architect  
**Related Documents:**
- `docs/architecture/EON_CORE_ARCHITECTURE.md` (`EON-ARCH-CORE-004`)
- `docs/architecture/EON_CORE_STATE_MODEL.md` (`EON-ARCH-CORE-007`)
- `docs/architecture/ARCHITECTURE_CONSTRAINTS.md` (`EON-ARCH-CONST-001`)

---

## 1. Executive Summary

This specification defines the fault isolation boundaries, blast radius containment mechanisms, and failure handling procedures implemented by **EON Core**.

A fundamental invariant of OVIC EON is that **the crash, exception, or timeout of an individual engine, perception pipeline, or ML model must not crash the complete EON runtime or halt safety advisory monitoring**.

---

## 2. Failure Domain Taxonomy and Containment Matrix

```text
+=======================================================================================+
| Failure Category      | Containment Mechanism               | Core Outcome & State    |
+=======================================================================================+
| Individual Engine     | Handler try-except; queue isolation;| State -> DEGRADED;      |
| Crash / Exception     | engine marked FAILED; retry up to 3x| Peer engines unaffected.|
+-----------------------+-------------------------------------+-------------------------+
| Local ML Runtime      | L7 adapter catches tensor/OOM error;| Fallback to template;   |
| Failure (ONNX / SLM)  | returns ModelInferenceError         | Zero process crash.     |
+-----------------------+-------------------------------------+-------------------------+
| Subscriber Queue      | Per-subscriber bounded capacity;    | Oldest unread dropped;  |
| Saturation (Slow Eng) | policy: DROP_OLDEST or REJECT       | Publisher unaffected.   |
+-----------------------+-------------------------------------+-------------------------+
| Context Storage Error | SQLite lock / disk full trapped;    | Fallback to volatile    |
| (Disk / Database)     | logs SafetyAdvisoryLevel.WARNING    | RAM-only memory mode.   |
+-----------------------+-------------------------------------+-------------------------+
| Engine Execution      | asyncio.wait_for deadline enforcer; | Stalled task cancelled; |
| Timeout (>300ms)      | handler cancelled via CancelledError| Fallback intent emitted.|
+-----------------------+-------------------------------------+-------------------------+
| Event Bus Core        | Task accounting overflow check;     | Fatal: Emits panic,     |
| Corruption (Critical) | isolated state locks                | initiates clean shutdown|
+=======================================================================================+
```

---

## 3. Blast Radius Isolation Architecture

1. **Process Isolation:** Core runs with dedicated signal handlers (`SIGTERM`, `SIGINT`).
2. **Event Loop Shielding:** Synchronous handlers execute in a bounded `ThreadPoolExecutor` (4 workers), preventing worker blocking from freezing the `asyncio` event loop.
3. **Queue Independence:** Each subscriber maintains a physically separate priority queue. A subscriber consuming slowly does not hold locks or consume memory from other subscriber queues.
4. **Safety Monitoring Immunity:** `SafetyAdvisoryEvent` routing uses high-priority queue channels (`EventPriority.HIGH` / `CRITICAL`), ensuring that safety alerts bypass perception queue backlogs.
