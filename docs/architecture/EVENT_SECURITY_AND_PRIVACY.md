# OVIC EON — Event Security and Privacy Specification

**Document ID:** `EON-POL-COMM-001`  
**Phase:** Phase 2 — System Architecture and Engineering Design  
**Sub-phase:** 2.5 — Design Event-Driven Communication  
**Status:** Approved Engineering Architecture Specification  
**Version:** 1.0.0  
**Classification:** Technical Architecture Specification  
**Document Owner:** Principal Software Architect  
**Related Documents:**
- `docs/architecture/EVENT_DRIVEN_COMMUNICATION.md` (`EON-ARCH-COMM-001`)
- `docs/architecture/EVENT_ENVELOPE_SPECIFICATION.md` (`EON-SPEC-ENV-001`)

---

## 1. Executive Summary

This specification establishes the access control rules, payload sanitization standards, and security boundaries governing inter-engine event exchange.

---

## 2. Privacy Classifications and Scrubbing Rules

All event envelopes declare a `DataClassification` metadata tag:
- `DataClassification.PUBLIC`: Non-sensitive diagnostic telemetry (safe for remote dashboards).
- `DataClassification.INTERNAL`: Normal operational events (emotion coordinates, turn actions).
- `DataClassification.CONFIDENTIAL`: Pseudonymous user preferences and session identifiers.
- `DataClassification.RESTRICTED`: Raw transcripts or biometric feature numbers.

**Log Scrubbing Invariant:** Event logging formatters automatically redact all fields marked `RESTRICTED` or `CONFIDENTIAL`.

---

## 3. Publisher and Subscriber Authorization

1. **Topic Sandboxing:** Engines may only publish to topics declared in their boundary contracts. ERS cannot publish to `actuation.*`; ERG cannot publish to `safety.*`.
2. **Replay & Spoofing Mitigation:** All envelopes carry `event_id` and strictly monotonic UTC timestamps. Events with timestamps older than $5.0\text{ s}$ or duplicate `event_id` are rejected as stale replay attempts.
