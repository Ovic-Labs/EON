# OVIC EON — Event Delivery and Reliability Specification

**Document ID:** `EON-SPEC-COMM-002`  
**Phase:** Phase 2 — System Architecture and Engineering Design  
**Sub-phase:** 2.5 — Design Event-Driven Communication  
**Status:** Approved Engineering Architecture Specification  
**Version:** 1.0.0  
**Classification:** Technical Architecture Specification  
**Document Owner:** Principal Software Architect  
**Related Documents:**
- `docs/architecture/EVENT_DRIVEN_COMMUNICATION.md` (`EON-ARCH-COMM-001`)
- `docs/architecture/BACKPRESSURE_AND_PRIORITY_POLICY.md` (`EON-ARCH-CORE-003`)

---

## 1. Executive Summary

This specification defines the queueing policies, backpressure handling, priority scheduling, and idempotency mechanisms governing reliable event delivery.

---

## 2. Queue Policies and Backpressure Mechanics

Every subscriber queue operates under one of three deterministic backpressure policies:

```text
+=======================================================================================+
| Policy        | Behavior on Queue Full               | Target Subsystem Usage         |
+=======================================================================================+
| `DROP_OLDEST` | Evicts oldest unread item; appends   | High-rate perception streams   |
|               | new event without blocking.          | (Face mesh, audio, pose).      |
+---------------+--------------------------------------+--------------------------------+
| `WAIT`        | Blocks publisher asynchronously up   | Critical transactional events  |
|               | to timeout_seconds; raises QueueFull | (Context updates, memory write)|
+---------------+--------------------------------------+--------------------------------+
| `REJECT`      | Immediately raises QueueFullError    | Actuation proposals under      |
|               | without modifying queue contents.    | heavy robot motor backlog.     |
+=======================================================================================+
```

---

## 3. Priority Inversion and Starvation Prevention

To prevent low-priority sensory frames from starving high-priority safety advisories:
1. `PriorityQueue` schedules items across `CRITICAL` -> `HIGH` -> `NORMAL` -> `LOW`.
2. **Starvation Counter (`DEFAULT_STARVATION_THRESHOLD = 10`):** After 10 consecutive high-priority dispatches, the queue manager forces one lower-priority dispatch, guaranteeing bounded latency for normal background tasks.
