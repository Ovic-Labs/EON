# ADR-016: Provider-Neutral Model Adapter Architecture and CPU Fallback

**Document ID:** `EON-ADR-016`  
**Status:** Approved  
**Date:** 2026-11-23  
**Deciders:** Principal Software Architect, Founder, Engineering Leads  
**Related Requirements:** `EON-NFR-030`, `EON-NFR-040`, `EON-SRS-085`, `EON-ARCH-MOD-001`

---

## 1. Context
Modern robotics AI integrates disparate model architectures: computer vision models, acoustic neural networks, Small Language Models, and neural vocoders. Hardcoding specific inference runtimes (e.g. PyTorch, llama.cpp, or ONNX Runtime) directly into cognitive engines locks the codebase to vendor SDKs, bloats binary dependencies, and prevents optimization on diverse edge silicon.

## 2. Problem
How should machine learning model execution be structured to ensure framework independence, local CPU-first baseline execution, opportunistic accelerator utilization, and zero external cloud AI dependencies?

## 3. Decision
Adopt a **Provider-Neutral Model Adapter Substrate (Layer 7)**:
1. **Abstract Inference Interfaces:** Engines invoke models strictly through `InferenceAdapterInterface`. Direct framework calls are strictly forbidden in L4.
2. **CPU-First Baseline (`CONST-PERF-001`):** Quantized INT8 ONNX and GGUF CPU execution serve as the universal baseline. Hardware accelerators (Rockchip RKNN, NVIDIA TensorRT) are used opportunistically when detected, but never mandated.
3. **Deterministic Zero-ML Fallbacks:** Every adapter integrates deterministic rule fallbacks that execute in $<5\text{ms}$ if an ML model crashes, runs out of memory, or exceeds its latency deadline.
4. **Zero Cloud API Mandatory Dependencies:** All core intelligence models execute locally on edge silicon. External cloud AI APIs (e.g. OpenAI, Anthropic, Gemini) are strictly prohibited from core execution.

## 4. Alternatives Considered
1. **Direct PyTorch Tensor Invocations in Engines:** Rejected because PyTorch adds >1.8 GB disk footprint, >800 MB runtime overhead, and lacks real-time CPU optimization on embedded ARM boards.
2. **Mandatory Cloud Offload for Large Dialogue Models:** Rejected due to unpredictable network latency (>1000 ms) and privacy violations.

## 5. Consequences
- **Positive:** Complete framework portability; model weights can be upgraded without changing engine code; deterministic fallback ensures zero conversational stalling.
- **Negative:** Requires writing custom adapter wrappers for new model formats.

## 6. Risks and Mitigations
- **Risk:** Quantization accuracy degradation on INT8 edge models.
- **Mitigation:** Rigorous calibration using validation datasets; fallback to deterministic logic when model confidence is low.
