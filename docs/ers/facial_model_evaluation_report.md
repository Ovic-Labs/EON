# Model Evaluation & Qualification Report: ers-facial-onnx-cpu-v1
**Record ID:** `VAL-ers-facial-onnx-cpu-v1-1795523284`  
**Validation Status:** **UNVALIDATED / RESTRICTED**  
**Evaluator:** OVIC Labs Scientific Qualification Runner  
**Timestamp:** 2026-11-24T12:28:04Z  
**Artifact SHA-256:** `0e8955c5187b2b9f69f9638e005b09abdbb1412951024e535fdefef48cc7d81b`  

## 1. Governance & Provenance
- **Training Dataset:** UNVERIFIED (Synthetic parameter initialization; no empirical training dataset)
- **Evaluation Dataset:** SYNTHETIC_FACIAL_FIXTURE_SUITE (Execution Testing Only - Accuracy Qualification BLOCKED) (`test` split)
- **Dataset License:** OVIC Internal Testing License
- **Commercial Use Allowed:** `False`
- **Restrictions:**
  - Research and pipeline testing only. Commercial deployment prohibited.

## 2. Macro Classification Metrics
| Metric | Score |
|---|:---:|
| **Accuracy** | `0.0` |
| **Balanced Accuracy** | `0.0` |
| **Macro Precision** | `0.0` |
| **Macro Recall** | `0.0` |
| **Macro F1** | `0.0` |
| **Total Samples** | `175.0` |
| **Abstention Rate** | `1.0` |

## 3. Calibration Metrics
- **Expected Calibration Error (ECE):** `0.0041`
- **Brier Score:** `0.8572`

## 4. Per-Class Performance
| Emotion Category | Precision | Recall | F1-Score | Support |
|---|:---:|:---:|:---:|:---:|
| `neutral` | 0.0000 | 0.0000 | 0.0000 | 0 |
| `happiness` | 0.0000 | 0.0000 | 0.0000 | 0 |
| `sadness` | 0.0000 | 0.0000 | 0.0000 | 0 |
| `anger` | 0.0000 | 0.0000 | 0.0000 | 0 |
| `fear` | 0.0000 | 0.0000 | 0.0000 | 0 |
| `surprise` | 0.0000 | 0.0000 | 0.0000 | 0 |
| `disgust` | 0.0000 | 0.0000 | 0.0000 | 0 |

## 5. Confusion Matrix
| True \ Pred | `neutral` | `happiness` | `sadness` | `anger` | `fear` | `surprise` | `disgust` |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| `neutral` | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `happiness` | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `sadness` | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `anger` | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `fear` | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `surprise` | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `disgust` | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

## 6. Validation Notes & Limitations
- Evaluation conducted on synthetic test partitions.
- Baseline ONNX weights contain unverified parameters.
- Accuracy qualification status: UNVALIDATED (qualification thresholds not met; scientific accuracy qualification BLOCKED).
- Evaluation used synthetic validation fixtures; not empirical accuracy qualification.
- Model weights have unverified provenance; prohibited from production validation.
- Model failed accuracy thresholds (Macro-F1 0.0 < 0.40). Classifications must be suppressed as INSUFFICIENT_EVIDENCE.
