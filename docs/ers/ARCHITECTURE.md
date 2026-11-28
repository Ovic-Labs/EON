# OVIC EON ERS Architecture

## 1. Subsystem Overview

`eon_ers` is a standalone, modular, CPU-first multimodal affective observation engine designed to run independently of future EON subsystems while providing clean event-bus boundaries (`eon_ers.core.adapter.CoreEventBusAdapter`).

### Core Modules
- `eon_ers.engine.ERSEngine`: Asynchronous orchestrator coordinating facial, speech, text, video, fusion, consent, metrics, and temporal smoothing.
- `eon_ers.facial`: Multi-candidate `HeuristicFaceDetector`, `FacialPreprocessor` (crop, alignment, finite normalization), `HeuristicLandmarkDetector`, `ExperimentalRegionalFeatureExtractor`, `ONNXFacialModelAdapter`, and `FacialPipeline`.
- `eon_ers.audio` & `eon_ers.speech`: Bounded `AudioDecoder` (WAV PCM 8/16/24/32-bit, stereo-to-mono, headerless PCM), `AudioResampler` (polyphase CPU resampling), `AudioSegmenter`, adaptive `VoiceActivityDetector`, `AcousticFeatureExtractor`, and `SpeechPipeline`.
- `eon_ers.text`: `TextNormalizer` (UTF-8, NFC, length bounds), `TextTokenizer` (Unicode word/punctuation cues & hashed vectors), `ExperimentalTextAffectAdapter`, `ONNXTextModelAdapter`, and `TextPipeline`.
- `eon_ers.video`: Bounded streaming `VideoDecoder` (RIFF AVI MJPEG, animated GIF/WEBP), `FrameSampler` (FPS + duplicate skipping + hard cap), ephemeral `SessionFaceTracker` (IoU matching without biometric vectors), and `VideoPipeline`.
- `eon_ers.fusion`: `ObservationAligner`, `ReliabilityWeighter`, `DivergenceCalculator` (Jensen-Shannon divergence), and `MultimodalFusionPipeline` (1-, 2-, and 3-modality Bayesian fusion with validation isolation and correlated-agreement dampening).
- `eon_ers.models`, `evaluation`, `training`: `ModelRegistry` (`MODEL_DISCOVERED`, `MODEL_LOADED_UNVALIDATED`, `MODEL_VALIDATED`, `MODEL_REJECTED`, `MODEL_REVOKED`), `ModelLoader`, `ModelValidationRecord`, `DatasetMetadata` (SHA-256 + `safe_extract_archive`), `EvaluationExecutionProof` (Ed25519), `CheckpointManager`, `ModelTrainingPipeline`.
- `eon_ers.api`, `live`, `sdk`: `APIKeyAuthManager` (PBKDF2 key verification, RBAC, expiry, session isolation), `SlidingWindowRateLimiter`, FastAPI `/api/v1/*` + legacy `/api/*`, `LiveSessionRecord` FSM + backpressure WebSocket, 15-view HTML enterprise console, and `ERSClient` SDK.
- `eon_ers.privacy`, `safety`, `monitoring`: Hashed `ConsentManager`, `MediaRetentionGuard`, `SensitiveDataRedactor`, `assert_no_actuator_commands`, `StructuredJSONFormatter`, `PerformanceTracker`, and `collect_system_diagnostics`.
