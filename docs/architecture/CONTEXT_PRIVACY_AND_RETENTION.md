# OVIC EON — Context Privacy and Retention Policy

**Document ID:** `EON-POL-CTX-002`  
**Phase:** Phase 2 — System Architecture and Engineering Design  
**Sub-phase:** 2.6 — Design Shared Context Management  
**Status:** Approved Engineering Architecture Specification  
**Version:** 1.0.0  
**Classification:** Technical Architecture Specification  
**Document Owner:** Principal Software Architect  
**Related Documents:**
- `docs/architecture/SHARED_CONTEXT_ARCHITECTURE.md` (`EON-ARCH-CTX-001`)
- `docs/architecture/ARCHITECTURE_CONSTRAINTS.md` (`EON-ARCH-CONST-001`)

---

## 1. Executive Summary

This specification establishes the privacy-by-design requirements, cryptographic key lifecycles, and retention limits governing context storage.

---

## 2. Cryptographic Storage and Verifiable Deletion

1. **Envelope Encryption:** Context records in persistent storage are encrypted using SQLCipher / AES-256-GCM. Each user profile possesses a unique Data Encryption Key (DEK).
2. **Cryptographic Shredding (`CryptoShredder`):** Upon receiving an authorized deletion request, EON destroys the user's DEK from the secure key store.
3. **Realistic Erasure Boundaries:** EON explicitly recognizes hardware storage limitations:
   - Cryptographic shredding renders encrypted data permanently decipherable even if ciphertext remains in flash SSD wear-leveling blocks or backup snapshots.
   - EON does not claim physical magnetic demagnetization or flash-cell zeroing on third-party host SSDs.
4. **Zero Raw Media Retention:** Raw camera video frames and PCM audio buffers must **never** be saved to context storage.
