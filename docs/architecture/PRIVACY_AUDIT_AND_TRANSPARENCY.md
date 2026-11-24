# OVIC EON — Privacy Audit and Transparency Specification

**Document ID:** `EON-SPEC-PRIV-007`  
**Phase:** Phase 2 — System Architecture and Engineering Design (Sub-phase 2.17)  
**Status:** `DESIGNED — NOT IMPLEMENTED (Phase 2 Architecture Baseline)`  
**Target Audience:** Compliance Auditors, Robotics Transparency Researchers  
**Traceability:** `EON-ARCH-PRIV-001`, ADR-026  

---

## 1. Transparency and Subject Access Rights

In compliance with GDPR Article 15 (Right of Access) and California Consumer Privacy Act (CCPA):
1. **User Transparency Query:** A user or operator can query the robot (`GET /api/v1/context/{subject_id}/export`) to receive a human-readable JSON summary of all data retained under their subject profile.
2. **Explanation of Inferred Emotion:** The system can provide a behavioral justification payload explaining which perceptual modalities contributed to an emotion estimate (e.g., `"Primary modality: vocal prosody (pitch variation), weight: 65%"`).

---

## 2. Cryptographic Privacy Audit Log

Every privacy-sensitive action generates an immutable audit record:
- `CONSENT_GRANTED`: Records timestamp, subject UUID, and consented scope.
- `CONSENT_REVOKED`: Records timestamp, subject UUID, and revocation trigger.
- `CRYPTOGRAPHIC_SHRED_EXECUTED`: Records confirmation that DEK was overwritten and WAL truncated.
- `DATA_EXPORTED`: Records data access request fulfillment.
