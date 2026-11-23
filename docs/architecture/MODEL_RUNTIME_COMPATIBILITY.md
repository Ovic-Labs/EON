# OVIC EON — Model Runtime Compatibility Specification

**Document ID:** `EON-SPEC-MOD-002`  
**Phase:** Phase 2 — System Architecture and Engineering Design  
**Sub-phase:** 2.7 — Design Model Adapter Architecture  
**Status:** Approved Engineering Architecture Specification  
**Version:** 1.0.0  
**Classification:** Technical Architecture Specification  
**Document Owner:** Principal Software Architect  
**Related Documents:**
- `docs/architecture/MODEL_ADAPTER_ARCHITECTURE.md` (`EON-ARCH-MOD-001`)
- `docs/architecture/HARDWARE_CAPABILITY_ABSTRACTION.md` (`EON-SPEC-MOD-003`)

---

## 1. Executive Summary

This document establishes the verified and target runtime compatibility profiles across operating systems, CPU architectures, and optional hardware accelerators.

---

## 2. Runtime Compatibility Matrix

```text
+=======================================================================================+
| Runtime Provider      | Target Format  | Primary Hardware | Fallback Provider | Status|
+=======================================================================================+
| ONNX Runtime CPU      | `.onnx` (INT8) | ARM64 NEON/AVX2  | None (Baseline)   | [REP] |
| ONNX Runtime OpenVINO | `.onnx` (FP16) | Intel Core Ultra | CPU Baseline      | [EST] |
| Rockchip RKNN Runtime | `.rknn` (INT8) | RK3588 NPU       | CPU Baseline      | [EST] |
| NVIDIA TensorRT / CUDA| `.engine`/ONNX | Jetson Orin Nano | CPU Baseline      | [EST] |
| llama.cpp CPU Runner  | `.gguf` (Q4)   | 4x Cortex-A76    | Safety Templates  | [REP] |
| Piper TTS C++ Engine  | `.onnx` (VITS) | ARM64 CPU        | Audio Tone Chime  | [REP] |
+=======================================================================================+
```

> **Testing Policy Invariant:** Compatibility is marked `[REP]` (Reproduced) only when validated on reference hardware. Accelerators without physical bench results remain classified as `[EST]` (Estimated).
