# OVIC EON — Context Privacy and Retention Policy

**Document ID:** `EON-POL-CTX-002`  
**Phase:** Phase 2 — System Architecture and Engineering Design  
**Sub-phase:** 2.6 — Design Shared Context Management  
**Status:** Approved Engineering Architecture Specification  
**Version:** 2.0.0 (Authoritative Reconciled Baseline)  
**Classification:** Technical Architecture Specification  
**Document Owner:** Principal Software Architect  
**Related Documents:**  
- `docs/architecture/SHARED_CONTEXT_ARCHITECTURE.md` (`EON-ARCH-CTX-001`)  
- `docs/architecture/CONTEXT_ACCESS_CONTROL.md` (`EON-POL-CTX-001`)  
- `docs/architecture/DATA_PRIVACY_AND_RETENTION.md` (`EON-POL-DATA-002`)  
- `docs/architecture/ARCHITECTURE_CONSTRAINTS.md` (`EON-ARCH-CONST-001`)  

---

## 1. Executive Summary

This policy establishes the privacy-by-design requirements, cryptographic key lifecycles, and retention limits governing shared context storage (working memory, dialogue session state, and long-term user profiles).

---

## 2. Cryptographic Storage & Verifiable Deletion

1. **Envelope Encryption:** Context records in persistent storage are encrypted using SQLCipher / AES-256-GCM. Each user profile possesses a unique Data Encryption Key (DEK) wrapped by the host Master Key Encryption Key (KEK).
2. **Cryptographic Shredding (`CryptoShredder`):** Upon receiving an authorized deletion request (`POST /api/v1/memory/purge`), EON permanently destroys the subject's DEK from the secure key store.
3. **Realistic Erasure Boundaries & Truth-in-Specification:** EON explicitly recognizes hardware storage realities:
   - Cryptographic shredding renders encrypted data **permanently undecipherable** even if ciphertext blocks linger in flash SSD wear-leveling blocks or backup snapshots.
   - EON does not claim physical magnetic demagnetization, flash-cell electrical zeroing, or physical destruction of third-party host SSDs.
4. **Zero Raw Media Retention:** Raw camera video frames and PCM audio buffers must **never** be saved to context storage under any circumstances.
5. **Epistemological Qualification:** Emotion observations stored in context are explicitly tagged as probabilistic signals (`confidence: float`, `epistemology: "PROBABILISTIC_OBSERVATION"`), preventing erroneous representation as verified ground-truth medical or psychological facts.

---

## 3. Context Privacy Lifecycle Classification

| Guarantee Scope | Architectural Policy | Engineering Classification | Notes |
| :--- | :--- | :--- | :--- |
| **In-Memory Scrubbing** | Working memory zeroed upon session termination or timeout. | **DESIGNED — NOT RUNTIME VERIFIED** | Context manager runtime deferred to future implementation phase. |
| **Episodic Erasure** | Cryptographic key destruction guarantees mathematical unrecoverability. | **DESIGNED — NOT RUNTIME VERIFIED** | Specified in Section 2; cryptographic shredding runtime deferred. |
| **WAL Cleanup** | Active WAL files forced to truncate upon profile deletion. | **DESIGNED — NOT RUNTIME VERIFIED** | Database persistence layer deferred to future implementation phase. |
| **Physical Drive Zeroing**| Complete NAND flash cell zeroing on third-party robot hardware. | **NOT APPLICABLE** | Disclaimed per Section 2.3; hardware FTL controllers make physical zeroing unverifiable. |
| **Zero Raw Media** | No storage of camera frames or audio audio buffers. | **IMPLEMENTED & VERIFIED** | Enforced by Phase 0 PRD (`EON-PSR-001`) and Phase 1.2 schemas (`eon.schemas`). |
