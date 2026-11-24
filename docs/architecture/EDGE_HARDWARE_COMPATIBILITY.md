# OVIC EON — Edge Hardware Compatibility Specification

**Document ID:** `EON-SPEC-EDGE-008`  
**Phase:** Phase 2 — System Architecture and Engineering Design (Sub-phase 2.14)  
**Status:** `DESIGNED — NOT IMPLEMENTED (Phase 2 Architecture Baseline)`  
**Target Audience:** Hardware Engineers, Systems Integrators  
**Traceability:** `EON-ARCH-EDGE-001`, ADR-023  

---

## 1. Validated Hardware Platform Profiles

| Platform Family | Example SoC / Board | Architecture | Supported Profile | Acceleration Backend |
|---|---|---|---|---|
| **NVIDIA Jetson** | AGX Orin 64GB / Orin NX 16GB | ARM Cortex-A78AE | Accelerated / Standard | TensorRT / CUDA / DLA |
| **NVIDIA Jetson** | Orin Nano 8GB | ARM Cortex-A78AE | Low-Resource | INT8 TensorRT / CPU |
| **Intel Core Ultra** | Core Ultra 7 155H / 165H | x86_64 (Meteor Lake) | Standard / Accelerated | OpenVINO (CPU + NPU + Arc iGPU) |
| **AMD Ryzen Embedded** | Ryzen Embedded V3000 / 7000 | x86_64 (Zen 4) | Standard | CPU AVX-512 / ROCm |
| **Raspberry Pi** | Raspberry Pi 5 (8GB) | ARM Cortex-A76 | Low-Resource | ARM Neon CPU / Hailo-8 M.2 |
| **Qualcomm Robotics** | Dragonwing RB5 / RB6 | Kryo 585 / ARM64 | Standard | Qualcomm QNN / Hexagon NPU |

---

## 2. Hardware Bring-Up and Qualification Checklist

Before deploying EON to a novel edge board:
- [ ] Verify Linux kernel $\ge 5.15$ with `cgroups v2` and `tmpfs` enabled.
- [ ] Verify `/dev/shm` mounted with POSIX shared memory support.
- [ ] Test CPU SIMD extensions (`lscpu` shows AVX2 on x86 or Neon on ARM).
- [ ] Measure baseline IPC latency with `eon-benchmark-ipc`.
- [ ] Ensure power delivery sustains peak inference bursts without undervoltage CPU throttling.
