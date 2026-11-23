# OVIC EON — Event-Driven Communication Architecture Specification

**Document ID:** `EON-ARCH-COMM-001`  
**Phase:** Phase 2 — System Architecture and Engineering Design  
**Sub-phase:** 2.5 — Design Event-Driven Communication  
**Status:** Approved Engineering Architecture Specification  
**Version:** 1.0.0  
**Classification:** Technical Architecture Specification  
**Document Owner:** Principal Software Architect  
**Related Documents:**
- `docs/architecture/EVENT_ENVELOPE_SPECIFICATION.md` (`EON-SPEC-ENV-001`)
- `docs/architecture/EVENT_TAXONOMY.md` (`EON-SPEC-COMM-001`)
- `docs/architecture/EVENT_DELIVERY_AND_RELIABILITY.md` (`EON-SPEC-COMM-002`)
- `docs/architecture/EVENT_SECURITY_AND_PRIVACY.md` (`EON-POL-COMM-001`)
- `docs/architecture/CORE_EVENT_BUS_ARCHITECTURE.md` (`EON-ARCH-CORE-001`)
- `docs/architecture/decisions/ADR-014-event-driven-communication-and-delivery-guarantees.md` (`EON-ADR-014`)

---

## 1. Executive Summary

This specification establishes the communication architecture connecting EON Core, the seven intelligence engines, and platform support services.

OVIC EON utilizes a high-performance, CPU-optimized, asynchronous in-memory event-driven architecture. All cross-component messaging is mediated by the **L5 Core Event Bus** using standardized, versioned event envelopes. This decouples event publishers from consumers, enforces failure isolation, and guarantees bounded memory consumption.

---

## 2. Communication Model and Guarantees

### 2.1 Core Communication Entities
- **Publishers:** Components emitting events (e.g. L3 Perception, ERS, ERE, SIE, ERG).
- **Subscribers:** Components registering interest in exact topic strings (e.g. `emotion.estimate.realtime`) or prefix wildcards (e.g. `observation.*`).
- **Event Bus Router:** Snapshot-based, lock-free routing engine matching topics to subscriber queues.
- **Priority Queues:** Per-subscriber bounded priority queues supporting three scheduling tiers: `HIGH`, `NORMAL`, `LOW`.

### 2.2 Delivery Guarantees
- **In-Memory Delivery:** At-least-once delivery for subscribers under non-saturated queue conditions; at-most-once under `DROP_OLDEST` eviction during overload.
- **Ordering Guarantee:** Strict FIFO ordering is guaranteed within an identical priority tier for any single publisher-subscriber pair.
- **No Magical Exactly-Once:** OVIC EON explicitly avoids false claims of distributed "exactly-once" delivery. Subscribers must enforce idempotent event handling using `event_id` and `causation_id`.

---

## 3. Existing Event Bus Compatibility and Gap Analysis

A rigorous inspection of the implemented Phase 1.3 Core Event Bus (`src/eon/core/event_bus.py`, `event_router.py`, `queue_manager.py`) confirmed:

```text
+=======================================================================================+
| Architectural Requirement        | Existing Phase 1.3 Implementation | Status         |
+=======================================================================================+
| Bounded Subscriber Queues        | Implemented in queue_manager.py   | 100% Aligned   |
| Backpressure (WAIT/REJECT/DROP)  | Implemented in backpressure.py    | 100% Aligned   |
| Synchronous Handler Isolation    | ThreadPoolExecutor (4 workers)    | 100% Aligned   |
| Deterministic Task Accounting    | Exact task_done tracking          | 100% Aligned   |
| Priority Scheduling (HIGH/NORM)  | EventPriority in priority.py      | 100% Aligned   |
| Sub-millisecond Dispatch Latency | 0.038ms median benchmarked        | Verified [REP] |
+----------------------------------+-----------------------------------+----------------+
| Routing Deadline / Expiry Check  | In-flight deadline enforcement    | Phase 2 Target |
| Cryptographic Envelope Integrity | HMAC signature validation         | Phase 2 Target |
+=======================================================================================+
```
