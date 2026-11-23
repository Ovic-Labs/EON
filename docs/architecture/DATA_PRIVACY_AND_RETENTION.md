# OVIC EON — Data Privacy and Retention Policy

**Document ID:** `EON-POL-DATA-002`  
**Phase:** Phase 2 — System Architecture and Engineering Design  
**Sub-phase:** 2.8 — Design Data Architecture  
**Status:** Approved Engineering Architecture Specification  
**Version:** 1.0.0  
**Classification:** Technical Architecture Specification  
**Document Owner:** Principal Software Architect  
**Related Documents:**
- `docs/architecture/DATA_ARCHITECTURE.md` (`EON-ARCH-DATA-001`)
- `docs/architecture/ARCHITECTURE_CONSTRAINTS.md` (`EON-ARCH-CONST-001`)

---

## 1. Executive Summary

This policy establishes the data minimization constraints, consent gating workflows, retention limits, and verifiable deletion boundaries for OVIC EON.

---

## 2. Verifiable Erasure vs. Hardware Storage Realities

1. **The Physical Flash Memory Dilemma:** Solid-state drives (SSDs) and eMMC flash storage utilize wear-leveling controllers and over-provisioned blocks. Standard software file deletion (`os.remove`) or database `DELETE` commands mark logical blocks free, but physical flash cells may retain old data until garbage collected.
2. **EON's Verified Solution — Cryptographic Shredding:** EON encrypts every user's records with an isolated AES-256 key (`user_dek`). Upon user deletion, EON permanently destroys `user_dek`. Even if residual encrypted bytes linger on flash wear-leveling blocks or backup snapshots, they are rendered mathematically indecipherable.
3. **Explicit Truth-in-Specification:** EON does **not** claim physical degaussing or factory sanitization of host robot SSDs. It guarantees that deleted records cannot be recovered through cryptographic key destruction.
