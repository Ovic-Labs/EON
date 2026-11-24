# OVIC EON — Privacy Data Classification Specification

**Document ID:** `EON-SPEC-PRIV-002`  
**Phase:** Phase 2 — System Architecture and Engineering Design (Sub-phase 2.17)  
**Status:** `DESIGNED — NOT IMPLEMENTED (Phase 2 Architecture Baseline)`  
**Target Audience:** Data Governance Officers, Security Engineers  
**Traceability:** `EON-ARCH-PRIV-001`, `DATA_PRIVACY_AND_RETENTION.md`, ADR-026  

---

## 1. Five-Tier Data Sensitivity Taxonomy

Every data structure and event in EON is classified into one of five sensitivity tiers:

| Tier | Category Name | Examples | Storage Location | Retention Lifetime | Disk Storage Permitted? |
|---|---|---|---|---|---|
| **Tier 1** | Ephemeral Raw Media | 1080p camera frames, raw audio PCM, depth maps | Volatile RAM (`/dev/shm`) | $\le 100\text{ ms}$ (frame duration) | **STRICTLY PROHIBITED** |
| **Tier 2** | Extracted Geometric Features | 2D facial landmarks, gaze angles, audio pitch | Volatile Ingress Queue | $\le 500\text{ ms}$ (inference window) | **STRICTLY PROHIBITED** |
| **Tier 3** | Inferred Affective Estimates | Valence/arousal scores, emotion confidence | Ephemeral Event Bus | $\le 30\text{ seconds}$ (decay half-life) | No (RAM only unless Tier 4) |
| **Tier 4** | Consented Subject Context | Preferred greeting style, interaction frequency | Encrypted SQLite (`context.db`) | Until Consent Revocation | **Yes (AES-256-GCM Encrypted)** |
| **Tier 5** | System Audit & Health Telemetry | Engine state changes, error counts, FPS | Systemd Journal / Log | 30–90 days rolling | Yes (Anonymized plaintext) |

---

## 2. Storage Prohibition Enforcement

The EON Core persistence manager actively verifies the data classification tier before executing any filesystem write. Attempting to pass Tier 1 (raw frames/audio) or Tier 2 (raw landmarks) to the SQLite storage engine raises a fatal runtime contract violation (`EON_ERR_PRIVACY_VIOLATION`), terminating the write operation.
