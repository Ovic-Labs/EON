# OVIC EON — Edge Deployment Architecture Specification

**Document ID:** `EON-ARCH-EDGE-001`  
**Phase:** Phase 2 — System Architecture and Engineering Design (Sub-phase 2.14)  
**Status:** `DESIGNED — NOT IMPLEMENTED (Phase 2 Architecture Baseline)`  
**Target Audience:** Edge Systems Engineers, Embedded Linux Developers, Deployment Architects  
**Traceability:** PRD Section 4.5, SRS-ARCH-013, ADR-023, ADR-014, ADR-020  

---

## 1. Executive Summary and Edge-First Mandate

The **OVIC EON Edge Deployment Architecture** defines the packaging, resource partitioning, process supervision, and runtime lifecycle for executing EON directly aboard autonomous robotic computers and embedded edge hardware.

Deployment adheres to three non-negotiable principles:
1. **CPU-First Autonomy:** The entire baseline system must execute deterministically on standard x86_64 and ARM64 CPUs without requiring a discrete GPU or cloud offloading.
2. **Strict Hardware Tiering:** Predefined deployment profiles for low-resource (embedded SBC), standard (robot onboard compute), and accelerated (workstation / Jetson AGX) tiers, fully detailed in `EDGE_RESOURCE_MANAGEMENT.md` and `ARCHITECTURE_RESOURCE_BUDGETS.md`.
3. **Resilience to Edge Hostility:** Protection against abrupt power loss, intermittent sensor dropouts, memory saturation, and network absence.

---

## 2. Deployment Topology and Component Stacking

```text
+-------------------------------------------------------------------------+
|                         Host Robot Hardware                             |
|   (x86_64 Core Ultra / AMD Ryzen Embedded / aarch64 Jetson Orin)         |
+-------------------------------------------------------------------------+
                                    |
+-------------------------------------------------------------------------+
|                  Linux OS Layer (Ubuntu / Debian / Yocto)                |
|  - systemd process supervision   - cgroups v2 resource quotas           |
|  - tmpfs /dev/shm ring buffers   - dm-crypt LUKS encrypted volume       |
+-------------------------------------------------------------------------+
                                    |
+-------------------------------------------------------------------------+
|                       EON Edge Daemon Service                           |
|                                                                         |
|  +---------------------------+       +-------------------------------+  |
|  |     EON Core Daemon       | <---> |   Model Runtime Sandbox       |  |
|  | (IPC, Context, Event Bus) |       | (ONNX Runtime / OpenVINO / TRT)|  |
|  +---------------------------+       +-------------------------------+  |
|               ^                                      ^                  |
|               |                                      |                  |
|  +---------------------------+       +-------------------------------+  |
|  | Local Encrypted SQLite    |       |   Hardware Watchdog Guard     |  |
|  | (Per-subject DEK storage) |       | (Monitors health & memory)    |  |
|  +---------------------------+       +-------------------------------+  |
+-------------------------------------------------------------------------+
```

---

## 3. Standard Deployment Profiles and Headroom

| Profile | Target Compute | Memory Quota | Acceleration | Workload Allocation & Safety Headroom |
|---|---|---|---|---|
| **Low-Resource (Profile A)** | 4-core ARM64 / x86 (e.g. Jetson Orin Nano, Intel N100) | 2048 MB Cap (`MemoryMax`) | CPU-only / INT8 Quantized | 10 FPS Vision, mono audio; $\ge 2000\text{ MB}$ reserved for host robot Nav2/MoveIt |
| **Standard (Profile B)** | 8-core CPU (e.g. Intel Core Ultra 7, AMD Ryzen 7) | 4096 MB Cap (`MemoryMax`) | CPU + NPU / iGPU (OpenVINO) | 15–20 FPS Vision, stereo audio; $\ge 10000\text{ MB}$ reserved for host robot |
| **Accelerated (Profile C)** | 12+ core CPU + GPU (e.g. Jetson AGX Orin 64GB) | 8192 MB Cap (`MemoryMax`) | CUDA / TensorRT | 30 FPS Vision, dense RGB-D; $\ge 24000\text{ MB}$ reserved for host robot |

---

## 4. Traceability Matrix

| Requirement ID | Architectural Requirement | Specification Document |
|---|---|---|
| `PRD-REQ-007` | Embedded edge compatibility without mandatory cloud or GPU | `EDGE_RESOURCE_MANAGEMENT.md` |
| `SRS-ARCH-013` | Deterministic edge process supervision and update rollback | `EDGE_PROCESS_SUPERVISION.md` |
| `ADR-023` | Architecture Decision Record: Edge Deployment & Supervision | `ADR-023-edge-deployment-and-process-supervision.md` |
