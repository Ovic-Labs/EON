# OVIC EON — Security Key Management Specification

**Document ID:** `EON-SPEC-SEC-004`  
**Phase:** Phase 2 — System Architecture and Engineering Design (Sub-phase 2.16)  
**Status:** `DESIGNED — NOT IMPLEMENTED (Phase 2 Architecture Baseline)`  
**Target Audience:** Cryptographers, Security Architects  
**Traceability:** `EON-ARCH-SEC-001`, `DATA_PRIVACY_AND_RETENTION.md`, ADR-025  

---

## 1. Two-Tier Envelope Encryption Hierarchy

To safeguard stored user context while enabling instantaneous, cryptographically verified deletion (Right to be Forgotten):

```text
+-------------------------------------------------------------------------+
|                  Master Key Hierarchy (Envelope Encryption)             |
|                                                                         |
|        [Hardware TPM 2.0 / Linux Kernel Keyring (Root-of-Trust)]        |
|                                    |                                    |
|                                    v                                    |
|                [Key Encryption Key (KEK) - 256-bit AES]                 |
|                                    |                                    |
|             +----------------------+----------------------+             |
|             |                      |                      |             |
|             v (Wraps DEK)          v (Wraps DEK)          v (Wraps DEK) |
|         [DEK Subj 1]           [DEK Subj 2]           [DEK Subj N]      |
|             |                      |                      |             |
|             v (Encrypts)           v (Encrypts)           v (Encrypts)  |
|       [Records Subj 1]       [Records Subj 2]       [Records Subj N]    |
+-------------------------------------------------------------------------+
```

---

## 2. Key Lifecycle and Cryptographic Shredding

1. **Generation:** Each subject is assigned a unique, cryptographically random 256-bit Data Encryption Key (DEK) generated via `/dev/urandom` (CSPRNG).
2. **Storage:** The DEK is encrypted under the system KEK using AES-256-GCM and stored in the encrypted key table.
3. **Usage:** When subject data is read or written, the DEK is decrypted into non-swappable volatile RAM pinned via `mlock()` / `VirtualLock()`.
4. **Cryptographic Shredding:** Upon user deletion request:
   - In-memory DEK instances are zeroed using `sodium_memzero()` or `explicit_bzero()`.
   - The encrypted DEK record in `context.db` is overwritten with random bytes and deleted.
   - An immediate `PRAGMA wal_checkpoint(TRUNCATE)` is executed to flush and truncate write-ahead log journals.
   - All persistent ciphertext records referencing that subject become cryptographically inaccessible under AES-256-GCM, overcoming physical SSD wear-leveling limitations.
