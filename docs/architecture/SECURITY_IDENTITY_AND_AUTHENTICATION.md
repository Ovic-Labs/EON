# OVIC EON — Security Identity and Authentication Specification

**Document ID:** `EON-SPEC-SEC-002`  
**Phase:** Phase 2 — System Architecture and Engineering Design (Sub-phase 2.16)  
**Status:** `DESIGNED — NOT IMPLEMENTED (Phase 2 Architecture Baseline)`  
**Target Audience:** Security Architects, IAM Specialists  
**Traceability:** `EON-ARCH-SEC-001`, ADR-025  

---

## 1. Multi-Tier Identity Architecture

Identity in EON is segregated across three distinct operational layers:

```text
+-------------------------------------------------------------------------+
| Tier 1: Hardware Device Identity (Robot Node)                           |
| - Unique Device Certificate (X.509) tied to TPM 2.0 Endorsement Key    |
| - Authenticates robot to optional cloud platform via mTLS               |
+-------------------------------------------------------------------------+
| Tier 2: Local Process & Service Identity (IPC)                          |
| - Linux System User / Group (UID: `eon`, GID: `eon-clients`)            |
| - Verified via kernel `SO_PEERCRED` socket credentials                  |
+-------------------------------------------------------------------------+
| Tier 3: Human Subject Context Identity (Privacy-Preserving)             |
| - Pseudonymous UUIDv4 generated locally (`subject_uuid`)                |
| - Never tied to government IDs or real-world names in plain text        |
+-------------------------------------------------------------------------+
```

---

## 2. IPC Authentication Flow

When a client process initializes `eon::client::EonClient::Connect()`:
1. Client opens Unix Domain Socket connection to `/var/run/eon/eon.sock`.
2. EON Core executes `getsockopt(..., SOL_SOCKET, SO_PEERCRED, &ucred, ...)` to inspect the caller's UID and GID.
3. If caller UID is not root and GID does not match `eon-clients`, connection is severed with `EON_ERR_PERMISSION_DENIED`.
4. Client transmits an application registration token (`client_id`, requested capabilities).
5. Core returns a signed ephemeral session token valid for the duration of the socket connection.
