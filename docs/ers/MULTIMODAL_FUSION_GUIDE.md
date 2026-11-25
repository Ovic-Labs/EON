# Multimodal Fusion Engine Guide

## Validation-Isolated Fusion (`eon_ers.fusion.MultimodalFusionPipeline`)
- Supports **1-modality**, **2-modality** (facial + speech), and **3-modality** (facial + speech + text) alignment and Bayesian logarithmic opinion fusion.
- **Temporal Alignment:** Rejects stale observations (`age > max_staleness_seconds`, default `3.0s`) and unsynchronized cross-stream pairs (`dt > alignment_window_seconds`, default `0.5s`).
- **Missing Modalities:** Absent modalities are never imputed as `neutral`; single-validated fallbacks operate cleanly when remaining channels are missing or unvalidated.
- **Validation Isolation:** Only modalities with `ModelState.MODEL_LOADED_VALIDATED` and `is_validated=True` receive classification weights. Unvalidated channels appear solely in `diagnostic_modalities` and `excluded_modalities`.
- **Conflict & Correlation Guard:** Computes maximum pairwise Jensen-Shannon divergence (`conflict_threshold=0.45`) to attenuate confidence on diverging signals, and applies `correlated_agreement_dampening` (`0.85`) so correlated predictions do not inflate confidence artificially to `1.0`.
- **Schema (`v1.0`):** `FusionResult` exports `schema_version`, `fusion_algorithm`, `contributing_modalities` / `classification_eligible_modalities`, `excluded_modalities`, `conflict_metric`, `is_validated`, `processing_latency_ms`, and `is_definitive_claim=False`.
