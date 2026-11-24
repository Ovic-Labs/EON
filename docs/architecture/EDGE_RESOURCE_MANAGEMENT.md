# OVIC EON — Edge Resource Management Specification

**Document ID:** `EON-SPEC-EDGE-001`  
**Phase:** Phase 2 — System Architecture and Engineering Design (Sub-phase 2.14)  
**Status:** `DESIGNED — NOT IMPLEMENTED (Phase 2 Architecture Baseline)`  
**Target Audience:** Systems Performance Engineers, Edge Developers  
**Traceability:** `EON-ARCH-EDGE-001`, SRS-PERF-001, ADR-023  

---

## 1. Resource Budgets by Deployment Profile

To prevent EON from starving mission-critical robotic navigation or motion planning processes, edge resources are strictly budgeted:

```text
+-------------------------------------------------------------------------+
|                  Low-Resource Profile Budget (Max 8GB System)           |
|  - EON Total RAM Cap: 2048 MB (cgroups memory.max)                      |
|  - CPU Quota: Max 150% (1.5 cores)                                      |
|  - Shared Memory (/dev/shm): 256 MB                                     |
|  - Local Storage Cap: 2048 MB (encrypted SQLite + logs)                |
+-------------------------------------------------------------------------+
|                  Standard Profile Budget (16GB System)                  |
|  - EON Total RAM Cap: 4096 MB                                           |
|  - CPU Quota: Max 300% (3.0 cores)                                      |
|  - Shared Memory (/dev/shm): 512 MB                                     |
|  - Local Storage Cap: 8192 MB                                           |
+-------------------------------------------------------------------------+
|                  Accelerated Profile Budget (32GB+ System)              |
|  - EON Total RAM Cap: 8192 MB                                           |
|  - CPU Quota: Max 600% (6.0 cores) + GPU allocation                     |
|  - Shared Memory (/dev/shm): 1024 MB                                    |
|  - Local Storage Cap: 16384 MB                                          |
+-------------------------------------------------------------------------+
```

---

## 2. Linux Cgroups v2 Enforcement

Edge resource caps are enforced at the OS level via `cgroups v2` inside the `systemd` service definition:

```ini
[Service]
MemoryAccounting=yes
MemoryHigh=1800M
MemoryMax=2048M
CPUAccounting=yes
CPUQuota=150%
TasksMax=128
OOMScoreAdjust=-500
```

- **`MemoryHigh` (Soft Cap):** When memory reaches 1800 MB, the Linux kernel aggressively reclaims page cache and signals EON to flush volatile caches.
- **`MemoryMax` (Hard Cap):** Prevents edge memory leaks from destabilizing the host robot.
- **`OOMScoreAdjust=-500`:** Ensures background inference workers are terminated before the core EON communication bus.
