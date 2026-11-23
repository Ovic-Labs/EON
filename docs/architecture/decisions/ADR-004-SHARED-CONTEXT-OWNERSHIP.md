# ADR-004: Shared Context and Memory Layer Ownership

**Document ID:** `EON-ADR-004`  
**Status:** Approved  
**Date:** 2026-11-23  
**Deciders:** Principal Software Architect, Founder, Engineering Leads  
**Related Requirements:** `EON-FR-025`, `EON-PSR-010` through `EON-PSR-025`, `EON-SRS-070`

---

## 1. Context
Robots require interaction context (participant identity, conversational stage, dialogue slots) to converse coherently. They also benefit from remembering user preferences across encounters. However, privacy regulations (GDPR, CCPA) strictly prohibit unauthorized storage of biometric or personal data, and many robotics deployments (e.g., hospitals, defense) mandate zero persistent storage.

## 2. Problem
Where should context and memory reside in the architecture, who owns it, and how can EON guarantee privacy compliance and operation in privacy-restricted environments?

## 3. Decision
Establish **L6 (Context and Memory Layer)** as a distinct architectural layer separate from L4 Intelligence Engines:
1. **Dual-Tier Memory Model:**
   - **Volatile Working Memory:** Ephemeral in-memory RAM context (active participants, current conversation stage, recent turns). Always enabled; wiped upon session end.
   - **Persistent Episodic & Semantic Memory:** Strictly consent-gated. If consent is absent, persistent storage is completely disabled.
2. **EMS as Cognitive Custodian:** EMS (Emotion Modelling System) is the sole intelligence engine authorized to interact with L6 long-term storage providers. Other engines query EMS via event contracts.
3. **Verifiable Erasure via Cryptographic Shredding:** User records are encrypted with per-user keys. Deletion requests destroy the user key in `CryptoShredder`, rendering backup blocks permanently unrecoverable.

## 4. Alternatives Considered
1. **Embedding Memory Inside Each Individual Engine:** Each engine maintains its own database. Rejected because it fragments user data, prevents centralized GDPR erasure, and creates massive storage overhead.
2. **Mandatory Cloud Database (Vector DB / Firebase):** Rejected because it violates the offline-first execution invariant and introduces privacy compliance risks.

## 5. Consequences
- **Positive:** Centralized privacy governance; verifiable GDPR Article 17 compliance; system functions seamlessly in zero-disk ephemeral mode.
- **Negative:** Engines must query EMS for historical context rather than maintaining local caches.

## 6. Risks and Mitigations
- **Risk:** Database locking during heavy SQLite writes.
- **Mitigation:** SQLite configured with Write-Ahead Logging (WAL) and single-writer async threadpool.
