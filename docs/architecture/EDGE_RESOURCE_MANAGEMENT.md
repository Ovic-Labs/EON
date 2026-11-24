# OVIC EON — Edge Resource Management Specification

**Document ID:** `EON-SPEC-EDGE-001`  
**Phase:** Phase 2 — System Architecture and Engineering Design (Sub-phase 2.14)  
**Status:** `DESIGNED — NOT IMPLEMENTED (Phase 2 Architecture Baseline)`  
**Target Audience:** Systems Performance Engineers, Edge Developers, Embedded Robotics Architects  
**Traceability:** `EON-ARCH-EDGE-001`, SRS-PERF-001, ADR-023, `ARCHITECTURE_RESOURCE_BUDGETS.md`  

---

## 1. Executive Summary and Resource Partitioning Mission

OVIC EON executes directly aboard autonomous robot computers alongside mission-critical navigation (Nav2), motion planning (MoveIt), SLAM, and hardware emergency-stop systems. To guarantee that affective intelligence processing **never starves physical robot safety controllers**, EON enforces strict deterministic resource partitioning at both the application and operating system levels.

---

## 2. Low-Resource Profile Subsystem Budget Breakdown (2GB Memory & 150% CPU Quota)

The baseline deployment target (Profile A / Low-Resource Edge) enforces a hard memory cap of **2048 MB (`MemoryMax`)** and a CPU quota of **150% (`CPUQuota`)** across 2 CPU cores. The table below specifies the detailed allocation breakdown across every subsystem:

| Subsystem Component | Steady-State RAM | Peak Burst RAM | Steady CPU | Peak CPU | Storage Footprint | Resource Isolation Strategy |
|---|---|---|---|---|---|---|
| **EON Core Daemon (`eond`)** | 64 MB | 96 MB | 5% | 15% | $\le 10\text{ MB}$ | Supervisor process, configuration, IPC lifecycle |
| **Core Event Bus (`EventBus`)** | 48 MB | 64 MB | 10% | 20% | N/A (RAM only) | Lock-free ring queues, priority routing |
| **ERS (Emotion Recognition)** | 192 MB | 256 MB | 25% | 35% | $\le 100\text{ MB}$ (weights) | INT8 face/voice feature extractors |
| **EMS (Emotional Memory)** | 96 MB | 144 MB | 5% | 15% | $\le 500\text{ MB}$ (SQLite WAL) | Episodic context, per-subject DEK |
| **ERE (Empathy Reasoning)** | 64 MB | 96 MB | 10% | 15% | $\le 50\text{ MB}$ | Cognitive appraisal state machine |
| **PSE (Personality Simulation)** | 48 MB | 64 MB | 5% | 10% | $\le 10\text{ MB}$ | Behavioral style clamps and profiles |
| **SIE (Social Interaction)** | 64 MB | 96 MB | 5% | 15% | $\le 20\text{ MB}$ | Interaction HFSM, turn-taking queues |
| **ERG (Response Generation)** | 96 MB | 144 MB | 10% | 20% | $\le 150\text{ MB}$ (TTS cache) | Multimodal motion proposal generator |
| **HBU (Human Behaviour)** | 128 MB | 192 MB | 15% | 25% | $\le 100\text{ MB}$ (trackers) | Tracking, engagement dynamics |
| **Neural Model Runtime (ONNX)** | 384 MB | 512 MB | 20% | 35% | $\le 600\text{ MB}$ (INT8 models) | Pluggable ONNX CPU execution pool |
| **ROS 2 Bridge (`eon_ros2_bridge`)**| 64 MB | 96 MB | 5% | 15% | $\le 20\text{ MB}$ | DDS discovery, lifecycle node coordination |
| **Volatile Sensor Taps (`/dev/shm`)**| 128 MB | 256 MB | 10% | 20% | N/A (RAM tmpfs) | Fixed circular ring buffer, zero disk I/O |
| **Diagnostic Logging & Metrics** | 24 MB | 32 MB | 2% | 5% | $\le 150\text{ MB}$ (rolling logs)| Redacted JSON logs, OTel metrics |
| **Working Memory & SQLite Cache** | 64 MB | 96 MB | 3% | 5% | Included in EMS | Bounded LRU page cache, vector index |
| **TOTAL EON WORKLOAD** | **1464 MB** | **1950 MB** | **110%** | **145%** | **$\le 1600\text{ MB}$** | **Enforced by cgroups v2 (`MemoryMax=2048M`)** |

> [!IMPORTANT]
> **Host OS and Robot Safety Isolation:** The Host Linux OS (kernel, systemd, device drivers: $\approx 800\text{ MB}$ RAM) and external robot navigation/safety processes (Nav2, MoveIt: $\ge 1200\text{ MB}$ RAM) execute in independent cgroups slices (`system.slice`). EON’s hard memory cap guarantees that a minimum of **2000 MB RAM remains strictly reserved** for host robot operations on an 4GB–8GB edge device.

---

## 3. Workload Profiles: Low-Resource, Standard, and Accelerated

EON formally defines three deployment profiles:

| Dimension | Profile A (Low-Resource Edge) | Profile B (Standard Edge) | Profile C (Accelerated Edge) |
|---|---|---|---|
| **Target Hardware** | 4-Core ARM64 / x86_64 (Jetson Orin Nano 8GB, Intel N100, Raspberry Pi 5 8GB) | 6–8 Core x86_64 / ARM (Intel Core Ultra 5/7, AMD Ryzen Embedded, Orin NX 16GB) | 12+ Core + GPU/NPU (Jetson AGX Orin 64GB, Intel Core Ultra 7 + Arc, RTX IPC) |
| **Total System RAM** | 4 GB – 8 GB | 16 GB | 32 GB – 64 GB |
| **EON RAM Steady / Peak** | **1464 MB / 1950 MB** | **2800 MB / 3800 MB** | **5500 MB / 7500 MB** |
| **EON `MemoryHigh` (Soft)** | **1800 MB** | **3600 MB** | **7200 MB** |
| **EON `MemoryMax` (Hard)** | **2048 MB (2.0 GB)** | **4096 MB (4.0 GB)** | **8192 MB (8.0 GB)** |
| **EON CPU Quota (`CPUQuota`)**| **150% (1.5 Cores)** | **300% (3.0 Cores)** | **600% (6.0 Cores)** |
| **Host Safety Headroom** | $\ge 2000\text{ MB}$ RAM, 2.5 CPU cores | $\ge 10000\text{ MB}$ RAM, 5.0 CPU cores | $\ge 24000\text{ MB}$ RAM, 6.0+ CPU cores |
| **Vision Ingress Rate** | 10 FPS (640x480 sRGB) | 15–20 FPS (1280x720 sRGB) | 30 FPS (1920x1080 sRGB / RGB-D) |
| **Audio Ingress Rate** | 16 kHz Mono (PCM 16-bit) | 16 kHz Stereo (PCM 16-bit) | 16 kHz 4-Channel Array |
| **Model Quantization** | INT8 strictly | Hybrid FP16 / INT8 | FP16 TensorRT / OpenVINO NPU |

---

## 4. Linux Cgroups v2 and Systemd Service Configuration

Resource boundaries are enforced natively by the Linux kernel via `systemd` unit configuration (`/etc/systemd/system/eon.service`):

```ini
[Unit]
Description=OVIC EON Emotional Intelligence Infrastructure Daemon
After=network.target local-fs.target
Wants=systemd-udev-settle.service

[Service]
Type=notify
ExecStart=/usr/bin/eond --config /etc/eon/eon.conf
Restart=on-failure
RestartSec=3s
TimeoutStopSec=10s

# cgroups v2 Memory Controls
MemoryAccounting=yes
MemoryHigh=1800M
MemoryMax=2048M
MemorySwapMax=0M

# cgroups v2 CPU Controls
CPUAccounting=yes
CPUQuota=150%
CPUWeight=100

# Process and Task Limits
TasksMax=128
LimitNOFILE=65536

# OOM Killer Protection for Bus vs Inference
OOMScoreAdjust=-200
TimeoutSec=15s

[Install]
WantedBy=multi-user.target
```

- **`MemorySwapMax=0M`:** Prohibits paging sensitive in-memory biometric observations or cryptographic keys to unencrypted swap partitions on disk.
- **`MemoryHigh=1800M`:** Soft threshold triggering dynamic degradation: downsampling vision to 5 FPS, pruning historical cache pages, and freeing intermediate tensors before reaching hard termination.
- **`MemoryMax=2048M`:** Hard kernel threshold. If exceeded, kernel kills rogue worker subprocesses without impacting host robot stability.
