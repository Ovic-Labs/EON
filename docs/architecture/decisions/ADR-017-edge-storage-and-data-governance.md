# ADR-017: Edge Storage Strategy, Data Governance, and Verifiable Erasure

**Document ID:** `EON-ADR-017`  
**Status:** Approved  
**Date:** 2026-11-23  
**Deciders:** Principal Software Architect, Founder, Engineering Leads  
**Related Requirements:** `EON-NFR-020`, `EON-PSR-005`, `EON-PSR-020`, `EON-ARCH-DATA-001`

---

## 1. Context
Edge robotics platforms operate with limited onboard storage (eMMC or flash SSDs) that degrades under heavy write cycles. Furthermore, robotics deployments operate in privacy-sensitive environments governed by data protection laws (GDPR, CCPA). Storing raw camera feeds or unencrypted databases on edge devices exposes OEMs to catastrophic privacy breaches.

## 2. Problem
How should data storage be structured to eliminate flash wear, protect user privacy, prevent unauthorized data extraction, and support verifiable data erasure?

## 3. Decision
Adopt an **Embedded Serverless Storage Architecture with Zero Raw Media Persistence**:
1. **Volatile RAM Ingestion (`CONST-PRV-001`):** Raw camera video frames and audio chunks exist exclusively in volatile RAM ring buffers and are zero-wiped immediately following feature extraction. Zero raw multimedia is ever written to disk.
2. **Serverless Embedded Relational Storage:** Standardize on embedded SQLite with Write-Ahead Logging (WAL) and SQLCipher for persistent user preferences, eliminating heavy database server daemons.
3. **Cryptographic Shredding (`CONST-PRV-003`):** Every user profile is encrypted with an isolated symmetric key. User deletion requests permanently destroy this key from the secure key store.
4. **Realistic Erasure Boundaries:** Document explicitly that cryptographic key destruction guarantees cryptographic inaccessibility of ciphertext under AES-256-GCM, acknowledging physical SSD wear-leveling realities without making unsupported hardware-level claims.

## 4. Alternatives Considered
1. **Dockerized PostgreSQL or MongoDB Container:** Heavy daemon overhead (>400 MB RAM idle) and high flash write frequency caused by write-ahead logs.
2. **Plaintext SQLite Storage:** Rejected due to lack of encryption at rest, exposing user records to forensic extraction if the robot is physically stolen.

## 5. Consequences
- **Positive:** Bounded disk footprint (<500 MB); minimal flash wear; provable GDPR compliance; zero external database administration.
- **Negative:** SQLite write transactions require serialized single-writer coordination.

## 6. Risks and Mitigations
- **Risk:** Database corruption during sudden robot power brownouts.
- **Mitigation:** SQLite WAL mode with synchronous full checkpointing ensures atomic recovery upon reboot.
