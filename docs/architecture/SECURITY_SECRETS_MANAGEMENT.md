# OVIC EON — Security Secrets Management Specification

**Document ID:** `EON-SPEC-SEC-006`  
**Phase:** Phase 2 — System Architecture and Engineering Design (Sub-phase 2.16)  
**Status:** `DESIGNED — NOT IMPLEMENTED (Phase 2 Architecture Baseline)`  
**Target Audience:** Security Engineers, DevOps  
**Traceability:** `EON-ARCH-SEC-001`, ADR-025  

---

## 1. Secrets Handling and Storage Rules

1. **Zero Hardcoded Secrets:** No API keys, symmetric master keys, passwords, or private certificates are ever committed to source code or embedded in compiled binaries.
2. **Hardware Security Module (TPM 2.0 / PKCS#11):** Private keys for device mTLS certificates and KEK master keys are sealed to TPM PCR registers (verifying Secure Boot integrity before unsealing).
3. **In-Memory Hygiene:** Memory buffers holding cryptographic secrets are allocated using `mlock()` to prevent paging to swap space, and overwritten with `explicit_bzero` immediately after use.
