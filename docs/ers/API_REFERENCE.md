# ERS API Reference

## 1. Engine (`eon_ers.engine.ERSEngine`)

### Methods

- `async initialize() -> None`: Initializes facial, speech, and fusion pipelines and loads verified model adapters.
- `async start() -> None`: Transitions engine state from `INITIALIZED` to `RUNNING`.
- `register_consent(session_id: str, consent_reference: str) -> None`: Registers active consent (stores SHA-256 digest only).
- `revoke_consent(session_id: str) -> None`: Immediately revokes active session consent.
- `async process(inp: ERSInput) -> EmotionObservation | FusionResult`: Routes input by modality; enforces consent and scrubs media payloads in `try/finally`.
- `async process_facial(inp: ERSInput) -> EmotionObservation`: Executes 12-stage facial pipeline with quality checks, unvalidated suppression, and temporal smoothing.
- `async process_speech(inp: ERSInput) -> EmotionObservation`: Executes 12-stage speech acoustic pipeline with prosody extraction, unvalidated suppression, and temporal smoothing.
- `async process_multimodal(facial_input: ERSInput | None, speech_input: ERSInput | None) -> FusionResult`: Executes concurrent unimodal pipelines, alignment, eligibility/validation isolation, Bayesian fusion, and temporal smoothing.
- `health() -> dict[str, Any]`: Returns component health status, pipeline readiness, and lifecycle state.
- `get_metrics() -> dict[str, Any]`: Returns throughput, p50/p90/p95/p99 latency percentiles, and memory RSS statistics.
- `reset_session(session_id: str) -> None`: Flushes temporal smoothing buffers and session history.
- `async stop() -> None`: Drains resources and clears active session buffers.

---

## 2. Configuration (`eon_ers.config.ERSConfig`)

| Field | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `enable_facial` | `bool` | `True` | Enable visual facial processing pipeline |
| `enable_speech` | `bool` | `True` | Enable acoustic speech processing pipeline |
| `enable_multimodal_fusion` | `bool` | `True` | Enable multimodal probability fusion |
| `device` | `DeviceType` | `CPU` | Compute execution target (`cpu`, `cuda`, `openvino`) |
| `num_threads` | `int` | `4` | CPU worker thread pool size |
| `facial_model_path` | `str \| None` | `None` | Path to verified facial ONNX model file |
| `speech_model_path` | `str \| None` | `None` | Path to verified speech ONNX model file |
| `alignment_window_seconds` | `float` | `0.5` | Maximum multimodal timestamp divergence |
| `temporal_smoothing_alpha` | `float` | `0.35` | Exponential moving average alpha factor |
| `temporal_half_life_seconds` | `float` | `3.0` | Half-life in seconds for historical state decay |
| `confidence_threshold` | `float` | `0.35` | Minimum confidence score to prevent abstention |
| `uncertainty_threshold` | `float` | `0.65` | Maximum uncertainty threshold before flagging insufficient evidence |
| `require_explicit_consent` | `bool` | `True` | Enforce valid consent reference before processing |
| `zero_disk_retention` | `bool` | `True` | Enforce in-memory volatile processing with zero disk persistence |

---

## 3. Data Contracts (`eon_ers.contracts`)

### `ERSInput`
- `observation_id: str`
- `session_id: str`
- `timestamp: float`
- `modality: Modality`
- `consent_reference: str`
- `image_payload: bytes | None` (`scrub_media_payload()` clears both image & audio payloads)
- `audio_payload: bytes | None`
- `sample_rate: int | None`
- `image_dimensions: tuple[int, int] | None`
- `source_metadata: dict[str, Any]`
- `quality_metadata: dict[str, Any]`

### `EmotionObservation`
- `observation_id: str`, `timestamp: float`, `modality: Modality`
- `expression_observations: dict[str, Any]`
- `emotion_probabilities: dict[str, float]`
- `dominant_estimate: str`
- `confidence: float`, `uncertainty: float`, `quality_score: float` (`0.0` to `1.0`)
- `model_id: str`, `model_version: str`, `processing_latency_ms: float`
- `status: ObservationStatus`, `input_quality: InputQualityStatus`, `model_state: ModelState`
- `is_calibrated: bool`, `raw_confidence: float | None`, `is_validated: bool`
- `limitations: list[str]`
- `is_definitive_claim: bool = False` (Frozen invariant)

### `FusionResult`
- `result_id: str`, `timestamp: float`
- `facial_observation: EmotionObservation | None`, `speech_observation: EmotionObservation | None`
- `fused_probabilities: dict[str, float]`, `dominant_estimate: str`
- `modality_weights: dict[str, float]`, `confidence: float`, `uncertainty: float`
- `conflicting_evidence: bool`, `conflict_metric: float`, `missing_modalities: list[Modality]`
- `quality_summary: dict[str, float]`, `limitations: list[str]`
- `contributing_model_states: dict[str, str]`, `classification_eligible_modalities: list[str]`
- `diagnostic_modalities: list[str]`, `fusion_status: str`, `is_validated: bool`
- `is_definitive_claim: bool = False` (Frozen invariant)

---

## 4. Model Integrity & Loading (`eon_ers.models`)

- `ModelManifest`: Cryptographic SHA-256 manifest, tensor shape/name/dtype contracts (`validate_tensor_contracts()`), class ordering (`validate_class_ordering()`), and `verify_integrity()`.
- `ModelLoader.validate_and_load_onnx_weights(...)`: Validates non-empty file, SHA-256, `framework`/`modality`/major version compatibility, ONNX protobuf integrity (`onnx.checker`), external tensor completeness, initializer finiteness, contracts, and CPU smoke inference.
- `ModelLoader.load_onnx_session(...)`: Integrity-checked wrapper returning an `onnxruntime.InferenceSession`.
- `ModelValidationRecord`: Auditable empirical validation record with `verify_artifact_binding()` and Ed25519 proof metadata (`execution_proof_key_id`, `execution_proof_algorithm`, `execution_proof_signature`).

---

## 5. Dataset Integrity, Ed25519 Proofs & Evaluation (`eon_ers.evaluation`)

- `DatasetMetadata`: Provenance metadata with `verify_archive()`, `verify_manifest()`, and `safe_extract_archive()` (traversal, symlink, size-limit, and compression-ratio bomb protection).
- `EvaluationSample`, `EvaluationPartition`, `create_subject_independent_partition()`: Enforces unique `sample_id`s and strictly disjoint train/val/test subject sets.
- `SigningKeyPair`, `TrustedKeyRegistry`, `EvaluationExecutionProof`: Ed25519 signing/verification with key rotation (`rotate_key`) and revocation (`revoke_key`).
- `ModelEvaluator.evaluate_predictions(...)`: Validates sample count alignment, supported labels, probability schema/finiteness/unit-sum, manifest dimensions, and Ed25519 execution proof before computing classification/calibration metrics.

---

## 6. Training & ONNX Export (`eon_ers.training`)

- `SamplePreprocessor`, `FeatureExtractor`, `ZeroLeakageNormalizer`: Deterministic media preprocessing and zero-leakage feature scaling fitted strictly on training data.
- `CPUModelTrainer`, `TemperatureCalibrator`: CPU-only MLP training with Adam optimization and bounded scalar NLL temperature scaling.
- `ONNXModelExporter`: Strict dimension matching (zero padding/truncation), atomic `.onnx.tmp` export, and CPU ONNX Runtime vs. NumPy numerical parity verification (`ONNX_LOGIT_PARITY_ATOL`, `ONNX_PROB_PARITY_ATOL`).
- `ModelTrainingPipeline`: 15-stage end-to-end training/validation orchestrator requiring physical archive verification, genuine stage execution, and all-stage pass gating.
