# OVIC EON — Privacy Retention and Deletion Specification

**Document ID:** `EON-SPEC-PRIV-004`  
**Phase:** Phase 2 — System Architecture and Engineering Design (Sub-phase 2.17)  
**Status:** `DESIGNED — NOT IMPLEMENTED (Phase 2 Architecture Baseline)`  
**Target Audience:** Database Engineers, Systems Reliability Architects, Compliance Officers  
**Traceability:** `EON-ARCH-PRIV-001`, `DATA_PRIVACY_AND_RETENTION.md`, ADR-026  

---

## 1. Physical SSD Wear-Leveling and Truth-in-Specification

Traditional privacy policies frequently claim "physical deletion" or "secure zeroing of hard drive sectors" when a user requests data deletion.

> [!WARNING]
> **Truth-in-Specification Principle:** On modern solid-state drives (SSDs, eMMC, NVMe, UFS) deployed on robotic computers, the underlying **Flash Translation Layer (FTL)** dynamically redirects block writes to distribute wear across physical flash cells. An operating system or application cannot guarantee that a specific physical NAND flash block has been zeroed merely because `DELETE FROM table` was executed.

---

## 2. Mathematical Guarantee via Cryptographic Shredding

To resolve this physical reality, EON achieves complete unrecoverability through **cryptographic shredding**:

```text
[User Issues Deletion Request: "Forget Me"]
                   |
                   v
   +------------------------------------+
   | 1. Locate Subject DEK in Key Table |
   +------------------------------------+
                   |
                   v
   +------------------------------------+
   | 2. Overwrite DEK with Random Noise |
   |    (DEK completely unrecoverable)  |
   +------------------------------------+
                   |
                   v
   +------------------------------------+
   | 3. SQLite Row Deletion & Truncate  |
   |    PRAGMA wal_checkpoint(TRUNCATE) |
   +------------------------------------+
                   |
                   v
   +------------------------------------+
   | RESULT: Ciphertext blocks remaining|
   | on physical flash wear-level pool  |
   | are mathematically undecipherable. |
   +------------------------------------+
```

Even if an adversary extracts raw NAND flash chips using hardware desoldering techniques, the remaining ciphertext data cannot be decrypted without the destroyed DEK (which requires breaking AES-256-GCM, infeasible under known physics).
