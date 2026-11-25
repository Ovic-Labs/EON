# Model Training & Checkpointing Guide

## Reproducible CPU-First Pipeline (`eon_ers.training`)
`ModelTrainingPipeline.run_pipeline()` executes end-to-end training and strict fail-closed verification on CPU:
1. Archive byte integrity verification (`DatasetMetadata.verify_archive` + `safe_extract_archive`).
2. Zero-leakage subject-independent splitting (`create_subject_independent_partition`).
3. Training-only feature scaling (`FeatureNormalizer.fit` on train split only).
4. Reproducible seeded CPU MLP training with early stopping, validation loss monitoring, and integrity-verified checkpoints (`CheckpointManager.save` / `.load_latest` with `.npz` + SHA-256 `.meta.json` sidecar).
5. Post-training NLL temperature scaling calibration (`TemperatureScaler`).
6. Atomic ONNX export with `onnx.checker` + CPU parity verification (`ONNXModelExporter`, tolerance `1e-4` logits / `1e-5` probs).
7. Holdout evaluation & domain-separated **Ed25519** signing (`EvaluationExecutionProof`).

See [DATASET_ACQUISITION_GUIDE.md](DATASET_ACQUISITION_GUIDE.md) before attempting production training; licensed human affective datasets are not bundled in this repository.
