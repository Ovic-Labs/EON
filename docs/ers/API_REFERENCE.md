# ERS API Reference

## 1. Engine (`eon_ers.engine.ERSEngine`)

### Methods

- `async initialize() -> None`: Initializes pipelines, evaluates device configuration, and loads verified model adapters.
- `async start() -> None`: Transitions engine state from `INITIALIZED` to `RUNNING`.
- `async process(input: ERSInput) -> EmotionObservation | FusionResult`: Universal routing method executing facial, speech, or multimodal processing based on `input.modality`.
- `async process_facial(input: ERSInput) -> EmotionObservation`: Executes 12-stage facial expression pipeline with quality checks and temporal smoothing.
- `async process_speech(input: ERSInput) -> EmotionObservation`: Executes 12-stage speech acoustic pipeline with prosody extraction and temporal smoothing.
- `async process_multimodal(facial_input: ERSInput | None, speech_input: ERSInput | None) -> FusionResult`: Executes time-window alignment, reliability weighting, and Bayesian probability fusion.
- `health() -> dict[str, Any]`: Returns component health status, pipeline availability, and lifecycle state.
- `get_metrics() -> dict[str, Any]`: Returns throughput, p50/p90/p95/p99 latency percentiles, and memory RSS statistics.
- `reset_session(session_id: str) -> None`: Securely flushes temporal smoothing buffers and session history.
- `async stop() -> None`: Gracefully drains queues and stops processing workers.

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
- `image_payload: bytes | None`
- `audio_payload: bytes | None`
- `sample_rate: int | None`
- `image_dimensions: tuple[int, int] | None`
- `source_metadata: dict[str, Any]`
- `quality_metadata: dict[str, Any]`

### `EmotionObservation`
- `observation_id: str`
- `timestamp: float`
- `modality: Modality`
- `expression_observations: dict[str, Any]`
- `emotion_probabilities: dict[str, float]`
- `dominant_estimate: str`
- `confidence: float` (0.0 to 1.0)
- `uncertainty: float` (0.0 to 1.0)
- `quality_score: float` (0.0 to 1.0)
- `model_id: str`
- `model_version: str`
- `processing_latency_ms: float`
- `limitations: list[str]`
- `status: ObservationStatus`
- `is_definitive_claim: bool = False` (Frozen invariant)

### `FusionResult`
- `result_id: str`
- `timestamp: float`
- `facial_observation: EmotionObservation | None`
- `speech_observation: EmotionObservation | None`
- `fused_probabilities: dict[str, float]`
- `dominant_estimate: str`
- `modality_weights: dict[str, float]`
- `confidence: float`
- `uncertainty: float`
- `conflicting_evidence: bool`
- `conflict_metric: float`
- `missing_modalities: list[Modality]`
- `quality_summary: dict[str, float]`
- `limitations: list[str]`
- `is_definitive_claim: bool = False` (Frozen invariant)
