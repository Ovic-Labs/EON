# ADR-003: Asynchronous Event-Driven Inter-Component Communication

**Document ID:** `EON-ADR-003`  
**Status:** Approved  
**Date:** 2026-11-23  
**Deciders:** Principal Software Architect, Founder, Engineering Leads  
**Related Requirements:** `EON-NFR-011`, `EON-SRS-005` through `EON-SRS-015`, `EON-ARCH-CORE-001`

---

## 1. Context
Real-time robotics architectures process multiple sensory streams concurrently (video at 30 fps, audio chunks at 50 fps, odometry at 100 Hz) while concurrently performing cognitive reasoning and generating expressive behaviors. Synchronous blocking communication across such heterogeneous workloads causes event loop blocking and frame drops.

## 2. Problem
What communication paradigm should mediate inter-component messaging across OVIC EON, and how can the platform ensure high throughput, deterministic backpressure, and fault isolation?

## 3. Decision
Adopt an **In-Memory Asynchronous Event-Driven Architecture** mediated by the **L5 Core Event Bus**:
1. **Typed Event Envelopes:** All messages are wrapped in `EventEnvelope[PayloadT]` carrying causality IDs, correlation IDs, UTC timestamps, and privacy classifications.
2. **Per-Subscriber Bounded Priority Queues:** Each subscriber receives an isolated queue with configurable capacity (default 1000) and backpressure policy (`WAIT`, `REJECT`, `DROP_OLDEST`).
3. **Threadpool Isolation for Synchronous Handlers:** Synchronous handlers are offloaded to a bounded `ThreadPoolExecutor` (default 4 workers) to prevent event loop starvation.
4. **Deterministic Task Accounting:** Exact matching of queue joins and completions with underflow/overflow prevention.

## 4. Alternatives Considered
1. **ZeroMQ / Nanomsg In-Process Sockets:** High serialization overhead; introduces native C library dependencies that complicate cross-compilation on edge ARM64 platforms.
2. **Python `asyncio.Queue` Without Isolation:** Unbounded queues risk memory exhaustion under slow consumers; synchronous handler execution blocks the event loop.

## 5. Consequences
- **Positive:** Decoupled publisher-subscriber topology; verified peak throughput of >108,000 events/sec; zero thread contention; deterministic backpressure.
- **Negative:** Subscribers must handle asynchronous event delivery and possible out-of-order event arrivals.

## 6. Risks and Mitigations
- **Risk:** Queue saturation under bursty sensory input.
- **Mitigation:** High-frequency observation queues use `DROP_OLDEST` policy, dropping stale frames while preserving safety and context events.
