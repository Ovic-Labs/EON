# OVIC EON — Architecture Resource Budgets Specification

**Document ID:** `EON-SPEC-BUD-001`  
**Phase:** Phase 2 — System Architecture and Engineering Design (Sub-phase 2.20)  
**Status:** `DESIGNED — NOT IMPLEMENTED (Phase 2 Architecture Baseline)`  
**Target Audience:** Embedded Systems Engineers, Hardware Architects  
**Traceability:** `EON-ARCH-EDGE-001`, `EDGE_RESOURCE_MANAGEMENT.md`, ADR-023  

---

## 1. Target Resource Budgets by Deployment Profile

This specification establishes the maximum resource allocation caps across the three official EON edge deployment tiers:

| Resource Dimension | Low-Resource Tier (Embedded SBC) | Standard Tier (Onboard Compute) | Accelerated Tier (Workstation / AGX) |
|---|---|---|---|
| **Target Hardware** | Jetson Orin Nano (8GB) / Intel N100 | Intel Core Ultra 7 / AMD Ryzen 7 | Jetson AGX Orin (64GB) / RTX IPC |
| **CPU Allocation Cap** | 1.5 Cores (150% in systemd) | 3.0 Cores (300% in systemd) | 6.0 Cores (600% in systemd) |
| **System RAM Budget (`memory.max`)** | 2048 MB (2.0 GB) | 4096 MB (4.0 GB) | 8192 MB (8.0 GB) |
| **RAM Soft Limit (`memory.high`)** | 1800 MB | 3600 MB | 7200 MB |
| **Shared Memory (`/dev/shm`)** | 256 MB (Fixed ring buffer) | 512 MB (Fixed ring buffer) | 1024 MB (Fixed ring buffer) |
| **Non-Volatile Storage (Disk)** | $\le 2048\text{ MB}$ (SQLite + Models) | $\le 8192\text{ MB}$ | $\le 16384\text{ MB}$ |
| **Nominal Vision Sampling Rate** | 10 FPS (sRGB 640x480) | 15 FPS (sRGB 1280x720) | 30 FPS (sRGB 1920x1080) |
| **Audio Sampling Rate** | 16 kHz Mono (PCM 16-bit) | 16 kHz Stereo (PCM 16-bit) | 16 kHz 4-Channel Array |
| **Event Bus Ingress Queue Depth** | 128 Envelopes | 512 Envelopes | 2048 Envelopes |

---

## 2. Invariant Boundary Enforcement

- If system memory reaches `memory.high`, EON Core automatically executes memory reclamation: trimming model intermediate activation tensors, discarding historical affect dynamics caches, and reducing perception sampling rates.
- EON guarantees that its total background memory usage will never breach `memory.max`, protecting adjacent robot navigation, localization, and motor controller processes from edge OOM termination.
