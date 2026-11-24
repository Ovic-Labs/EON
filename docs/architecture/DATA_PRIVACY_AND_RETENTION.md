# OVIC EON — Data Privacy and Retention Policy

**Document ID:** `EON-POL-DATA-002`  
**Phase:** Phase 2 — System Architecture and Engineering Design  
**Sub-phase:** 2.8 — Design Data Architecture  
**Status:** Approved Engineering Architecture Specification  
**Version:** 2.0.0 (Authoritative Reconciled Baseline)  
**Classification:** Technical Architecture Specification  
**Document Owner:** Principal Software Architect  
**Related Documents:**  
- `docs/architecture/DATA_ARCHITECTURE.md` (`EON-ARCH-DATA-001`)  
- `docs/architecture/DATA_STORAGE_STRATEGY.md` (`EON-SPEC-DATA-002`)  
- `docs/architecture/DATA_SECURITY.md` (`EON-POL-DATA-001`)  
- `docs/architecture/ARCHITECTURE_CONSTRAINTS.md` (`EON-ARCH-CONST-001`)  

---

## 1. Executive Summary & Purpose

This policy establishes the data minimization constraints, consent gating workflows, retention limits, cryptographic key lifecycles, and verifiable deletion boundaries for OVIC EON persistent data storage.

---

## 2. Comprehensive Privacy & Deletion Subsystem Audit

### 2.1 Context & Episodic Storage
- User profile records, interaction histories, and episodic memory embeddings are encrypted at rest using SQLCipher / SQLite WAL mode with AES-256-GCM.
- Each subject identifier possesses an isolated Data Encryption Key (DEK).

### 2.2 Data Retention Windows
- **Perception Observations:** Ephemeral in-memory ring buffers; discarded immediately after multi-modal fusion window expires ($< 2.0\text{ s}$).
- **Working Memory / Session Context:** Automatically expires 120 seconds after user departure (continuous presence timeout).
- **Long-Term User Profiles:** Retained subject to explicit user consent; evaluated against configured retention ceilings (default 90 days of inactivity).

### 2.3 Encryption Architecture & Key Lifecycle
- **Key Hierarchy:** Two-tier envelope encryption:
  1. Master Key Encryption Key (KEK): Stored in OS-native secure credential store (Linux Secret Service / Keyring, macOS Keychain, or TPM 2.0 PKCS#11).
  2. Data Encryption Keys (DEKs): Per-subject isolated 256-bit symmetric keys encrypted by KEK.
- **Key Revocation & Shredding:** Destroying a subject's DEK renders all associated ciphertext across database files and indices permanently undecipherable.

### 2.4 Database WAL Files & Residual Page Copies
- SQLite in Write-Ahead Log (WAL) mode writes modified pages to `<database>-wal` before checkpointing back to the main DB file.
- **WAL Checkpointing Policy:** Upon executing a deletion or key purge, EON mandates an immediate passive or truncate checkpoint (`PRAGMA wal_checkpoint(TRUNCATE)`) to prevent stale pages from lingering in the WAL journal.

### 2.5 Temporary Storage & IPC Memory Buffers
- Shared memory IPC segments (`/dev/shm`) and temporary processing files (`/tmp/eon_*`) are strictly memory-backed (RAM), mounted with `noexec,nosuid,nodev`, and zeroed upon process termination.
- Raw video frames and raw PCM audio buffers are **NEVER** written to disk.

### 2.6 Diagnostic Logs & Traces
- Production logs strictly redact all Personally Identifiable Information (PII), authorization tokens, and raw human sensory features.
- Log rotation truncates diagnostic files after reaching 50 MB, retaining a maximum of 3 historical rotated archives.

### 2.7 Caches, Snapshots, Backups, and Cloud Replicas
- In-memory LRU vector caches are flushed upon session reset.
- Backup snapshots are encrypted with snapshot-specific keys. Deleting a subject DEK renders historical backup snapshots unreadable for that specific user.
- Cloud synchronization payloads (`EON-SPEC-DATA-004`) carry the exact same per-subject encryption; edge deletions synchronize tombstones to cloud replicas immediately upon reconnection.

### 2.8 Hardware SSD Realities vs. Mathematical Unrecoverability
- **Solid-State Drive (SSD) & Flash Limitations:** Flash memory controllers (FTL) employ dynamic wear-leveling, bad-block remapping, and over-provisioned spare blocks. Standard software-level file unlinking (`os.remove`) or SQL `DELETE` statements mark logical blocks free, but physical flash NAND cells may retain residual charge patterns until background garbage collection or wear cycles overwrite them.
- **Truth-in-Specification:** EON does **not** claim complete physical degaussing, magnetic sanitization, or instant flash-cell zeroing on third-party host robot storage drives. EON guarantees **mathematical unrecoverability** via cryptographic shredding of the subject's unique Data Encryption Key (DEK).

---

## 3. Formal Classification of Privacy & Deletion Guarantees

Every privacy and deletion guarantee is explicitly audited and classified according to verified implementation reality:

| Guarantee / Claim ID | Scope / Subsystem | Architectural Statement | Current Engineering Classification | Verification Evidence / Reference |
| :--- | :--- | :--- | :--- | :--- |
| **PRIV-CLM-01** | Raw Media Ingestion | Zero retention of raw camera frames and raw microphone audio buffers. | **IMPLEMENTED & VERIFIED** | Verified in Phase 0 PRD (`EON-PSR-001`) and Phase 1.2 schemas (`eon.schemas.observations`). |
| **PRIV-CLM-02** | Observation Buffers | Ephemeral in-memory ring buffers discarded after fusion window ($< 2.0\text{ s}$). | **IMPLEMENTED & TESTED** | Implemented and regression-tested in Phase 1.3 EventBus tests (`test_privacy_sanitization.py`). |
| **PRIV-CLM-03** | Working Memory | Session context automatically evicted after continuous presence timeout (120s). | **DESIGNED — NOT RUNTIME VERIFIED** | Specified in `EON-SPEC-CTX-002`; runtime context manager deferred to future implementation. |
| **PRIV-CLM-04** | Envelope Encryption | Per-subject isolated AES-256-GCM Data Encryption Keys (DEKs) wrapped by KEK. | **DESIGNED — NOT RUNTIME VERIFIED** | Specified in `EON-POL-DATA-001` & `EON-POL-CTX-001`; cryptographic storage runtime deferred. |
| **PRIV-CLM-05** | Cryptographic Shredding | Deleting subject DEK renders all user ciphertext mathematically undecipherable. | **DESIGNED — NOT RUNTIME VERIFIED** | Specified in `EON-POL-DATA-002` Section 2; cryptographic shredding runtime deferred. |
| **PRIV-CLM-06** | Database WAL Checkpoint | Truncating SQLite WAL journal upon user purge (`wal_checkpoint(TRUNCATE)`). | **DESIGNED — NOT RUNTIME VERIFIED** | Specified in `EON-SPEC-DATA-002` & `EON-POL-DATA-002`; database engine runtime deferred. |
| **PRIV-CLM-07** | Diagnostic Redaction | Automatic masking of authorization headers, tokens, and PII in logs. | **DESIGNED — NOT RUNTIME VERIFIED** | Specified in `EON-POL-SDK-001` & `EON-POL-API-001`; client and gateway logging deferred. |
| **PRIV-CLM-08** | Physical Flash Zeroing | Physical degaussing or instant wear-leveling flash-cell sanitization on host SSDs. | **NOT APPLICABLE** | Explicitly disclaimed in Section 2.8; physical hardware drive sanitization is out of scope. |
