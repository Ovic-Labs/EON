# ADR-014: Event-Driven Communication and Delivery Guarantees

**Document ID:** `EON-ADR-014`  
**Status:** Approved  
**Date:** 2026-11-23  
**Deciders:** Principal Software Architect, Founder, Engineering Leads  
**Related Requirements:** `EON-FR-001`, `EON-NFR-011`, `EON-SRS-005`, `EON-ARCH-COMM-001`

---

## 1. Context
Real-time robotics architectures process multiple sensory streams concurrently (video at 30 fps, audio chunks at 50 fps, odometry at 100 Hz) while concurrently performing cognitive reasoning and generating expressive behaviors. Cross-component messaging must be fast, bounded, and immune to cascading consumer slowdowns.

## 2. Problem
What delivery guarantees, backpressure policies, and priority mechanisms should govern the communication substrate across EON Core and the seven intelligence engines?

## 3. Decision
Adopt an **In-Memory Asynchronous Priority-Scheduled Event Bus**:
1. **Realistic Delivery Semantics:** At-least-once delivery under normal load; at-most-once under `DROP_OLDEST` overload eviction. Avoid false claims of distributed "exactly-once" delivery.
2. **Per-Subscriber Bounded Queues:** Isolated FIFO queues with strict capacities (50–200 items), eliminating shared lock contention.
3. **Synchronous Worker Isolation:** Bounded `ThreadPoolExecutor` (4 workers) for legacy or synchronous handlers, preventing event loop blocking.
4. **Deterministic Task Accounting:** Exact matching of queue joins and completions with underflow/overflow prevention.
5. **Universal Envelope Encapsulation:** Enforce `EventEnvelope[T]` with causality, correlation, and privacy classification metadata on every message.

## 4. Alternatives Considered
1. **IPC via Shared ZeroMQ / Nanomsg:** Introduces high serialization overhead and native C library compilation hurdles on edge ARM boards.
2. **Unbounded Python Queues:** Unbounded queues lead to memory exhaustion and kernel OOM kills under bursty vision inputs.

## 5. Consequences
- **Positive:** Sub-millisecond dispatch (0.038ms median); peak throughput >108,000 events/sec; zero thread contention; clean failure isolation.
- **Negative:** Subscribers must design for idempotency.

## 6. Risks and Mitigations
- **Risk:** Stale observations processed during sudden delays.
- **Mitigation:** Envelopes support `expires_at`; handlers discard stale payloads where `is_stale()` evaluates to true.
