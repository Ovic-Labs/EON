# ADR-005: Model and Algorithm Adapter Boundaries

**Document ID:** `EON-ADR-005`  
**Status:** Approved  
**Date:** 2026-11-23  
**Deciders:** Principal Software Architect, Founder, Engineering Leads  
**Related Requirements:** `EON-NFR-030`, `EON-SRS-085`, `EON-SPEC-ENG-001`

---

## 1. Context
OVIC EON incorporates diverse machine learning models: MediaPipe Face Mesh, Silero VAD, DistilHuBERT-SER, ST-GCN pose classification, Qwen2.5-1.5B quantized SLM, and Piper neural TTS. In typical research prototypes, model inference code is intermingled directly with application business logic, locking the system to specific inference runtimes (e.g. PyTorch or TensorFlow) and preventing migration to edge accelerators.

## 2. Problem
How should machine learning model execution and deterministic algorithms be encapsulated to permit model upgrades, backend switching, and hardware-specific optimization without modifying intelligence engine logic?

## 3. Decision
Establish **Layer 7 (Model and Algorithm Adapter Layer)** as an independent abstraction layer:
1. **Uniform Adapter Interfaces:** Define abstract SPIs (`InferenceAdapterInterface`, `LlmAdapterInterface`, `TtsAdapterInterface`).
2. **Framework Isolation:** All external runtime bindings (ONNX Runtime, `llama.cpp`, Piper C++) are strictly confined to L7. Engines consume model outputs via typed contracts.
3. **Hardware Execution Provider Detection:** L7 automatically detects available accelerators (CPU AVX2/NEON, OpenVINO, Rockchip RKNN, NVIDIA CUDA/TensorRT) and configures runtimes accordingly.
4. **Deterministic Algorithm Fallbacks:** Every adapter includes a deterministic, zero-ML fallback path (e.g., regex/template generation) for instant recovery under model failure or resource exhaustion.

## 4. Alternatives Considered
1. **Direct In-Engine Model Invocations:** Embedding `onnxruntime.InferenceSession` inside ERS and `llama_cpp.Llama` inside ERG. Rejected because it couples cognitive engines to specific libraries and prevents unit testing on systems without model weights.
2. **External Model Inference Microservice (Triton / TorchServe):** Rejected due to high edge resource footprint (requiring >2 GB RAM just for server overhead) and IPC network latency.

## 5. Consequences
- **Positive:** Models can be replaced or re-quantized (e.g. INT8 vs FP16) without changing a single line of engine code; engines can be unit-tested using lightweight mock adapters.
- **Negative:** Requires mapping tensor outputs to EON schema models at the adapter boundary.

## 6. Risks and Mitigations
- **Risk:** Tensor copy overhead between adapters and engines.
- **Mitigation:** Adapters return NumPy structured views or direct Python primitives to avoid redundant memory copies.
