# OVIC EON — Data Storage Strategy Specification

**Document ID:** `EON-SPEC-DATA-002`  
**Phase:** Phase 2 — System Architecture and Engineering Design  
**Sub-phase:** 2.8 — Design Data Architecture  
**Status:** Approved Engineering Architecture Specification  
**Version:** 1.0.0  
**Classification:** Technical Architecture Specification  
**Document Owner:** Principal Software Architect  
**Related Documents:**
- `docs/architecture/DATA_ARCHITECTURE.md` (`EON-ARCH-DATA-001`)

---

## 1. Executive Summary

This document details the trade-off evaluation and architectural rationale for storage engine selections across the OVIC EON platform.

---

## 2. Storage Engine Trade-Off Evaluation

```text
+=======================================================================================+
| Target Workload       | Selected Technology  | Trade-Off Rationale & Rejected Options |
+=======================================================================================+
| Static Configuration  | YAML + Pydantic v2   | Human-readable; validated at startup.  |
|                       |                      | Rejected: JSON (no comments), INI.     |
+-----------------------+----------------------+----------------------------------------+
| Volatile Perception & | In-Memory Pre-alloc  | Zero disk write; eliminates flash wear;|
| Audio Ring Buffers    | Circular RAM Buffer  | Sub-microsecond access latency.        |
+-----------------------+----------------------+----------------------------------------+
| Persistent Interaction| Embedded SQLite with | Zero daemon overhead; ACID compliant;   |
| Memory & Preferences  | SQLCipher (WAL Mode) | WAL mode prevents reader/writer locks. |
|                       |                      | Rejected: PostgreSQL/MySQL (heavy RAM).|
+-----------------------+----------------------+----------------------------------------+
| Event Bus In-Flight   | Bounded Python FIFO  | 108,000 ev/s throughput; sub-millisecond|
| Message Buffering     | PriorityQueue        | dispatch. Rejected: Redis/RabbitMQ.    |
+=======================================================================================+
```

### Storage Quota Enforcement
Persistent SQLite storage is capped at a configurable quota (default: $500\text{ MB}$). When storage reaches $90\%$ capacity, the oldest un-starred episodic records are automatically pruned via FIFO eviction.
