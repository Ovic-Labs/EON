# Model Evaluation & Qualification Guide

## Quantitative Evaluation (`eon_ers.metrics.evaluation` & `eon_ers.evaluation`)
Reports:
- Accuracy & **Balanced Accuracy**
- Macro Precision, Macro Recall, **Macro F1**
- Per-class Precision, Recall, F1, Support, and full Confusion Matrix
- **Expected Calibration Error (ECE)** (with inclusive zero-confidence lower bin fix `b == 0`) & **Brier Score**
- Selective abstention rate

## Qualification Thresholds
A model may only transition to empirically validated (`is_validated=True`, `MODEL_VALIDATED`) on real frozen holdout datasets when:
- `Macro-F1 >= 0.40`
- `Balanced Accuracy >= 0.40`
- `ECE <= 0.15`
- `Brier Score <= 0.35`

Synthetic fixture runs verify execution integrity only and **never** satisfy scientific qualification thresholds.
