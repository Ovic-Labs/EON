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
3. **Cryptographic Deletion Reality:** Grounded in mathematical unrecoverability via per-subject AES-256-GCM envelope encryption and key destruction. EON explicitly rejects false claims of physical flash block zeroing on commercial SSDs.
4. **Granular Consent & Context Isolation:** Complete separation between anonymous passersby, short-term interaction sessions, and consented long-term user personalization.

> [!IMPORTANT]
> **Implementation and Certification Status:** This specification establishes the complete privacy architecture for EON. In accordance with Phase 2 governance rules, all privacy capabilities are classified as **DESIGNED — NOT IMPLEMENTED**. No formal GDPR, CCPA, or EU AI Act legal compliance certifications are claimed.

---

## 2. Privacy Lifecycle and Data Flow Topology

```text
+-------------------------------------------------------------------------+
|                  Perception Ingress (Volatile Ring Buffer)              |
|   - 1080p Camera Feed      - 16 kHz Microphone Stream                   |
|   - Ring Buffer (/dev/shm) : Strictly In-Memory (Zero Disk I/O)         |
+-------------------------------------------------------------------------+
                                    |
                    (Feature Extraction & Immediate Drop)
                                    v
+-------------------------------------------------------------------------+
|                Transient Low-Level Observation Extractors               |
|   - Facial Landmark Points (2D coords)  - Acoustic Pitch / Formants     |
|   - Raw media overwritten in circular ring buffer within <= 100 ms      |
+-------------------------------------------------------------------------+
                                    |
                    (Probabilistic Inference Pipeline)
                                    v
+-------------------------------------------------------------------------+
|                Affective State Estimation (ERS / EMS)                   |
|   - Output: Uncertain Observation (Valence, Arousal, Confidence)        |
|   - Invariant: is_definitive_claim = false; non-diagnostic             |
+-------------------------------------------------------------------------+
                                    |
                                    v
+-------------------------------------------------------------------------+
|                 Shared Context Storage Gate (Consent Arbiter)           |
|                                                                         |
|    [User Consented?]                                                    |
|      /             \                                                    |
|   [YES]           [NO]                                                  |
|    /                 \                                                  |
|   v                   v                                                 |
| [Encrypted Store]   [Ephemeral Session Cache]                           |
| - AES-256-GCM       - Discarded immediately upon user departure         |
| - Per-Subject DEK   - Zero disk persistence                             |
+-------------------------------------------------------------------------+
```

---

## 3. Epistemic Modesty and Emotional Observability

Affective science demonstrates that facial expressions and vocal prosody do not have 1:1 deterministic mappings to a human's internal subjective feelings (e.g., smiling does not always indicate happiness). EON formalizes this reality in code contracts:
- Emotion recognition outputs are labeled `EmotionObservation`, not `EmotionalTruth`.
- Every observation carries a `float confidence` and an explicit boolean `bool is_definitive_claim = false;`.
- Downstream behavioral engines (EMS, ERE, SIE) treat observations as probabilistic hypotheses that decay rapidly over time ($t_{1/2} \approx 3.0\text{ seconds}$) unless reinforced by ongoing multimodal evidence.

---

## 4. Traceability Matrix

| Requirement ID | Architectural Requirement | Specification Document |
|---|---|---|
| `PRD-REQ-010` | Privacy-by-design, zero raw media retention, and consent | `PRIVACY_DATA_MINIMIZATION.md` |
| `SRS-PRIV-001` | Granular user consent and right to be forgotten | `PRIVACY_CONSENT_MODEL.md` |
| `ADR-026` | Architecture Decision Record: Privacy Boundaries & Shredding | `ADR-026-privacy-by-design-and-cryptographic-boundaries.md` |
