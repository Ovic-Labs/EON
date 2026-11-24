# OVIC EON — Privacy Consent Model Specification

**Document ID:** `EON-SPEC-PRIV-001`  
**Phase:** Phase 2 — System Architecture and Engineering Design (Sub-phase 2.17)  
**Status:** `DESIGNED — NOT IMPLEMENTED (Phase 2 Architecture Baseline)`  
**Target Audience:** Privacy Engineers, Product Managers, Legal Counsel  
**Traceability:** `EON-ARCH-PRIV-001`, ADR-026  

---

## 1. Multi-Tier Consent Framework

Human interaction with autonomous robots encompasses varying degrees of familiarity and engagement. EON enforces three distinct consent tiers:

```text
+-------------------------------------------------------------------------+
| Tier 1: Anonymous Passerby (Zero Consent Required / Zero Storage)      |
| - Individual walks past robot in public space or corridor               |
| - Real-time ephemeral social obstacle avoidance and brief gaze cue     |
| - Zero identity generation, zero disk writes, zero biometric storage    |
+-------------------------------------------------------------------------+
| Tier 2: Ephemeral Interaction Session (Implied / Verbal Consent)        |
| - User approaches robot and initiates conversation ("Hello robot")      |
| - Working memory tracks context during the live dialogue session        |
| - All session context scrubbed from RAM upon user departure (timeout)   |
+-------------------------------------------------------------------------+
| Tier 3: Consented Personalization (Explicit Opt-In Consent)             |
| - User registers for personalized social assistance (e.g., eldercare)   |
| - Requires explicit, informed confirmation via app or vocal prompt      |
| - Context stored in encrypted SQLite database under subject DEK         |
+-------------------------------------------------------------------------+
```

---

## 2. Instantaneous Consent Revocation (Right to be Forgotten)

1. **Revocation Mechanism:** A user or administrator can issue a revocation command via REST API (`POST /api/v1/context/{subject_id}/purge`), ROS 2 service (`eon_msgs/srv/PurgeSubjectContext`), or voice command ("Robot, delete all my data").
2. **Cryptographic Shredding Execution:**
   - The subject’s unique Data Encryption Key (DEK) is overwritten and destroyed in the key table.
   - Associated database records are deleted.
   - An explicit `PRAGMA wal_checkpoint(TRUNCATE)` is executed to purge WAL log residues.
   - Any historical backup containing the ciphertext records becomes mathematically unrecoverable.
