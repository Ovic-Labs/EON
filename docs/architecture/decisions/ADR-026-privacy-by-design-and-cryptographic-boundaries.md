# ADR-026: Privacy-by-Design and Cryptographic Boundaries

**Document ID:** `EON-ADR-026`  
**Date:** 2026-11-24  
**Status:** `APPROVED`  
**Deciders:** Antigravity Engineering Architecture Team  
**Scope:** Privacy, Ethics, Affective Computing, Cryptographic Deletion  

---

## 1. Context and Problem Statement

Robotic affective computing processes human faces, voices, and emotional reactions. Inappropriate handling creates severe risks of surveillance, psychological profiling, and regulatory non-compliance under GDPR and the EU AI Act.

## 2. Decision

We decide to mandate a strict **Privacy-by-Design Architecture**:
1. **Zero Raw Media Disk Retention:** Camera feeds and audio buffers exist strictly in volatile RAM ring buffers (`/dev/shm`) and are discarded within $\le 100\text{ ms}$; zero raw media is written to non-volatile disk.
2. **Epistemic Modesty Contract:** Inferred emotions are explicitly marked as uncertain behavioral observations (`is_definitive_claim = false`). Medical diagnosis or covert psychological profiling is architecturally prohibited.
3. **Truth-in-Specification Deletion:** Replaces false physical SSD zeroing claims with cryptographic erasure via per-subject DEK destruction, in-memory zeroization, and SQLite `PRAGMA wal_checkpoint(TRUNCATE)`, formalized in a multi-tier deletion lifecycle.
4. **Granular Consent:** 3-tier model separating Anonymous Passerby, Ephemeral Session, and Consented Personalization.

## 3. Alternatives Considered

- *Alternative A: Cloud Privacy Filtering.* Rejected: Exposing raw media over network wires violates privacy-by-design.
- *Alternative B: Claiming Physical Flash Sanitization.* Rejected: Technically false due to modern SSD Flash Translation Layer wear-leveling algorithms.

## 4. Consequences and Implications

- **Positive:** Complete regulatory alignment with GDPR/EU AI Act, robust protection against biometric theft, high user trust.
- **Negative:** Requires strict discipline across all model adapter pipelines to prevent accidental disk caching.
- **Security Implications:** Reduces data at rest to anonymized/pseudonymous ciphertext.
- **Privacy Implications:** Fundamental core invariant of the entire OVIC EON product.
- **Performance Implications:** Volatile memory ring buffers maximize throughput and reduce disk write wear.
- **Related ADRs:** ADR-011, ADR-015, ADR-017, ADR-025.
- **Supersession History:** Formalizes and expands the privacy baseline of ADR-011.
