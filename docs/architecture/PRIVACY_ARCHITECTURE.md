# OVIC EON — Privacy Architecture Specification

**Document ID:** `EON-ARCH-PRIV-001`  
**Phase:** Phase 2 — System Architecture and Engineering Design (Sub-phase 2.17)  
**Status:** `DESIGNED — NOT IMPLEMENTED (Phase 2 Architecture Baseline)`  
**Target Audience:** Privacy Engineers, Compliance Officers, Robotics Ethics Boards, System Architects  
**Traceability:** PRD Section 4.5, SRS-PRIV-001 through SRS-PRIV-010, ADR-026, ADR-014  

---

## 1. Executive Summary and Privacy-by-Design Philosophy

The **OVIC EON Privacy Architecture** establishes the privacy-by-design framework for human-facing robotics systems equipped with affective and social intelligence capabilities.

Robots interact with humans in deeply intimate, high-vulnerability physical environments: homes, hospital wards, eldercare facilities, classrooms, and workplaces. Without rigorous architectural privacy boundaries, affective computing risks degenerating into invasive surveillance, covert psychological profiling, or behavioral manipulation.

EON is engineered upon four non-negotiable architectural privacy pillars:
1. **Zero Raw Media Retention:** Raw visual camera frames, RGB-D depth arrays, and microphone audio waveforms exist exclusively in volatile memory ring buffers (`/dev/shm`) and are **never written to secondary non-volatile storage** by default.
2. **Epistemic Modesty & Non-Diagnostic Guarantee:** Affective state estimates are treated strictly as **uncertain, context-dependent behavioral observations** (`is_definitive_claim = false`). EON prohibits medical diagnosis, psychiatric profiling, or emotion truth claims.
3. **Cryptographic Erasure and Multi-Tier Deletion Lifecycle:** Grounded in cryptographic erasure via per-subject AES-256-GCM envelope encryption and key destruction. EON explicitly rejects false claims of physical flash block zeroing on commercial SSDs and defines a multi-tier deletion lifecycle distinguishing software guarantees from hardware dependencies.
4. **Granular Consent & Context Isolation:** Complete separation between anonymous passersby, short-term interaction sessions, and consented long-term user personalization across 12 distinct data sensitivity classes.

> [!IMPORTANT]
> **Implementation and Certification Status:** This specification establishes the complete privacy architecture for EON. In accordance with Phase 2 governance rules, all privacy capabilities are classified as **DESIGNED — NOT IMPLEMENTED**. No formal GDPR, CCPA, or EU AI Act legal compliance certifications are claimed.

---

## 2. Multi-Tier Deletion Lifecycle

To reconcile user privacy rights with the physical realities of modern edge storage media (such as NAND flash wear-leveling and write-ahead log journals), EON defines a formal six-tier deletion lifecycle:

```text
+-------------------------------------------------------------------------------+
|                        MULTI-TIER DELETION LIFECYCLE                         |
+-------------------------------------------------------------------------------+
| Tier 1: Logical Deletion                                                      |
|   - Record flagged as tombstoned; immediately excluded from query APIs        |
|   - Software guarantee: Immediate invisibility at application layer           |
+-------------------------------------------------------------------------------+
| Tier 2: Cryptographic Erasure                                                 |
|   - Per-subject Data Encryption Key (DEK) destroyed in secure key store       |
|   - Ciphertext blocks remain cryptographically inaccessible under AES-256-GCM |
|   - Cryptographic guarantee: Computational infeasibility of decryption       |
+-------------------------------------------------------------------------------+
| Tier 3: Storage-Level Physical Overwrite                                      |
|   - SQLite PRAGMA wal_checkpoint(TRUNCATE) flushes and truncates WAL journal   |
|   - SQLite VACUUM / secure page wipe zeroes freed database pages              |
|   - OS page cache flushed to prevent dirty page persistence                   |
|   - Software guarantee: File-level journal and page truncation                |
+-------------------------------------------------------------------------------+
| Tier 4: Hardware-Level Physical Purge                                         |
|   - NVMe Sanitize / ATA Secure Erase / blkdiscard (TRIM) command dispatch     |
|   - Hardware dependency: Flash Translation Layer (FTL) wear-leveling pool     |
|   - Truth-in-Specification: Physical NAND cell wipe depends on host hardware  |
+-------------------------------------------------------------------------------+
| Tier 5: In-Memory Zeroization                                                 |
|   - Volatile buffers, DEK memory pages, and vector caches zeroed explicitly   |
|   - Enforced via sodium_memzero / explicit_bzero and mlock-pinned pages       |
|   - Software guarantee: Zero memory residue across volatile memory segments   |
+-------------------------------------------------------------------------------+
| Tier 6: Backup & Snapshot Expiration Lifecycle                                |
|   - Existing block-level / filesystem snapshots retain encrypted ciphertext   |
|   - Ciphertext in snapshots is inaccessible due to destroyed DEK (Tier 2)     |
|   - Snapshot files physically expire per independently configured schedule   |
|   - Infrastructure guarantee: Decoupled retention and cryptographic shredding |
+-------------------------------------------------------------------------------+
```

---

## 3. Software Guarantees vs. Hardware / OS Dependencies

EON enforces strict truth-in-specification by differentiating what the EON software runtime guarantees versus what depends on the underlying host operating system, filesystem, and hardware controller:

| Dimension | EON Software Runtime Guarantee | Host OS / Filesystem / Hardware Dependency |
|---|---|---|
| **API Invisibility** | Guaranteed: Logical tombstoning excludes subject data from all APIs immediately. | N/A (Handled within EON runtime). |
| **Volatile Media** | Guaranteed: Audio/video ring buffers reside in `/dev/shm` tmpfs; never written to disk. | OS tmpfs configuration; non-swappable RAM via `mlock()`. |
| **Cryptographic Shredding** | Guaranteed: Subject DEK is overwritten with random noise and removed from key table. | Cryptographic primitive security (AES-256-GCM). |
| **Memory Residue** | Guaranteed: Key material and working memory zeroed via `sodium_memzero` on teardown. | OS swap behavior prevented via `mlock()`; compiler does not optimize away zeroing. |
| **Database Journaling** | Guaranteed: `PRAGMA wal_checkpoint(TRUNCATE)` called immediately upon purge. | Filesystem write barriers and SQLite VFS sync implementation. |
| **Physical Flash Erase** | NOT Guaranteed: Software cannot bypass SSD Flash Translation Layer (FTL). | Host SSD controller firmware, NVMe Sanitize, ATA Secure Erase support. |
| **Backup Persistence** | Guaranteed: Historical backup ciphertext is unreadable without subject DEK. | Backup storage retention policy, snapshot rotation schedule. |

---

## 4. Twelve Data Sensitivity Classes

EON architecture categorizes all ingested, processed, and stored data across 12 distinct sensitivity classes, detailed in `PRIVACY_DATA_CLASSIFICATION.md`:
1. `RAW_AUDIO` (microphone waveform chunks, 16 kHz PCM)
2. `RAW_VIDEO` (camera frames, 1080p RGB, depth arrays)
3. `FACIAL_BIOMETRICS` (landmark coordinates, 3D mesh points, face descriptors)
4. `VOICEPRINT` (speaker embeddings, vocal acoustic features)
5. `EMOTIONAL_STATE` (probabilistic valence/arousal/discrete emotion hypotheses)
6. `CONVERSATION_TRANSCRIPT` (ASR text transcripts, dialogue turns)
7. `USER_IDENTITY` (subject ID, name, profile metadata)
8. `METRICS_TELEMETRY` (FPS, latency, CPU/memory usage, engine health)
9. `SYSTEM_LOGS` (redacted diagnostic traces, warning/error events)
10. `DERIVED_EPISODIC` (summarized interaction episodes, episodic memories)
11. `PERSONA_MEMORY` (learned user preferences, social affinity scores)
12. `ENVIRONMENT_MAP` (semantic spatial anchors, social zone boundaries)

---

## 5. Epistemic Modesty and Emotional Observability

Affective science demonstrates that facial expressions and vocal prosody do not have 1:1 deterministic mappings to a human's internal subjective feelings (e.g., smiling does not always indicate happiness). EON formalizes this reality in code contracts:
- Emotion recognition outputs are labeled `EmotionObservation`, not `EmotionalTruth`.
- Every observation carries a `float confidence` and an explicit boolean `bool is_definitive_claim = false;`.
- Downstream behavioral engines (EMS, ERE, SIE) treat observations as probabilistic hypotheses that decay rapidly over time ($t_{1/2} \approx 3.0\text{ seconds}$) unless reinforced by ongoing multimodal evidence.
- Medical diagnosis, psychiatric categorization, and legal truth claims are explicitly prohibited by architectural invariants (`CONST-ETH-001`, `CONST-ETH-002`).

---

## 6. Traceability Matrix

| Requirement ID | Architectural Requirement | Specification Document |
|---|---|---|
| `PRD-REQ-010` | Privacy-by-design, zero raw media retention, and consent | `PRIVACY_DATA_MINIMIZATION.md` |
| `SRS-PRIV-001` | Granular user consent and right to be forgotten | `PRIVACY_CONSENT_MODEL.md` |
| `SRS-PRIV-002` | Multi-tier deletion lifecycle and truthful erasure | `PRIVACY_RETENTION_AND_DELETION.md` |
| `SRS-PRIV-003` | 12-class data sensitivity taxonomy | `PRIVACY_DATA_CLASSIFICATION.md` |
| `ADR-026` | Architecture Decision Record: Privacy Boundaries & Shredding | `ADR-026-privacy-by-design-and-cryptographic-boundaries.md` |
