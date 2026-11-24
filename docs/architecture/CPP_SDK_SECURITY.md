# OVIC EON — C++ SDK Security Specification

**Document ID:** `EON-SPEC-CPP-007`  
**Phase:** Phase 2 — System Architecture and Engineering Design (Sub-phase 2.11)  
**Status:** `DESIGNED — NOT IMPLEMENTED (Phase 2 Architecture Baseline)`  
**Target Audience:** Security Engineers, Systems Programmers  
**Traceability:** `EON-ARCH-CPP-001`, ADR-020, ADR-025  

---

## 1. IPC Security and Access Control

Because `libeonsdk` interfaces directly with EON Core via local IPC (Unix Domain Sockets or Windows Named Pipes), security must be enforced at the transport and process boundary:
1. **Filesystem Socket Permissions:** Unix Domain Sockets (`/var/run/eon/eon.sock` or `/tmp/eon.sock`) are created with restrictive permissions (`0660`), owned by the `eon` service user and `eon-clients` group.
2. **Peer Credential Verification (`SO_PEERCRED` / `SCM_CREDENTIALS`):** On Linux, the core server inspects the connecting client's UID, GID, and PID. Untrusted processes are rejected before handshake.
3. **Client Authentication Handshake:** During `Connect()`, the SDK transmits a client token or cryptographic device identity.
4. **Shared Memory Access Rights:** SHM segments are created with `O_RDWR` only for authorized client and engine processes; segment file descriptors are passed via Unix domain socket file-descriptor passing (`SCM_RIGHTS`) to avoid open filesystem handles.

---

## 2. Memory Hygiene and Buffer Overrun Defenses

- **Strict Bounds Checking:** Every deserialization step validates buffer lengths against declared schema lengths.
- **ASLR and Stack Canaries:** Built with `-fstack-protector-strong -D_FORTIFY_SOURCE=2 -fPIE -pie`.
- **Zeroing of Ephemeral Memory:** Context tokens and sensitive credential buffers are scrubbed using `explicit_bzero` or `SecureZeroMemory` upon destruction.
