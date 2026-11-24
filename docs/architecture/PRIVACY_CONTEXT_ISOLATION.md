# OVIC EON — Privacy Context Isolation Specification

**Document ID:** `EON-SPEC-PRIV-005`  
**Phase:** Phase 2 — System Architecture and Engineering Design (Sub-phase 2.17)  
**Status:** `DESIGNED — NOT IMPLEMENTED (Phase 2 Architecture Baseline)`  
**Target Audience:** Cognitive Systems Engineers, Software Architects  
**Traceability:** `EON-ARCH-PRIV-001`, `CONTEXT_PRIVACY_AND_RETENTION.md`, ADR-026  

---

## 1. Subject and Session Boundary Isolation

In multi-user robotics environments (e.g., family living room, shared hospital ward, classroom), context cross-talk between different humans is a major privacy vulnerability:

```text
+-------------------------------------------------------------------------+
|                  Subject Isolation Memory Model                         |
|                                                                         |
|  +--------------------------------+  +--------------------------------+ |
|  | Context Boundary: User A       |  | Context Boundary: User B       | |
|  | - Subject UUID: a1b2...        |  | - Subject UUID: c3d4...        | |
|  | - Dedicated Session Memory     |  | - Dedicated Session Memory     | |
|  | - Encrypted with DEK_A         |  | - Encrypted with DEK_B         | |
|  +--------------------------------+  +--------------------------------+ |
|                 ^                                  ^                    |
|                 |                                  |                    |
|                 +-----------------+----------------+                    |
|                                   |                                     |
|             [Shared Context Access Control Arbiter]                     |
|      (Enforces zero read/write across disparate subject UUIDs)          |
+-------------------------------------------------------------------------+
```

---

## 2. Session Expiration Policies

When a user ceases interacting with the robot:
1. **Engagement Timeout:** If no face or voice is detected for 60 seconds, the active interaction session enters `EXPIRING` state.
2. **Volatile Scrubbing:** After 120 seconds of continuous absence, all ephemeral session tokens, temporary conversation scratchpads, and short-term affect dynamics are scrubbed from RAM.
3. **No Unconsented Spillover:** When a new person approaches, the robot starts with a fresh, neutral cognitive slate; context from the previous user is inaccessible.
