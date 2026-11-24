# Model Evaluation & Qualification Report: ers-speech-onnx-cpu-v1
**Record ID:** `VAL-ers-speech-onnx-cpu-v1-1795520066`  
**Validation Status:** **UNVALIDATED / RESTRICTED**  
**Evaluator:** OVIC Labs Scientific Qualification Runner  
**Timestamp:** 2026-11-24T11:34:26Z  
**Artifact SHA-256:** `c5c8538e69d6f66e4724a7ca118b61c3c3e39686ba6adb53443bcb099fc0b0a2`  

## 1. Governance & Provenance
- **Training Dataset:** UNVERIFIED (Synthetic parameter initialization; no empirical training dataset)
- **Evaluation Dataset:** synthetic_speech_fixture_suite (`test` split)
- **Dataset License:** OVIC Internal Testing License
- **Commercial Use Allowed:** `False`
- **Restrictions:**
  - Research and pipeline testing only. Commercial deployment prohibited.

## 2. Macro Classification Metrics
| Metric | Score |
|---|:---:|
| **Accuracy** | `0.1429` |
| **Balanced Accuracy** | `0.1429` |
| **Macro Precision** | `0.0204` |
| **Macro Recall** | `0.1429` |
| **Macro F1** | `0.0357` |
| **Total Samples** | `175.0` |
| **Abstention Rate** | `0.0` |

## 3. Calibration Metrics
- **Expected Calibration Error (ECE):** `0.8571`
- **Brier Score:** `1.7143`

## 4. Per-Class Performance
| Emotion Category | Precision | Recall | F1-Score | Support |
|---|:---:|:---:|:---:|:---:|
| `neutral` | 0.0000 | 0.0000 | 0.0000 | 25 |
| `happiness` | 0.0000 | 0.0000 | 0.0000 | 25 |
| `sadness` | 0.0000 | 0.0000 | 0.0000 | 25 |
| `anger` | 0.0000 | 0.0000 | 0.0000 | 25 |
| `fear` | 0.0000 | 0.0000 | 0.0000 | 25 |
| `surprise` | 0.0000 | 0.0000 | 0.0000 | 25 |
| `disgust` | 0.1429 | 1.0000 | 0.2500 | 25 |

## 5. Confusion Matrix
| True \ Pred | `neutral` | `happiness` | `sadness` | `anger` | `fear` | `surprise` | `disgust` |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| `neutral` | 0 | 0 | 0 | 0 | 0 | 0 | 25 |
| `happiness` | 0 | 0 | 0 | 0 | 0 | 0 | 25 |
| `sadness` | 0 | 0 | 0 | 0 | 0 | 0 | 25 |
| `anger` | 0 | 0 | 0 | 0 | 0 | 0 | 25 |
| `fear` | 0 | 0 | 0 | 0 | 0 | 0 | 25 |
| `surprise` | 0 | 0 | 0 | 0 | 0 | 0 | 25 |
| `disgust` | 0 | 0 | 0 | 0 | 0 | 0 | 25 |

## 6. Validation Notes & Limitations
- Evaluation conducted on synthetic acoustic prosody feature suite.
- Baseline ONNX weights contain unverified parameters.
- Accuracy qualification status: UNVALIDATED (qualification thresholds not met).
- Evaluation used synthetic validation fixtures; not empirical accuracy qualification.
- Model weights have unverified provenance; prohibited from production validation.
- Model failed accuracy thresholds (Macro-F1 0.0357 < 0.40). Classifications must be suppressed as INSUFFICIENT_EVIDENCE.
