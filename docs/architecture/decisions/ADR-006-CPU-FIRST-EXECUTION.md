# ADR-006: CPU-First and Edge-First Execution Invariant

**Document ID:** `EON-ADR-006`  
**Status:** Approved  
**Date:** 2026-11-23  
**Deciders:** Principal Software Architect, Founder, Engineering Leads  
**Related Requirements:** `EON-NFR-040`, `EON-PERF-001` through `EON-PERF-020`, `EON-SRS-090`

---

## 1. Context
Commercial service and humanoid robots operate under strict electrical power, thermal, and cost budgets. High-end discrete GPUs (e.g. NVIDIA RTX) consume 75–300 W of power, generate excessive heat, and increase bill-of-materials costs by thousands of dollars. The vast majority of deployed robots rely on embedded host CPUs (ARM64 Cortex-A76/A55, Intel Core Ultra, AMD Ryzen Embedded).

## 2. Problem
Should OVIC EON mandate GPU or NPU hardware acceleration for emotional intelligence, or must it execute entirely on edge CPUs?

## 3. Decision
Enforce a non-negotiable **CPU-First Execution Invariant (`CONST-PERF-001`)**:
1. **Baseline Operation on 4-Core Edge CPU:** The complete EON pipeline (vision, audio, emotion recognition, turn-taking, dialogue generation, speech synthesis) must execute in real time on a 4-core ARM64 Cortex-A76 @ 2.4 GHz processor without mandatory GPU or NPU.
2. **Accelerators as Opportunistic Optimizers:** NPUs (Rockchip RKNN) and GPUs (NVIDIA Jetson) are supported as optional execution providers in L7 to reduce CPU load and power consumption, but are never required for basic functionality.
3. **Quantized Models & Lightweight Architectures:** Standardize on quantized models (INT8 ONNX for vision/audio, W4A16 Q4_K_M GGUF for SLM dialogue, low/medium ONNX for Piper TTS).

## 4. Alternatives Considered
1. **Mandatory GPU Acceleration (CUDA Only):** Would restrict EON exclusively to expensive NVIDIA Jetson or x86 GPU boards, completely locking out the mass-market ARM64 robotics ecosystem (Raspberry Pi 5, Orange Pi 5 RK3588).
2. **Cloud AI Processing:** Offloading inference to cloud GPUs. Rejected because it introduces network latency jitter (>1000 ms), causes robot failures in elevators or basements, and violates privacy regulations.

## 5. Consequences
- **Positive:** Broad hardware portability; lower hardware cost for robot OEMs; operation within standard robot battery budgets (<35 W).
- **Negative:** Requires rigorous profiling and optimization; model sizes constrained to Small Language Models ($\le 1.5\text{B}$ parameters).

## 6. Risks and Mitigations
- **Risk:** CPU thermal throttling during continuous multi-modal processing.
- **Mitigation:** Multi-process worker pools with CPU core pinning and priority-based frame throttling under high thermal load.
