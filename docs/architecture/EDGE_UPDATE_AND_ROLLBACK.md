# OVIC EON — Edge Update and Rollback Specification

**Document ID:** `EON-SPEC-EDGE-006`  
**Phase:** Phase 2 — System Architecture and Engineering Design (Sub-phase 2.14)  
**Status:** `DESIGNED — NOT IMPLEMENTED (Phase 2 Architecture Baseline)`  
**Target Audience:** Release Engineers, Firmware Engineers, DevOps  
**Traceability:** `EON-ARCH-EDGE-001`, ADR-023  

---

## 1. A/B Dual-Slot Partitioning and Atomic Updates

To prevent robotic systems from being bricked in the field by partial, corrupt, or incompatible software updates:

```text
+-------------------------------------------------------------------------+
|                        Edge Storage Partitions                          |
|                                                                         |
|  +------------------------------+     +------------------------------+  |
|  | Slot A: Active System (v1.0) |     | Slot B: Standby System(v1.1) |  |
|  | (Current running binaries)   |     | (Target of atomic update)    |  |
|  +------------------------------+     +------------------------------+  |
|                 \                                     /                 |
|                  +-----------------+-----------------+                  |
|                                    |                                    |
|                                    v                                    |
|                      [U-Boot / GRUB Bootloader]                         |
|               (Boots Slot B with automatic 3-strike boot                |
|                fallback to Slot A upon kernel / service fault)          |
+-------------------------------------------------------------------------+
```

---

## 2. Rollback Triggers and Schema Migrations

1. **Service Startup Watchdog:** If the updated EON daemon fails to notify `systemd` within 30 seconds of system boot, the bootloader counter triggers an immediate automatic rollback to the previous known-good partition.
2. **Database Schema Versioning:** SQLite databases use monotonic schema versioning (`PRAGMA user_version`). Backwards-incompatible migrations create an automatic atomic snapshot (`context.db.backup`) prior to applying migration steps. If migration fails, the database restores the backup atomically.
