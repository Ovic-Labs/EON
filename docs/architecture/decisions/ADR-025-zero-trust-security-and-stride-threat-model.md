# ADR-025: Zero-Trust Security Architecture and STRIDE Threat Model

**Document ID:** `EON-ADR-025`  
**Date:** 2026-11-24  
**Status:** `APPROVED`  
**Deciders:** Antigravity Engineering Architecture Team  
**Scope:** Security Architecture, Threat Modeling, Cryptography  

---

## 1. Context and Problem Statement

Robots operate in untrusted physical and local network environments. Compromising an AI emotion engine must never allow an attacker to hijack physical robot actuators, steal biometric data, or compromise adjacent robotics infrastructure.

## 2. Decision

We decide to adopt a comprehensive **Zero-Trust Security Architecture**:
1. Five segregated security domains with three formal trust boundaries (Robot Safety, Core IPC, Cloud).
2. STRIDE threat model covering Spoofing, Tampering, Repudiation, Information Disclosure, Denial of Service, and Elevation of Privilege with automated verification methods.
3. Envelope encryption using hardware TPM 2.0 / secure keyring wrapping per-subject AES-256-GCM Data Encryption Keys.
4. Tamper-evident append-only audit trail with SHA-256 cryptographic hash chaining.
5. Supply chain security via CycloneDX/SPDX SBOMs and Cosign cryptographic signatures.

## 3. Alternatives Considered

- *Alternative A: Perimeter Security Only.* Rejected: Fails when an attacker gains local Wi-Fi or USB physical port access.
- *Alternative B: Single Database Master Key.* Rejected: Precludes individual subject cryptographic shredding.

## 4. Consequences and Implications

- **Positive:** Multi-layered defense-in-depth, verifiable cryptographic deletion, zero actuator attack path.
- **Negative:** Requires cryptographic key management overhead.
- **Security Implications:** Substantially reduces the attack surface across local IPC and network boundaries.
- **Privacy Implications:** Strong protection of at-rest contextual data.
- **Performance Implications:** Negligible hardware-accelerated AES-NI encryption overhead.
- **Related ADRs:** ADR-011, ADR-017, ADR-018, ADR-024, ADR-026.
- **Supersession History:** Supersedes high-level concepts in ADR-011 with formal architectural contracts.
