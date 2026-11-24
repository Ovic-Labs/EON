# OVIC EON — Privacy Data Classification Specification

**Document ID:** `EON-SPEC-PRIV-002`  
**Phase:** Phase 2 — System Architecture and Engineering Design (Sub-phase 2.17)  
**Status:** `DESIGNED — NOT IMPLEMENTED (Phase 2 Architecture Baseline)`  
**Target Audience:** Data Governance Officers, Security Engineers, Robotics Privacy Architects  
**Traceability:** `EON-ARCH-PRIV-001`, `DATA_PRIVACY_AND_RETENTION.md`, ADR-026  

---

## 1. Twelve-Class Data Sensitivity Taxonomy

Every data structure, observation event, and persistent record in OVIC EON is classified into one of twelve authoritative data sensitivity classes. This taxonomy defines the storage medium, retention lifetime, non-volatile disk permission, cryptographic encryption requirement, and engineering implementation status for every data element:

| Class ID | Sensitivity Class | Description & Examples | Storage Medium | Retention Ceiling | Disk Storage Permitted? | Cryptographic Protection | Engineering Implementation Status |
|---|---|---|---|---|---|---|---|
| **DSC-01** | `RAW_AUDIO` | Microphone audio waveform chunks (16 kHz PCM) | Volatile RAM (`/dev/shm` tmpfs) | $\le 100\text{ ms}$ (frame duration) | **STRICTLY PROHIBITED** | In-memory only; non-swappable | `IMPLEMENTED — TESTED` (Phase 1.2 schemas) |
| **DSC-02** | `RAW_VIDEO` | Camera frames (1080p RGB, depth arrays) | Volatile RAM (`/dev/shm` tmpfs) | $\le 100\text{ ms}$ (frame duration) | **STRICTLY PROHIBITED** | In-memory only; non-swappable | `IMPLEMENTED — TESTED` (Phase 1.2 schemas) |
| **DSC-03** | `FACIAL_BIOMETRICS` | 2D/3D facial landmarks, mesh points, face descriptors | Volatile Ingress Queue / RAM | $\le 500\text{ ms}$ (inference window) | **STRICTLY PROHIBITED** | In-memory only; zeroed post-inference | `IMPLEMENTED — TESTED` (Phase 1.3 EventBus) |
| **DSC-04** | `VOICEPRINT` | Speaker embeddings, vocal pitch, formant vectors | Volatile Ingress Queue / RAM | $\le 500\text{ ms}$ (inference window) | **STRICTLY PROHIBITED** | In-memory only; zeroed post-inference | `IMPLEMENTED — TESTED` (Phase 1.3 EventBus) |
| **DSC-05** | `EMOTIONAL_STATE` | Probabilistic valence/arousal scores, discrete emotion estimates (`is_definitive_claim = false`) | Ephemeral Event Bus / RAM | $\le 30\text{ s}$ (probabilistic decay half-life) | Prohibited unless consented (DSC-10/11) | In-memory volatile structure | `IMPLEMENTED — TESTED` (Phase 1.2 schemas) |
| **DSC-06** | `CONVERSATION_TRANSCRIPT` | ASR speech-to-text transcripts, dialogue utterances | Working Memory / Encrypted SQLite | Duration of active dialogue session (max 120s idle) | Prohibited in raw text; encrypted if consented | AES-256-GCM under Subject DEK | `DESIGNED — NOT IMPLEMENTED` |
| **DSC-07** | `USER_IDENTITY` | Subject ID, display pseudonym, registration metadata | Encrypted SQLite (`context.db`) | Until consent revocation or retention limit | Yes (Encrypted) | AES-256-GCM under Subject DEK | `DESIGNED — NOT IMPLEMENTED` |
| **DSC-08** | `METRICS_TELEMETRY` | System FPS, pipeline latency, CPU/memory quotas, engine health | Local Timeseries / Systemd Log | Rolling 30–90 days | Yes (Plaintext / Aggregated) | None (Redacted anonymized metrics) | `DESIGNED — NOT IMPLEMENTED` |
| **DSC-09** | `SYSTEM_LOGS` | Diagnostic log traces, warning and error events | Systemd Journal / File | Rolling 30 days (max 50 MB x 3) | Yes (Plaintext) | None (Strict automated PII redaction) | `DESIGNED — NOT IMPLEMENTED` |
| **DSC-10** | `DERIVED_EPISODIC` | Summarized interaction episodes, semantic interaction graphs | Encrypted SQLite (`context.db`) | Default 90 days of inactivity | Yes (Encrypted) | AES-256-GCM under Subject DEK | `DESIGNED — NOT IMPLEMENTED` |
| **DSC-11** | `PERSONA_MEMORY` | Learned user preferences, conversational tone affinity | Encrypted SQLite (`context.db`) | Until consent revocation | Yes (Encrypted) | AES-256-GCM under Subject DEK | `DESIGNED — NOT IMPLEMENTED` |
| **DSC-12** | `ENVIRONMENT_MAP` | Semantic spatial anchors, social interaction zones | Encrypted SQLite (`context.db`) | Managed by robot spatial navigation layer | Yes (Encrypted) | System-level AES-256-GCM under KEK | `DESIGNED — NOT IMPLEMENTED` |

---

## 2. Storage Prohibition and Runtime Interception

The EON Core Shared Context Manager actively validates the data sensitivity classification before executing any filesystem write operation:
- Attempting to pass `RAW_AUDIO`, `RAW_VIDEO`, `FACIAL_BIOMETRICS`, or `VOICEPRINT` data to any persistent storage interface raises a fatal runtime exception (`EON_ERR_PRIVACY_STORAGE_VIOLATION`), terminating the write operation immediately.
- Attempting to persist unconsented `EMOTIONAL_STATE` or `CONVERSATION_TRANSCRIPT` records beyond the ephemeral session boundary triggers immediate memory reclamation.

---

## 3. Engineering Status Legend

In accordance with EON engineering governance, all privacy and data classification capabilities are tagged with one of four formal status indicators:
1. `DESIGNED — NOT IMPLEMENTED`: Fully specified in architecture deliverables; implementation deferred to runtime development phases.
2. `IMPLEMENTED — NOT TESTED`: Code implemented but awaiting automated test qualification.
3. `IMPLEMENTED — TESTED`: Code implemented, verified by passing automated unit/integration test suites (e.g., Phase 1 data models and EventBus sanitization).
4. `INDEPENDENTLY VERIFIED`: Validated by an independent third-party audit or formal security/compliance certification body (no current components hold this status).
