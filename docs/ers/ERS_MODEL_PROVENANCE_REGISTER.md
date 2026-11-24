# ERS Model Provenance & Governance Register

## 1. Register Overview

This register provides an auditable accounting of all machine learning models, ONNX topologies, and experimental heuristics incorporated into the Emotion Recognition System (ERS).

Every entry tracks:
- Unique model identifier and version.
- Artifact filesystem location and SHA-256 cryptographic digest.
- Training provenance and dataset lineage.
- Software and data licensing constraints.
- Commercial suitability determination.
- Current validation status and operational restrictions.

---

## 2. Model Inventory

### 2.1 ERS Lightweight Facial Emotion ConvNet

| Attribute | Specification / Audit State |
|---|---|
| **Model ID** | `ers-facial-onnx-cpu-v1` |
| **Model Name** | ERS Lightweight Facial Emotion ConvNet |
| **Version** | `1.0.0` |
| **Modality** | Visual Facial Expression (`facial`) |
| **Framework** | ONNX Runtime (`CPUExecutionProvider`) |
| **Artifact Path** | `packages/ers/models/facial_emotion_model.onnx` |
| **SHA-256 Digest** | `0e8955c5187b2b9f69f9638e005b09abdbb1412951024e535fdefef48cc7d81b` |
| **Input Shape** | `[1, 1, 64, 64]` (Normalized grayscale face crop) |
| **Output Shape** | `[1, 7]` (Logits over 7 basic categories) |
| **Training Provenance** | `UNVERIFIED` (Synthetic parameter initialization; integration test graph) |
| **License** | UNVERIFIED (Synthetic graph topology) |
| **Commercial Use Allowed** | `False` (`RESTRICTED`) |
| **Model State** | `MODEL_LOADED_UNVERIFIED` |
| **Validation Status** | **UNVALIDATED** (Fails empirical Macro-F1 and dataset criteria) |
| **Runtime Policy** | Discrete emotion predictions suppressed; returns `insufficient_evidence` |

### 2.2 ERS Lightweight Acoustic Prosody MLP

| Attribute | Specification / Audit State |
|---|---|
| **Model ID** | `ers-speech-onnx-cpu-v1` |
| **Model Name** | ERS Lightweight Acoustic Prosody MLP |
| **Version** | `1.0.0` |
| **Modality** | Acoustic Speech Prosody (`speech`) |
| **Framework** | ONNX Runtime (`CPUExecutionProvider`) |
| **Artifact Path** | `packages/ers/models/speech_emotion_model.onnx` |
| **SHA-256 Digest** | `c5c8538e69d6f66e4724a7ca118b61c3c3e39686ba6adb53443bcb099fc0b0a2` |
| **Input Shape** | `[1, 12]` (12 acoustic prosody feature vector) |
| **Output Shape** | `[1, 7]` (Logits over 7 basic categories) |
| **Training Provenance** | `UNVERIFIED` (Synthetic parameter initialization; integration test graph) |
| **License** | UNVERIFIED (Synthetic graph topology) |
| **Commercial Use Allowed** | `False` (`RESTRICTED`) |
| **Model State** | `MODEL_LOADED_UNVERIFIED` |
| **Validation Status** | **UNVALIDATED** (Fails empirical Macro-F1 and dataset criteria) |
| **Runtime Policy** | Discrete emotion predictions suppressed; returns `insufficient_evidence` |

### 2.3 Experimental Regional Feature Adapter

| Attribute | Specification / Audit State |
|---|---|
| **Model ID** | `ers-facial-experimental-v1` |
| **Modality** | Visual Facial Morphology |
| **Implementation** | `eon_ers.facial.adapters.ExperimentalRegionalFeatureAdapter` |
| **Model State** | `MODEL_EXPERIMENTAL` |
| **Validation Status** | **UNVALIDATED** |
| **Runtime Policy** | Explicitly abstains; returns `INSUFFICIENT_EVIDENCE` |

---

## 3. Commercial Gating & Legal Compliance

1. **Commercial Deployment Prohibited:** Both baseline ONNX models are explicitly flagged with `commercial_use_allowed = False`. They are licensed exclusively for edge runtime integration testing, pipeline benchmarking, and qualification demonstration.
2. **Audit Verification:** All model manifests (`.json`) and validation records (`.validation.json`) reside under version control alongside the artifacts. If any artifact is modified, the SHA-256 mismatch immediately trips `ERSModelIntegrityError`, preventing execution.
3. **Clearance Roadmap:** Production commercial deployment requires replacing these initial baseline weights with weights trained on permissible commercial datasets (e.g. licensed corporate datasets or Apache-2.0 / CC-BY-4.0 affective corpora with full commercial indemnification).
