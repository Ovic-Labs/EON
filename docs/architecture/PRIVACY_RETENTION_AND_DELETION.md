# OVIC EON — Privacy Retention and Deletion Specification

**Document ID:** `EON-SPEC-PRIV-004`  
**Phase:** Phase 2 — System Architecture and Engineering Design (Sub-phase 2.17)  
**Status:** `DESIGNED — NOT IMPLEMENTED (Phase 2 Architecture Baseline)`  
**Target Audience:** Database Engineers, Systems Reliability Architects, Compliance Officers  
**Traceability:** `EON-ARCH-PRIV-001`, `DATA_PRIVACY_AND_RETENTION.md`, ADR-026, ADR-014  

---

## 1. Physical Storage Realities and Truth-in-Specification

Traditional privacy specifications frequently claim "instant physical deletion" or "guaranteed physical overwriting of flash cells" upon user deletion requests.

> [!WARNING]
> **Truth-in-Specification Principle:** Modern solid-state drives (NVMe, SATA SSD, eMMC, UFS) deployed on robotic computers utilize a **Flash Translation Layer (FTL)**. The FTL dynamically redirects logical block addresses (LBAs) across physical NAND flash cells to balance write cycles (wear-leveling), remaps bad blocks, and maintains over-provisioned spare cell pools.
>
> Consequently, an application or operating system cannot guarantee that executing `DELETE FROM table`, `unlink()`, or single-pass block overwriting physically zeroes every residual charge pattern across NAND cells. EON rejects false claims of physical zeroing and instead implements a rigorous **Multi-Tier Deletion Lifecycle** centered on cryptographic erasure.

---

## 2. Multi-Tier Deletion Lifecycle

EON reconciles privacy rights (such as GDPR "Right to be Forgotten") with edge storage physics through six sequential tiers:

```text
[User Deletion Request: "Forget Subject Data"]
                     |
                     v
+-------------------------------------------------------------+
| Tier 1: Logical Deletion                                    |
| - Mark subject records as tombstoned in SQLite context.db   |
| - Immediate exclusion from all query and inference APIs     |
+-------------------------------------------------------------+
                     |
                     v
+-------------------------------------------------------------+
| Tier 2: Cryptographic Erasure                               |
| - Locate subject Data Encryption Key (DEK) in Key Table     |
| - Overwrite DEK in memory using sodium_memzero()            |
| - Destroy wrapped DEK in database with random noise         |
| - Invalidate DEK in all active engine key caches            |
| - RESULT: Ciphertext is cryptographically inaccessible      |
+-------------------------------------------------------------+
                     |
                     v
+-------------------------------------------------------------+
| Tier 3: Storage-Level Physical Overwrite                    |
| - Execute PRAGMA wal_checkpoint(TRUNCATE) on SQLite DB      |
| - Run PRAGMA incremental_vacuum / VACUUM to zero free pages |
| - Flush OS page cache via syncfs() / posix_fadvise()        |
+-------------------------------------------------------------+
                     |
                     v
+-------------------------------------------------------------+
| Tier 4: Hardware-Level Physical Purge                       |
| - Dispatch blkdiscard (TRIM) to host storage driver         |
| - Qualify NVMe Sanitize / ATA Secure Erase as hardware-     |
|   dependent host capabilities (outside EON runtime scope)   |
+-------------------------------------------------------------+
                     |
                     v
+-------------------------------------------------------------+
| Tier 5: In-Memory Zeroization                               |
| - Explicitly zero working memory buffers and embeddings     |
| - Prevent swap-to-disk leaks via mlock() pinned pages       |
+-------------------------------------------------------------+
                     |
                     v
+-------------------------------------------------------------+
| Tier 6: Backup Expiration Lifecycle                         |
| - Historical volume snapshots retain encrypted ciphertext   |
| - Ciphertext unreadable due to destroyed DEK (Tier 2)       |
| - Snapshots physically purged per backup rotation schedule  |
+-------------------------------------------------------------+
```

---

## 3. Detailed Deletion Tier Specifications

### 3.1 Tier 1: Logical Deletion
- **Trigger:** REST API `POST /api/v1/context/{subject_id}/purge`, ROS 2 service call `eon_msgs/srv/PurgeSubjectContext`, or voice-initiated privacy command.
- **Action:** EON Core Context Manager marks the subject's record tombstoned (`status = PURGED`, `tombstone_timestamp = UTC_NOW`).
- **Guarantee:** All subsequent query, search, and context aggregation operations return `NotFound` or `SubjectPurgedError`. No further affective profiling occurs for the subject ID.

### 3.2 Tier 2: Cryptographic Erasure
- **Trigger:** Immediately follows Tier 1 logical tombstoning.
- **Action:**
  1. The 256-bit symmetric Data Encryption Key (DEK) associated with the subject is located in the encrypted key table.
  2. Any in-memory decrypted copies of the DEK held across engine caches are scrubbed using `sodium_memzero()` or `explicit_bzero()`.
  3. The wrapped DEK entry in `context.db` is overwritten with high-entropy cryptographic pseudorandom bytes (from `/dev/urandom`) before the row is deleted.
- **Guarantee:** All ciphertext blocks previously encrypted under the subject DEK (including dialogue turns, episodic embeddings, and persona profiles) become cryptographically inaccessible under AES-256-GCM. Decryption without the destroyed key requires solving the discrete logarithm or brute-forcing $2^{256}$ keyspace, which is computationally infeasible under known physical laws.

### 3.3 Tier 3: Storage-Level Physical Overwrite
- **Trigger:** Immediate post-crypto-erasure maintenance hook.
- **Action:**
  1. **WAL Checkpoint:** SQLite in Write-Ahead Log mode writes changes to `<database>-wal`. EON executes `PRAGMA wal_checkpoint(TRUNCATE)`. This writes committed transactions back to the main database file and truncates the WAL file length to zero bytes, preventing stale plaintext or key ciphertext from lingering in uncommitted journal frames.
  2. **Page Freeing & Zeroing:** EON triggers `PRAGMA auto_vacuum = INCREMENTAL` followed by `PRAGMA incremental_vacuum;` or an offline `VACUUM` maintenance pass to reclaim freed pages.
  3. **OS Page Cache Flush:** EON invokes `syncfs()` and advises the Linux kernel via `posix_fadvise(POSIX_FADV_DONTNEED)` to drop dirty file pages from the operating system buffer cache.
- **Guarantee:** Removes logical file residues from filesystem journals and operating system page buffers.

### 3.4 Tier 4: Hardware-Level Physical Purge
- **Scope & Demarcation:** Robotic edge computers utilize diverse solid-state media (e.g., M.2 NVMe on Jetson Orin, soldered eMMC on embedded boards, SATA SSDs on industrial x86_64 PCs).
- **Action:** If the host block device supports the Linux `FITRIM` ioctl or `blkdiscard` command, EON emits a discard notification for unallocated filesystem blocks.
- **Hardware Dependency Disclaimer:** Physical NAND block erasure, block retirement, and controller-level wear-leveling pools are managed strictly by SSD firmware. Full flash sanitization requires hardware-native commands (NVMe Sanitize / ATA Enhanced Secure Erase) managed at the robot platform provisioning level, which EON software cannot execute or verify directly.

### 3.5 Tier 5: In-Memory Zeroization
- **Action:**
  1. All working memory structures holding subject features (e.g. transient embedding vectors, extracted tokens, recent emotional states) are overwritten with zero bytes using compiler-barrier memory scrubbers (`sodium_memzero()`).
  2. Sensitive buffers containing cryptographic key material or biometric descriptors are allocated within non-swappable memory pools pinned via `mlock()` / `VirtualLock()`, preventing OS kernel swapper processes from writing sensitive memory pages to unencrypted swap partitions or swap files on disk.

### 3.6 Tier 6: Backup & Snapshot Expiration Lifecycle
- **Scope:** Production robotics deployments frequently employ block-level filesystem snapshots (e.g., ZFS snapshots, btrfs subvolumes, systemd system images, or remote rsync mirrors).
- **Reality:** An application-level database deletion cannot alter existing read-only historical volume snapshots.
- **Cryptographic Independence:** Because all user records in snapshots were encrypted with the subject DEK at the time of creation, destroying the DEK in Tier 2 renders the historical snapshots cryptographically unreadable for that subject, even if snapshot image files persist on backup disks.
- **Lifecycle Management:** Snapshots are purged physically according to the host platform's backup retention policy (recommended maximum: 30 days).

---

## 4. Software Guarantees vs. Hardware Dependencies Matrix

| Guarantee Dimension | EON Software Runtime Guarantee | Host OS / Storage Hardware Dependency |
|---|---|---|
| **API Invisibility** | Absolute: Logical tombstone immediately filters subject data. | None (EON application layer). |
| **Volatile Ingress Buffer** | Absolute: Raw audio/video processed strictly in `/dev/shm` tmpfs. | OS tmpfs mount configuration. |
| **Cryptographic Shredding** | Absolute: Subject DEK zeroed in RAM and overwritten in key store. | AES-256-GCM cryptographic strength. |
| **Journal Truncation** | Guaranteed: `PRAGMA wal_checkpoint(TRUNCATE)` executed. | POSIX filesystem write barrier adherence. |
| **Swap Leak Prevention** | Guaranteed: Key pages pinned via `mlock()`. | Kernel RLIMIT_MEMLOCK configuration limits. |
| **Physical Flash Cell Wipe** | Disclaimed: Software cannot guarantee wear-leveling block erasure. | Host SSD controller, NVMe Sanitize, ATA Secure Erase. |
| **Snapshot File Removal** | Disclaimed: Read-only snapshots managed outside SQLite. | Host platform snapshot rotation and expiration policy. |

---

## 5. Engineering Status and Verification Procedures

In accordance with Phase 2 governance rules:
- **Specification Status:** `DESIGNED — NOT IMPLEMENTED (Phase 2 Architecture Baseline)`.
- **Planned Verification Tests (Phase 3):**
  1. `test_crypto_shredding_dek_destruction`: Verify DEK row overwritten and zeroed in memory.
  2. `test_wal_checkpoint_truncate`: Verify `-wal` file size resets to 0 bytes after purge.
  3. `test_ciphertext_inaccessibility`: Confirm that ciphertext records cannot be decrypted after DEK deletion.
  4. `test_mlock_key_buffer_allocation`: Verify that cryptographic key allocations use memory-locked segments.
