# OVIC EON — Data Architecture Specification

**Document ID:** `EON-ARCH-DATA-001`  
**Phase:** Phase 2 — System Architecture and Engineering Design  
**Sub-phase:** 2.8 — Design Data Architecture  
**Status:** Approved Engineering Architecture Specification  
**Version:** 1.0.0  
**Classification:** Technical Architecture Specification  
**Document Owner:** Principal Software Architect  
**Related Documents:**
- `docs/architecture/DATA_DOMAIN_MODEL.md` (`EON-SPEC-DATA-001`)
- `docs/architecture/DATA_STORAGE_STRATEGY.md` (`EON-SPEC-DATA-002`)
- `docs/architecture/DATA_SCHEMA_VERSIONING_AND_MIGRATIONS.md` (`EON-SPEC-DATA-003`)
- `docs/architecture/DATA_SECURITY.md` (`EON-POL-DATA-001`)
- `docs/architecture/DATA_PRIVACY_AND_RETENTION.md` (`EON-POL-DATA-002`)
- `docs/architecture/EDGE_AND_CLOUD_DATA_SYNCHRONIZATION.md` (`EON-SPEC-DATA-004`)
- `docs/architecture/decisions/ADR-017-edge-storage-and-data-governance.md` (`EON-ADR-017`)

---

## 1. Executive Summary

This specification establishes the logical and physical data architecture of OVIC EON.

OVIC EON operates under an edge-first, zero-raw-media paradigm. Data is partitioned into explicit operational domains separating transient in-memory sensory data from consent-governed persistent records. Storage technologies are evaluated and selected specifically for edge reliability, low flash wear, zero database server daemon overhead, and cryptographic privacy guarantees.

---

## 2. Core Data Architecture Principles

1. **Transient vs. Persistent Separation:** Sensory observations, audio buffers, and video frames exist strictly in volatile RAM. Only structured factual summaries and explicit user preferences are eligible for persistent storage.
2. **Serverless Embedded Storage:** Storage relies entirely on embedded libraries (SQLite with WAL mode, DuckDB) that execute in-process without requiring background database server processes (e.g. PostgreSQL, Redis, MongoDB).
3. **Envelope Encryption & Crypto-Shredding:** Persistent user data is encrypted using SQLCipher with per-user AES-256 keys. Deletion requests destroy the user key, guaranteeing unrecoverability.
4. **Air-Gapped Autonomous Baseline:** The complete data layer operates locally on the edge robot with zero cloud synchronization required.
