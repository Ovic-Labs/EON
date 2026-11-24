# ADR-015: Shared Context Management and Least-Privilege Access

**Document ID:** `EON-ADR-015`  
**Status:** Approved  
**Date:** 2026-11-23  
**Deciders:** Principal Software Architect, Founder, Engineering Leads  
**Related Requirements:** `EON-FR-025`, `EON-PSR-010`, `EON-SRS-070`, `EON-ARCH-CTX-001`

---

## 1. Context
Robots require active conversational state and long-term user preferences to personalize interactions. However, granting engines unrestricted access to a central database creates privacy risks, violates GDPR Article 5 (Data Minimization), and risks accidental leakage of sensitive biometric data.

## 2. Problem
How should context be scoped, categorized, and protected so that engines receive necessary conversational state while strictly enforcing least privilege, consent gating, and verifiable erasure?

## 3. Decision
Adopt a **Scoped Shared Context Architecture with EMS as Sole Memory Custodian**:
1. **Eight Explicit Context Categories:** Context is partitioned into 8 typed categories (Session, Interaction, Short-Term, Long-Term, Environmental, Task, User Preferences, Transient Observations).
2. **Role-Based Engine Access Control:** Only **EMS** has write/delete authority over persistent memory; other engines (ERE, SIE, ERG) possess read-only views filtered by least privilege. Perception engines (ERS, HBU) have zero access to long-term memory.
3. **Cryptographic Shredding for Verifiable Erasure:** User records are encrypted using per-user symmetric keys. Deletion requests destroy the user key in `CryptoShredder`, rendering persistent ciphertext cryptographically inaccessible under AES-256-GCM.
4. **Realistic Erasure Demarcation:** The architecture explicitly recognizes hardware storage realities: cryptographic shredding renders ciphertext cryptographically inaccessible, but cannot claim physical magnetic demagnetization of host SSD blocks.

## 4. Alternatives Considered
1. **Unrestricted Shared Global Blackboard:** Rejected because any compromised or buggy engine could read or overwrite another engine's private state or leak user data.
2. **Per-Engine Siloed Databases:** Rejected because it causes massive data duplication and makes centralized GDPR deletion auditing impossible.

## 5. Consequences
- **Positive:** Provable least-privilege compliance; GDPR Article 17 adherence; centralized conflict resolution.
- **Negative:** Engines must query context through asynchronous contracts.

## 6. Risks and Mitigations
- **Risk:** Stale context returned during rapid turn transitions.
- **Mitigation:** Context records carry `expires_at` and version numbers; stale records are automatically discarded.
