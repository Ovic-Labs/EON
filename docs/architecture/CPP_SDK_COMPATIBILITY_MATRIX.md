# OVIC EON — C++ SDK Compatibility Matrix and Benchmark Protocol

**Document ID:** `EON-SPEC-CPP-008`  
**Phase:** Phase 2 — System Architecture and Engineering Design (Sub-phase 2.11)  
**Status:** `DESIGNED — NOT IMPLEMENTED (Phase 2 Architecture Baseline)`  
**Target Audience:** QA Engineers, Systems Architects, Hardware Partners  
**Traceability:** `EON-ARCH-CPP-001`, `PYTHON_SDK_ARCHITECTURE.md`, ADR-020  

---

## 1. Platform and Compiler Compatibility Matrix

| Operating System | Architecture | Minimum Compiler | Middleware / Python | Status |
|---|---|---|---|---|
| Ubuntu 22.04 LTS | x86_64 | GCC 11.4 / Clang 14 | ROS 2 Humble, Python 3.10+ | DESIGNED |
| Ubuntu 24.04 LTS | x86_64 | GCC 13.2 / Clang 18 | ROS 2 Jazzy, Python 3.12+ | DESIGNED |
| Ubuntu 22.04 (Jetpack 5.1/6.0) | aarch64 (Jetson Orin) | GCC 11.4 | ROS 2 Humble | DESIGNED |
| Debian 12 (Bookworm) | x86_64 / aarch64 | GCC 12.2 | Standalone / Python 3.11 | DESIGNED |
| Windows 11 / Server 2022 | x86_64 | MSVC 2022 (v143) | Standalone / Python 3.10+ | DESIGNED |
| QNX Neutrino 7.1 | aarch64 / x86_64 | QCC 8.3 | Real-Time Embedded Profile | PROVISIONAL |

---

## 2. Future Hardware Benchmark Protocol

> [!IMPORTANT]
> All latency figures ($p_{50} \le 0.15\text{ ms}, p_{99} \le 0.50\text{ ms}$) are **provisional targets**. They must be validated using the formal hardware benchmark protocol specified below prior to production release.

### Benchmark Setup and Methodology
1. **Hardware Testbeds:**
   - **Tier 1 (Workstation):** AMD Ryzen 9 7950X / Intel Core i9-13900K, 64GB DDR5, Linux 6.5 lowlatency.
   - **Tier 2 (Edge Robotics Compute):** NVIDIA Jetson AGX Orin 64GB (MAX-N mode), Jetson Orin Nano 8GB (15W mode).
   - **Tier 3 (Embedded CPU):** Intel Core Ultra 7 155H, 32GB LPDDR5x.
2. **Execution Parameters:**
   - Publication rates: 10 Hz, 50 Hz, 100 Hz, 500 Hz, 1000 Hz.
   - Payload sizes: Small (64 bytes metadata), Medium (4 KB structured event), Dense (1 MB zero-copy SHM image).
   - Concurrency: 1 publisher, 4 subscribers; competing synthetic CPU background load (stress-ng).
3. **Metrics Recorded:**
   - $p_{50}, p_{95}, p_{99}, p_{99.9}$ roundtrip IPC dispatch latency.
   - CPU utilization percentage per thread.
   - Peak RSS and memory fragmentation index over 24-hour endurance test.
