# OVIC EON — Model Adapter Architecture Specification

**Document ID:** `EON-ARCH-MOD-001`  
**Phase:** Phase 2 — System Architecture and Engineering Design  
**Sub-phase:** 2.7 — Design Model Adapter Architecture  
**Status:** Approved Engineering Architecture Specification  
**Version:** 1.0.0  
**Classification:** Technical Architecture Specification  
**Document Owner:** Principal Software Architect  
**Related Documents:**
- `docs/architecture/MODEL_ADAPTER_INTERFACE_SPECIFICATION.md` (`EON-SPEC-MOD-001`)
- `docs/architecture/MODEL_RUNTIME_COMPATIBILITY.md` (`EON-SPEC-MOD-002`)
- `docs/architecture/HARDWARE_CAPABILITY_ABSTRACTION.md` (`EON-SPEC-MOD-003`)
- `docs/architecture/MODEL_LIFECYCLE.md` (`EON-SPEC-MOD-004`)
- `docs/architecture/MODEL_PROVENANCE_AND_GOVERNANCE.md` (`EON-POL-MOD-001`)
- `docs/architecture/decisions/ADR-016-provider-neutral-model-adapter-architecture.md` (`EON-ADR-016`)

---

## 1. Executive Summary

This specification defines the provider-independent machine learning model and algorithm adapter architecture of OVIC EON (Layer 7 of the system architecture).

OVIC EON isolates all local machine learning runtimes (ONNX Runtime, `llama.cpp`, Piper neural TTS) and deterministic rule systems behind uniform adapter abstractions. Intelligence engines interact with models strictly via typed contract interfaces, shielding them from specific framework APIs, memory allocation quirks, or vendor SDKs.

---

## 2. Core Architecture Subsystems

```text
+===================================================================================+
|                     MODEL & ALGORITHM ADAPTER LAYER (L7)                          |
+===================================================================================+
|  +-----------------------------------------------------------------------------+  |
|  |                             Model Adapter Registry                          |  |
|  |    (Adapter catalog, model discovery, version tracking, hardware selection) |  |
|  +-----------------------------------------------------------------------------+  |
|         │                        │                        │                       |
|         ▼                        ▼                        ▼                       |
|  +---------------+      +------------------+      +------------------------+      |
|  | Hardware      |      | Model Metadata & |      | Model Health & Memory  |      |
|  | Detector      |      | Provenance Store |      | Supervisor             |      |
|  +---------------+      +------------------+      +------------------------+      |
|         │                        │                        │                       |
|  +-----------------------------------------------------------------------------+  |
|  |                     Provider-Neutral Inference Adapters                     |  |
|  |    - ONNX Runtime Adapter (Face Mesh, Silero VAD, SER, ST-GCN Pose)         |  |
|  |    - LlamaCpp Adapter (Local Qwen2.5-1.5B GGUF Dialogue Generation)         |  |
|  |    - Piper TTS Adapter (Local Neural Speech Vocoding)                       |  |
|  |    - Deterministic Rule Engine Adapter (Fast Safety & Fallback Templates)   |  |
|  +-----------------------------------------------------------------------------+  |
+===================================================================================+
```

---

## 3. Supported Model Types and Modalities

```text
+=======================================================================================+
| Domain Modality       | Target Algorithm / Model         | Framework / Format         |
+=======================================================================================+
| Facial Action Units   | MediaPipe Face Mesh + MLP Head   | ONNX INT8 / TFLite         |
| Voice Activity (VAD)  | Silero VAD v4                    | ONNX INT8                  |
| Speech Emotion (SER)  | DistilHuBERT-SER                 | ONNX INT8                  |
| Multimodal Fusion     | Gated Cross-Attention Head       | ONNX INT8                  |
| 3D Pose & Activity    | MediaPipe Pose + ST-GCN          | ONNX INT8                  |
| Gesture Tracking      | MediaPipe Hands + DTW Classifier | ONNX / Deterministic Rules |
| Dialogue Generation   | Qwen2.5-1.5B-Instruct            | GGUF Q4_K_M (llama.cpp)    |
| Speech Synthesis      | Piper VITS Vocoder               | ONNX Medium / Low Quality  |
| Fallback Deliberation | CPM Appraisal & Safety Templates | Deterministic Rule Engine  |
+=======================================================================================+
```
