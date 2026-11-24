# OVIC EON — Edge Model Deployment Specification

**Document ID:** `EON-SPEC-EDGE-004`  
**Phase:** Phase 2 — System Architecture and Engineering Design (Sub-phase 2.14)  
**Status:** `DESIGNED — NOT IMPLEMENTED (Phase 2 Architecture Baseline)`  
**Target Audience:** Machine Learning Engineers, Embedded AI Specialists  
**Traceability:** `EON-ARCH-EDGE-001`, `EON-ARCH-ADP-001`, ADR-023, ADR-015  

---

## 1. Edge Model Runtime Architecture

In compliance with EON Principle 2.1 (CPU-first) and Principle 2.2 (no mandatory cloud AI APIs):
- **ONNX Runtime (Primary):** Cross-platform execution engine supporting CPU (x86 AVX2/AVX-512, ARM Neon) and optional hardware accelerators.
- **Execution Providers (Modular Acceleration):**
  - `CPUExecutionProvider` (Default fallback baseline).
  - `OpenVINOExecutionProvider` (Intel Core Ultra CPUs, integrated GPUs, and NPUs).
  - `TensorRTExecutionProvider` (NVIDIA Jetson / discrete GPUs).
  - `QNNExecutionProvider` (Qualcomm Snapdragon / RB5 NPUs).

---

## 2. Model Quantization and Footprint Targets

| Engine Component | Model Architecture | Baseline Precision | Edge Optimized Precision | RAM Footprint Target |
|---|---|---|---|---|
| **ERS Face Analysis** | MobileNetV3 / ResNet-18 Backbone | FP32 | INT8 Quantized | $\le 45\text{ MB}$ |
| **ERS Acoustic Prosody** | Conformer-Lite / CNN14 | FP32 | INT8 Quantized | $\le 30\text{ MB}$ |
| **HBU Pose & Gesture** | MoveNet / MediaPipe Pose | FP32 | FP16 / INT8 | $\le 50\text{ MB}$ |
| **EMS Affect Dynamics** | Lightweight Recurrent State (GRU) | FP32 | FP32 (Scalar Math) | $\le 5\text{ MB}$ |
| **ERG Rule & Strategy** | Deterministic Decision Graph | N/A | In-Memory Graph Table | $\le 10\text{ MB}$ |

Total Model Weights Footprint: $\le 140\text{ MB}$ on edge storage, easily fitting into low-power embedded flash.
