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
2. **Strict Hardware Tiering:** Predefined deployment profiles for low-resource (embedded SBC), standard (robot onboard compute), and accelerated (workstation / Jetson AGX) tiers.
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

## 3. Standard Deployment Profiles

| Profile | Target Compute | Memory | Acceleration | Workload Allocation |
|---|---|---|---|---|
| **Low-Resource** | 4-core ARM64 / x86 (e.g. Jetson Orin Nano, Intel N100) | 4–8 GB | CPU-only / INT8 Quantized | 5–10 FPS Vision, lightweight audio prosody, bounded memory (2 GB) |
| **Standard** | 8-core CPU (e.g. Intel Core Ultra 7, AMD Ryzen 7) | 16 GB | CPU + NPU / iGPU (OpenVINO) | 15 FPS Vision, multi-channel acoustic analysis, full context |
| **Accelerated** | 12+ core CPU + GPU (e.g. Jetson AGX Orin 64GB) | 32–64 GB | CUDA / TensorRT | 30 FPS Vision, dense 3D gaze estimation, real-time multimodal fusion |

---

## 4. Traceability Matrix

| Requirement ID | Architectural Requirement | Specification Document |
|---|---|---|
| `PRD-REQ-007` | Embedded edge compatibility without mandatory cloud or GPU | `EDGE_RESOURCE_MANAGEMENT.md` |
| `SRS-ARCH-013` | Deterministic edge process supervision and update rollback | `EDGE_PROCESS_SUPERVISION.md` |
| `ADR-023` | Architecture Decision Record: Edge Deployment & Supervision | `ADR-023-edge-deployment-and-process-supervision.md` |
