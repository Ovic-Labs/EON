# OVIC EON — Architecture Resource Budgets Specification

**Document ID:** `EON-SPEC-BUD-001`  
**Phase:** Phase 2 — System Architecture and Engineering Design (Sub-phase 2.20)  
**Status:** `DESIGNED — NOT IMPLEMENTED (Phase 2 Architecture Baseline)`  
**Target Audience:** Embedded Systems Engineers, Hardware Architects, Performance Engineers  
**Traceability:** `EON-ARCH-EDGE-001`, `EDGE_RESOURCE_MANAGEMENT.md`, ADR-023, SRS-PERF-001  

---

## 1. Target Resource Budgets by Deployment Profile

This specification establishes the authoritative resource allocation quotas across the three official EON edge deployment tiers:

| Resource Dimension | Profile A: Low-Resource (Embedded SBC) | Profile B: Standard (Onboard Compute) | Profile C: Accelerated (Workstation / AGX) |
|---|---|---|---|
| **Target Hardware** | Jetson Orin Nano (8GB) / Intel N100 / RPi 5 | Intel Core Ultra 5/7 / AMD Ryzen 7 / Orin NX | Jetson AGX Orin (64GB) / RTX Industrial IPC |
| **Total System RAM** | 4 GB – 8 GB | 16 GB | 32 GB – 64 GB |
| **EON Steady-State RAM** | **1464 MB** | **2800 MB** | **5500 MB** |
| **EON Peak Burst RAM** | **1950 MB** | **3800 MB** | **7500 MB** |
| **RAM Soft Limit (`memory.high`)** | **1800 MB** | **3600 MB** | **7200 MB** |
| **RAM Hard Cap (`memory.max`)** | **2048 MB (2.0 GB)** | **4096 MB (4.0 GB)** | **8192 MB (8.0 GB)** |
| **EON CPU Steady / Peak** | **110% / 145%** | **220% / 285%** | **450% / 580%** |
| **CPU Allocation Cap (`CPUQuota`)** | **150% (1.5 Cores)** | **300% (3.0 Cores)** | **600% (6.0 Cores)** |
| **Host Robot Headroom (Reserved)** | **$\ge 2000\text{ MB}$ RAM, 2.5 CPU cores** | **$\ge 10000\text{ MB}$ RAM, 5.0 CPU cores** | **$\ge 24000\text{ MB}$ RAM, 6.0+ CPU cores** |
| **Shared Memory (`/dev/shm`)** | 256 MB (Fixed ring buffer) | 512 MB (Fixed ring buffer) | 1024 MB (Fixed ring buffer) |
| **Non-Volatile Storage (Disk)** | $\le 2048\text{ MB}$ (SQLite + Models) | $\le 8192\text{ MB}$ | $\le 16384\text{ MB}$ |
| **Nominal Vision Sampling Rate** | 10 FPS (sRGB 640x480) | 15–20 FPS (sRGB 1280x720) | 30 FPS (sRGB 1920x1080 / RGB-D) |
| **Audio Sampling Rate** | 16 kHz Mono (PCM 16-bit) | 16 kHz Stereo (PCM 16-bit) | 16 kHz 4-Channel Array |
| **Event Bus Ingress Queue Depth** | 128 Envelopes | 512 Envelopes | 2048 Envelopes |

---

## 2. Low-Resource Profile Subsystem Memory and CPU Breakdown

The table below delineates the strict internal budget allocation for the 2048 MB RAM cap and 150% CPU quota in Profile A:

| Subsystem Component | Allocated RAM | Allocated CPU | Storage Ceiling | Invariant Enforcement |
|---|---|---|---|---|
| **EON Core Daemon (`eond`)** | 64 MB | 5% (15% peak) | 10 MB | Process supervisor, cgroups monitor |
| **Core Event Bus (`EventBus`)** | 48 MB | 10% (20% peak) | RAM-only | Bounded queue, `DROP_OLDEST` on saturation |
| **ERS (Emotion Recognition)** | 192 MB | 25% (35% peak) | 100 MB | INT8 model weights, landmark buffers |
| **EMS (Emotional Memory)** | 96 MB | 5% (15% peak) | 500 MB | SQLite WAL, per-subject DEK encryption |
| **ERE (Empathy Reasoning)** | 64 MB | 10% (15% peak) | 50 MB | Cognitive appraisal state machine |
| **PSE (Personality Simulation)** | 48 MB | 5% (10% peak) | 10 MB | Style profile clamps and modifiers |
| **SIE (Social Interaction)** | 64 MB | 5% (15% peak) | 20 MB | Interaction HFSM, turn-taking queues |
| **ERG (Response Generation)** | 96 MB | 10% (20% peak) | 150 MB | Multimodal motion proposal generator |
| **HBU (Human Behaviour)** | 128 MB | 15% (25% peak) | 100 MB | Optical tracking, engagement models |
| **Neural Model Runtime (ONNX)** | 384 MB | 20% (35% peak) | 600 MB | ONNX Runtime CPU thread affinity |
| **ROS 2 Bridge (`eon_ros2_bridge`)**| 64 MB | 5% (15% peak) | 20 MB | DDS discovery, lifecycle node bridge |
| **Volatile Sensor Taps (`/dev/shm`)**| 128 MB | 10% (20% peak) | RAM-only | Fixed circular ring buffer, zero disk I/O |
| **Diagnostic Logging & Metrics** | 24 MB | 2% (5% peak) | 150 MB | Redacted JSON logs, OTel metrics |
| **Working Memory & SQLite Cache** | 64 MB | 3% (5% peak) | Included in EMS | Bounded LRU page cache, vector index |
| **TOTAL SUB-BUDGET** | **1464 MB** | **110%** | **$\le 1600\text{ MB}$** | **Enforced by cgroups v2 (`MemoryMax=2048M`)** |

---

## 3. End-to-End Latency Budgets (Perception to Motion Proposal)

To support real-time human-robot interaction without conversational lag:

| Processing Stage | Subsystem | Budget (Profile A) | Budget (Profile B) | Budget (Profile C) |
|---|---|---|---|---|
| Ingress & Preprocessing | V4L2 / ALSA Ingress | $\le 10\text{ ms}$ | $\le 5\text{ ms}$ | $\le 2\text{ ms}$ |
| Feature Extraction & Perception | ERS / HBU (ONNX CPU) | $\le 45\text{ ms}$ | $\le 25\text{ ms}$ | $\le 12\text{ ms}$ |
| Event Bus Dispatch | Core IPC Transport | $\le 1\text{ ms}$ | $\le 0.5\text{ ms}$ | $\le 0.2\text{ ms}$ |
| Working Memory Lookup | EMS Shared Context | $\le 8\text{ ms}$ | $\le 4\text{ ms}$ | $\le 2\text{ ms}$ |
| Empathy & Appraisal Reasoning | ERE Cognitive Engine | $\le 15\text{ ms}$ | $\le 10\text{ ms}$ | $\le 5\text{ ms}$ |
| Social Interaction FSM | SIE Turn-Taking | $\le 10\text{ ms}$ | $\le 5\text{ ms}$ | $\le 2\text{ ms}$ |
| Response & Motion Proposal | ERG Proposal Formatter | $\le 20\text{ ms}$ | $\le 12\text{ ms}$ | $\le 5\text{ ms}$ |
| ROS 2 Bridge Publishing | `eon_ros2_bridge` DDS | $\le 5\text{ ms}$ | $\le 2\text{ ms}$ | $\le 1\text{ ms}$ |
| **TOTAL PERCEPTION-TO-PROPOSAL**| **End-to-End Pipeline** | **$\le 114\text{ ms}$** | **$\le 63.5\text{ ms}$** | **$\le 29.2\text{ ms}$** |

---

## 4. Reproducible Benchmark Protocol for Phase 3 Qualification

Prior to claiming runtime performance qualification in Phase 3, the following measurement methodology must be executed on documented reference hardware:
1. **Measurement Harness:** Continuous logging via Linux `cgroups v2` interface (`/sys/fs/cgroup/system.slice/eon.service/memory.current` and `cpu.stat`), sampled at 10 Hz.
2. **Standard Benchmark Scenarios:**
   - **Scenario 1 (Idle Standby):** No humans in perceptual field for 30 minutes; verify RAM $\le 800\text{ MB}$, CPU $\le 15\%$.
   - **Scenario 2 (Continuous Dialogue):** Continuous multimodal turn-taking with a single user for 60 minutes; verify RAM $\le 1600\text{ MB}$, CPU $\le 120\%$.
   - **Scenario 3 (Crowded Public Scene):** 3+ simultaneous human faces and background acoustic chatter for 30 minutes; verify RAM $\le 1850\text{ MB}$, CPU $\le 145\%$.
   - **Scenario 4 (Stress Burst & Deletion):** Rapid user departure and immediate Right to be Forgotten purge request; verify WAL truncation and zero OOM events.
3. **Pass Criteria:** Zero cgroups OOM kill events (`memory.events:oom_kill == 0`), zero frame buffer drop in `/dev/shm`, and 95th-percentile perception-to-proposal latency under target budget.
