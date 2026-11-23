# OVIC EON — Data Security Specification

**Document ID:** `EON-POL-DATA-001`  
**Phase:** Phase 2 — System Architecture and Engineering Design  
**Sub-phase:** 2.8 — Design Data Architecture  
**Status:** Approved Engineering Architecture Specification  
**Version:** 1.0.0  
**Classification:** Technical Architecture Specification  
**Document Owner:** Principal Software Architect  
**Related Documents:**
- `docs/architecture/DATA_ARCHITECTURE.md` (`EON-ARCH-DATA-001`)
- `docs/architecture/SECURITY.md`

---

## 1. Executive Summary

This specification defines the cryptographic standards, access control models, and key management lifecycles securing data at rest and in transit.

---

## 2. Security Standards

1. **Encryption at Rest:** AES-256 in Galois/Counter Mode (GCM) via SQLCipher. Master key derived via Argon2id (memory cost: 64MB, time cost: 3 iterations).
2. **Encryption in Transit:** Local IPC uses Unix domain sockets restricted by file permissions (`chmod 0660`). External network interfaces (L9 REST/WebSocket) mandate TLS 1.3.
3. **Key Management:** Master encryption keys are managed through Linux Keyutils kernel keyring or environment injection at runtime; keys are zero-overwritten in RAM upon process exit.
4. **Tamper-Evident Audit Logging:** Security-sensitive events (user deletion, configuration reload, permission failure) append to a SHA-256 hash-chained audit log.
