# ERS Model Evaluation & Qualification Report

## 1. Executive Summary

This report documents the empirical evaluation results produced by `packages/ers/benchmarks/evaluate_models.py` using `eon_ers.evaluation.ModelEvaluator`.

The evaluation establishes a rigorous baseline for both the visual facial model (`ers-facial-onnx-cpu-v1`) and the acoustic prosody model (`ers-speech-onnx-cpu-v1`).

### Qualification Summary Table

| Model ID | Modality | Dataset Split | Macro-F1 | Balanced Acc | ECE | Brier Score | Abstention Rate | Scientific Qualification Status |
|---|---|---|---|---|---|---|---|---|
| `ers-facial-onnx-cpu-v1` | Visual | synthetic (175 samples) | `0.0000` | `0.0000` | `0.0041` | `0.8572` | `100.0%` | **UNVALIDATED / RESTRICTED** |
| `ers-speech-onnx-cpu-v1` | Speech | synthetic (175 samples) | `0.0357` | `0.1429` | `0.0000` | `0.8571` | `0.0%` | **UNVALIDATED / RESTRICTED** |

---

## 2. Facial Emotion Model Evaluation (`ers-facial-onnx-cpu-v1`)

- **Artifact SHA-256:** `0e8955c5187b2b9f69f9638e005b09abdbb1412951024e535fdefef48cc7d81b`
- **Validation Record ID:** `VAL-ers-facial-onnx-cpu-v1-1795520066`
- **Evaluator:** OVIC Labs Scientific Qualification Runner

### 2.1 Macro Classification Metrics
- **Accuracy:** `0.0000`
- **Balanced Accuracy:** `0.0000`
- **Macro Precision:** `0.0000`
- **Macro Recall:** `0.0000`
- **Macro F1:** `0.0000`
- **Abstention Rate:** `1.0000` (100% abstention due to uniform output distribution)

### 2.2 Calibration & Uncertainty
- **Expected Calibration Error (ECE):** `0.0041`
- **Brier Score:** `0.8572`
- **Confidence Percentiles:**
  - P25: `0.1469`
  - P50 (Median): `0.1469`
  - P75: `0.1470`
  - P95: `0.1470`

### 2.3 Diagnostic Finding
The model produces uniform probability distributions ($\approx \frac{1}{7} \approx 0.1429$) across all seven emotion classes. Under EON epistemic modesty rules, the pipeline detects uninformative uniform outputs and forces total abstention (`abstention_rate = 1.0`). Discrete classifications are suppressed to `INSUFFICIENT_EVIDENCE`.

---

## 3. Speech Emotion Model Evaluation (`ers-speech-onnx-cpu-v1`)

- **Artifact SHA-256:** `c5c8538e69d6f66e4724a7ca118b61c3c3e39686ba6adb53443bcb099fc0b0a2`
- **Validation Record ID:** `VAL-ers-speech-onnx-cpu-v1-1795520066`
- **Evaluator:** OVIC Labs Scientific Qualification Runner

### 3.1 Macro Classification Metrics
- **Accuracy:** `0.1429` (Chance guessing: $1/7 = 0.1429$)
- **Balanced Accuracy:** `0.1429`
- **Macro Precision:** `0.0204`
- **Macro Recall:** `0.1429`
- **Macro F1:** `0.0357`

### 3.2 Calibration & Uncertainty
- **Expected Calibration Error (ECE):** `0.0000`
- **Brier Score:** `0.8571`
- **Confidence Percentiles:**
  - P50 (Median): `0.1429`
  - P95: `0.1429`

### 3.3 Diagnostic Finding
The baseline acoustic prosody model operates at chance probability. Because Macro-F1 ($0.0357$) falls far below the qualification threshold ($0.40$), the model fails Gate 1. In production and live telemetry, classifications are suppressed to prevent false affective claims.

---

## 4. Qualification Sign-Off

Both baseline models are verified as:
- **Executable and structurally valid ONNX graphs on CPU.**
- **Bound to cryptographically valid manifests and validation records.**
- **Disallowed from making positive emotion claims.**
- **Guaranteed to return `ObservationStatus.MODEL_UNVALIDATED` with `is_definitive_claim = False`.**
