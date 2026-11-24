# ADR-011: Security, Privacy, and Verifiable Data Governance

**Document ID:** `EON-ADR-011`  
**Status:** Approved  
**Date:** 2026-11-23  
**Deciders:** Principal Software Architect, Founder, Engineering Leads  
**Related Requirements:** `EON-PSR-001` through `EON-PSR-086`, `EON-SRS-140`

---

## 1. Context
Robots operating in human spaces (homes, elderly care facilities, hospitals, retail) ingest intimate, sensitive visual and acoustic data. The public and regulatory bodies (EU AI Act, GDPR, HIPAA) demand verifiable technical guarantees that robots do not persist unconsented surveillance data, conduct covert biometric profiling, or fail to honor user deletion rights.

## 2. Problem
How can OVIC EON guarantee privacy by design, prevent unauthorized biometric profiling, ensure verifiable data erasure, and protect system security on edge devices?

## 3. Decision
Adopt a comprehensive **Privacy-by-Design and Security Architecture**:
1. **Zero Raw Biometric Persistence (`CONST-PRV-001`):** Raw camera video frames and PCM audio waveforms are held exclusively in volatile RAM ring buffers in L2/L3 and are zero-wiped immediately following feature extraction. No raw media is ever written to disk or flash storage.
2. **Anti-Profiling Invariant:** No engine maintains facial recognition templates or voiceprint biometric models. Tracking IDs are ephemeral integer tokens reset between sessions. The system is strictly prohibited from inferring psychiatric diagnoses or sensitive demographic traits.
3. **Verifiable Cryptographic Shredding (`CONST-PRV-003`):** Long-term memory records in EMS are encrypted at rest using per-user symmetric AES-256 keys. Deletion requests destroy the user key, rendering ciphertext across backup blocks cryptographically inaccessible without the destroyed key.
4. **Least-Privilege Process Security:** The EON daemon runs under an unprivileged `eon-service` user with locked Linux cgroup memory quotas, read-only root filesystems, and strict Unix socket permissions (`0660`).

## 4. Alternatives Considered
1. **Disk Caching for Debugging:** Storing raw audio/video clips on disk during development. Rejected as too dangerous for production codebases; diagnostic tools must use ephemeral memory tap buffers only.
2. **Standard Database `DELETE` Without Key Destruction:** Standard row deletion leaves traces in database write-ahead logs and flash wear-leveling blocks that can be recovered with forensics. Cryptographic shredding renders ciphertext cryptographically inaccessible, overcoming physical wear-leveling limits.

## 5. Consequences
- **Positive:** Complete GDPR Article 17 and EU AI Act compliance; eliminates enterprise privacy liability; establishes high trust with end users and robotics OEMs.
- **Negative:** Historical debugging of mis-recognized emotions must rely on extracted feature numbers rather than recorded raw video clips.

## 6. Risks and Mitigations
- **Risk:** Forensic recovery of plaintext memory from RAM dumps.
- **Mitigation:** Volatile buffers are explicitly zero-wiped via `ctypes.memset` immediately following feature extraction.
