# OVIC EON — Seven Engine Boundary Specifications

**Document ID:** `EON-SPEC-ENG-001`  
**Phase:** Phase 2 — System Architecture and Engineering Design  
**Sub-phase:** 2.2 — Seven-Engine Boundary Design  
**Status:** Approved Engineering Architecture Specification  
**Version:** 1.0.0  
**Classification:** Technical Architecture Specification  
**Document Owner:** Principal Software Architect  
**Related Documents:**
- `docs/architecture/SEVEN_ENGINE_ARCHITECTURE.md` (`EON-ARCH-ENG-001`)
- `docs/architecture/ENGINE_DEPENDENCY_MATRIX.md` (`EON-ARCH-DEP-002`)
- `docs/architecture/ENGINE_INPUT_OUTPUT_CONTRACTS.md` (`EON-SPEC-ENG-IO-001`)
- `docs/architecture/SYSTEM_LAYERED_ARCHITECTURE.md` (`EON-ARCH-LAYERS-001`)

---

## 1. Executive Summary

This document establishes the exhaustive engineering boundary specifications for each of the **Seven Intelligence Engines** of OVIC EON. Each engine is specified across the mandatory 27-item template to enable independent development, rigorous unit testing, and decoupled verification without cross-team ambiguity.

---

## 2. Engine 1: Emotion Recognition System (ERS)

### 2.1 Engine ID and Name
- **Engine ID:** `ERS`
- **Full Name:** Emotion Recognition System
- **Package Location:** `src/eon/engines/ers/`

### 2.2 Mission and Purpose
Process multimodal human behavioral cues (facial action units, acoustic speech prosody, and transcribed text hints) to estimate continuous Valence-Arousal-Dominance (VAD) affective trajectories and discrete emotion distributions with calibrated uncertainty.

### 2.3 Scope
- Facial action unit (AU) intensity tracking (12 FACS AUs).
- Acoustic speech prosody feature extraction ($F_0$, energy, jitter, shimmer, speaking rate).
- Multimodal gated cross-attention fusion.
- Continuous VAD coordinate regression with temperature calibration.
- Discrete emotion category scoring (6 Ekman categories + Neutral).
- Divergence and conflict detection between visual and acoustic signals (e.g., smiling while speaking in distressed tones).

### 2.4 Out-of-Scope Responsibilities
- Biometric facial recognition or identity authentication.
- Long-term memory storage or emotional history persistence (owned by EMS).
- Cognitive appraisal or empathy reasoning (owned by ERE).
- Deciding what the robot should say or do (owned by SIE and ERG).
- Directly acquiring camera or microphone hardware frames (owned by L2/L3).

### 2.5 Functional Requirements
- `REQ-ERS-001`: Ingest `ObservationPayload` events from visual and acoustic perception pipelines.
- `REQ-ERS-002`: Compute continuous VAD scores in $[-1.0, +1.0]^3$ space with calibrated confidence.
- `REQ-ERS-003`: Detect multi-modal cue divergence: assert `conflict_flag=True` when visual valence and acoustic valence diverge by $>0.75$.
- `REQ-ERS-004`: Publish `EmotionEstimatePayload` events within $\le 25\text{ ms}$ of observation receipt.
- `REQ-ERS-005`: Dynamically degrade to unimodal estimation when visual or acoustic cues are flagged `QualityStatus.MISSING`.

### 2.6 Non-Functional Requirements
- Latency: p95 processing latency $\le 25\text{ ms}$ on 4-core Cortex-A76 CPU.
- Throughput: Sustained observation processing rate $\ge 30\text{ fps}$.
- Memory: Heap footprint $\le 65\text{ MB}$.
- Availability: $99.99\%$ continuous operation without memory leakage.

### 2.7 Inputs and Input Schemas
- `ObservationPayload` (`eon.schemas.observations`): Modalities `VISUAL`, `AUDIO`, `TEXT`, `MULTIMODAL`.
- `VisualObservationData`: Action unit intensities, head pose yaw/pitch/roll.
- `AudioObservationData`: Pitch, energy, spectral tilt, VAD speech flag.

### 2.8 Outputs and Output Schemas
- `EmotionEstimatePayload` (`eon.schemas.emotions`): Continuous VAD scores (`valence`, `arousal`, `dominance`), discrete emotion scores, uncertainty metadata, conflict flag, modality quality indicators.

### 2.9 Events Consumed
- `observation.visual.*` (Topic: `observation.visual.face_mesh`)
- `observation.audio.*` (Topic: `observation.audio.speech_emotion`)
- `observation.text.*` (Topic: `observation.text.sentiment`)
- `observation.multimodal.*` (Topic: `observation.multimodal.fused`)

### 2.10 Events Published
- `eon.emotion_estimate` (Topic: `emotion.estimate.realtime`)
- `eon.component_health` (Topic: `health.ers`)

### 2.11 Public Interfaces
```python
class EonEngineInterface(ABC):
    async def initialize(config: EngineConfig, event_bus: EventBus, context: Any) -> None: ...
    async def start() -> None: ...
    async def stop(timeout_seconds: float) -> None: ...
    async def handle_event(envelope: EventEnvelope[ObservationPayload]) -> None: ...
    async def get_health() -> ComponentHealthPayload: ...
```

### 2.12 Internal Component Boundaries
- `ErsIngestionRouter`: Validates and routes incoming observation envelopes.
- `UnimodalCalibrator`: Applies temperature scaling to unimodal feature inputs.
- `GatedFusionProcessor`: Gated cross-modal attention combining active modalities.
- `ConflictDetector`: Identifies affective masking or sarcastic tone divergence.
- `TrajectorySmoother`: Exponential moving average (EMA) filter preventing erratic jitter.

### 2.13 Dependencies
- Internal: `eon.core.event_bus`, `eon.schemas`, `eon.interfaces`.
- Adapters (L7): `OnnxInferenceAdapter` (for fusion head).
- External: `numpy`, `scipy` (no direct GUI or hardware packages).

### 2.14 Forbidden Dependencies
- Prohibited from importing or calling other engines (EMS, ERE, PSE, SIE, ERG, HBU).
- Prohibited from importing camera drivers (`cv2.VideoCapture`), ALSA audio, or disk database libraries (`sqlite3`).

### 2.15 Execution Model
- Asynchronous subscriber on L5 Core Event Bus.
- Numerical fusion inference offloaded to bounded worker threadpool (`ThreadPoolExecutor`).
- Internal event queue capacity: 100 items with `DROP_OLDEST` policy.

### 2.16 Lifecycle Requirements
- `initialize()` loads calibration parameters; `start()` launches queue worker; `stop()` cancels workers and drains queues within 2.0s.

### 2.17 Failure Modes
- Corrupted observation payloads -> Logged, discarded, `corrupted_payload_count` incremented.
- ONNX model inference crash -> Fall back to weighted linear average of unimodal scores.
- Queue overflow -> Oldest observation dropped, `dropped_observations` metric incremented.

### 2.18 Timeout and Cancellation Behaviour
- Subscribed handler deadline: $30\text{ ms}$. If deadline exceeded, task cancelled via `asyncio.CancelledError`; last valid EMA trajectory published.

### 2.19 Degraded Operation
- **Degraded Mode 1 (Audio Missing):** Evaluates visual AUs alone; flags `modality_quality_scores.audio = 0.0`.
- **Degraded Mode 2 (Video Missing):** Evaluates speech prosody alone; flags `modality_quality_scores.visual = 0.0`.
- **Degraded Mode 3 (Both Missing):** Emits neutral affective state $(0.0, 0.0, 0.0)$ with `QualityStatus.MISSING`.

### 2.20 Security Requirements
- Payload validation using Pydantic v2 schemas; rejects arbitrary object deserialization; zero execution of unsanitized code.

### 2.21 Privacy Requirements
- Strictly zero persistence of biometric feature vectors; does not generate facial identity embeddings; all state in volatile RAM.

### 2.22 Resource Requirements
- CPU: $\le 15\%$ of 1 core (Cortex-A76 @ 2.4 GHz). RAM: $\le 65\text{ MB}$.

### 2.23 Logging and Observability
- Emits structured JSON logs. Metrics: `ers_latency_p95_ms`, `ers_conflict_count`, `ers_drop_count`.

### 2.24 Unit-Test Requirements
- 100% mocked input envelopes; tests for conflicting modalities (smile + angry voice); tests for missing modalities; numerical boundary tests ($[-1.0, 1.0]$).

### 2.25 Integration-Test Requirements
- End-to-end event flow: Ingest synthetic `ObservationPayload` -> Publish `EmotionEstimatePayload` via Core Event Bus -> Verify delivery to ERE subscriber.

### 2.26 Acceptance Criteria
- Latency $\le 25\text{ ms}$ under 30 fps observation stream; $0$ unhandled exceptions under 10,000 malformed input envelopes.

### 2.27 Open Technical Questions
- Evaluation of Dirichlet calibration vs. temperature scaling for discrete category calibration under non-frontal facial yaw.

---

## 3. Engine 2: Emotion Modelling System (EMS)

### 3.1 Engine ID and Name
- **Engine ID:** `EMS`
- **Full Name:** Emotion Modelling System (encompassing Affective Memory)
- **Package Location:** `src/eon/engines/ems/`

### 3.2 Mission and Purpose
Maintain the longitudinal affective state dynamics of the robot and interaction participants, manage active working memory, govern consent-gated episodic memory, and enforce verifiable forgetting.

### 3.3 Scope
- Temporal affective decay modeling (exponential decay of arousal back to baseline).
- Participant mood tracking across conversational turns.
- Active short-term working memory management.
- Optional, encrypted episodic memory storage (SQLite / SQLCipher).
- Explicit user consent verification for memory retention.
- GDPR Article 17 "Right to Erasure" coordination (cryptographic key shredding).

### 3.4 Out-of-Scope Responsibilities
- Real-time sensory feature extraction (owned by ERS).
- Empathy reasoning or response selection (owned by ERE / ERG).
- Conversation turn-taking arbitration (owned by SIE).

### 3.5 Functional Requirements
- `REQ-EMS-001`: Ingest `EmotionEstimatePayload` events and update participant affective state.
- `REQ-EMS-002`: Apply temporal decay function $A(t) = A_0 \cdot e^{-\lambda \Delta t}$ to arousal levels during periods of silence.
- `REQ-EMS-003`: Maintain active conversational turn memory in volatile RAM (capacity: 20 turns).
- `REQ-EMS-004`: If consent granted, persist episodic interaction summaries to encrypted storage.
- `REQ-EMS-005`: Upon receipt of `eon.privacy.delete_user`, execute cryptographic key shredding and database row purge within $\le 500\text{ ms}$.

### 3.6 Non-Functional Requirements
- Latency: State update $\le 5.0\text{ ms}$; episodic retrieval $\le 15.0\text{ ms}$.
- Storage footprint: Bounded to configured quota (default $\le 500\text{ MB}$).
- Security: Field-level encryption using AES-256-GCM.

### 3.7 Inputs and Input Schemas
- `EmotionEstimatePayload` (`eon.schemas.emotions`).
- `InteractionContextPayload` (`eon.schemas.context`).
- Proposed `MemoryQueryPayload` and `UserDeletionRequestPayload`.

### 3.8 Outputs and Output Schemas
- Proposed `AffectiveStateUpdatePayload` (`eon.schemas.affective_state`).
- Proposed `MemoryRecordCollectionPayload` (`eon.schemas.memory`).
- Proposed `DeletionReceiptPayload`.

### 3.9 Events Consumed
- `eon.emotion_estimate` (Topic: `emotion.estimate.realtime`)
- `eon.context_update` (Topic: `context.session.update`)
- `eon.privacy.delete_user` (Topic: `privacy.gdpr.purge`)

### 3.10 Events Published
- `eon.affective_state` (Topic: `ems.state.update`)
- `eon.memory.retrieved` (Topic: `ems.memory.context`)
- `eon.component_health` (Topic: `health.ems`)

### 3.11 Public Interfaces
```python
class EmsEngineInterface(EonEngineInterface):
    async def get_current_affective_state(participant_id: str) -> AffectiveStatePayload: ...
    async def query_interaction_history(query: MemoryQuery) -> list[MemoryRecord]: ...
    async def purge_user_data(user_id: str, auth_token: str) -> DeletionReceipt: ...
```

### 3.12 Internal Component Boundaries
- `AffectiveDynamicsEngine`: Calculates emotional decay and mood integration.
- `WorkingMemoryCache`: RAM-only FIFO ring buffer of recent turns.
- `EpisodicStorageProvider`: Encrypted SQLite interface with SQLCipher.
- `CryptoKeyShredder`: Manages per-user AES-256 keys; destroys keys upon deletion.

### 3.13 Dependencies
- Internal: `eon.core.event_bus`, `eon.schemas`, `eon.interfaces`.
- Storage: `sqlite3` (standard library), embedded SQLCipher.

### 3.14 Forbidden Dependencies
- Prohibited from importing perception packages (MediaPipe, PyTorch, ONNX).
- Prohibited from invoking speech synthesis or robot motion controllers.

### 3.15 Execution Model
- Async event consumption; storage I/O offloaded to dedicated single-threaded SQLite worker thread.

### 3.16 Lifecycle Requirements
- `initialize()` checks database encryption keys; `start()` starts decay timer; `stop()` flushes write-ahead logs within 3.0s.

### 3.17 Failure Modes
- Database lock or disk-full error -> Degrades to RAM-only ephemeral mode; logs `SafetyAdvisoryLevel.WARNING`.

### 3.18 Timeout and Cancellation Behaviour
- Memory retrieval timeout: $25\text{ ms}$. If exceeded, returns empty memory collection to prevent stalling dialogue.

### 3.19 Degraded Operation
- **Degraded Mode (No Disk Storage):** Functions entirely in volatile RAM; persistent storage disabled; zero user data stored on disk.

### 3.20 Security Requirements
- Encrypted-at-rest database; per-user key isolation; rejection of SQL injection via prepared statements.

### 3.21 Privacy Requirements
- Anti-Profiling Invariant: Strictly prohibited from storing inferred psychiatric labels or psychological diagnoses; stores only explicit user preferences and interaction counts.

### 3.22 Resource Requirements
- CPU: $\le 5\%$ of 1 core. RAM: $\le 45\text{ MB}$. Disk: $\le 500\text{ MB}$ bounded.

### 3.23 Logging and Observability
- Logs storage operations with scrubbed PII; metrics: `ems_active_sessions`, `ems_decay_cycles`, `ems_purge_latency_ms`.

### 3.24 Unit-Test Requirements
- Test exponential decay calculation; test cryptographic key shredding and unrecoverability; test FIFO queue eviction at turn limit.

### 3.25 Integration-Test Requirements
- Store episodic memory -> Query via Core Event Bus -> Purge user data -> Verify query returns zero records.

### 2.26 Acceptance Criteria
- Complete data erasure within $\le 500\text{ ms}$; zero plaintext recovery from database journal.

### 2.27 Open Technical Questions
- Evaluation of vector embedding retrieval (Qdrant Embedded) vs. pure SQLite relational indexing for resource-constrained edge tiers.

---

## 4. Engine 3: Empathy Reasoning Engine (ERE)

### 4.1 Engine ID and Name
- **Engine ID:** `ERE`
- **Full Name:** Empathy Reasoning Engine
- **Package Location:** `src/eon/engines/ere/`

### 4.2 Mission and Purpose
Evaluate the cognitive and emotional context of human participants using Scherer's Component Process Model (CPM) of appraisal, formulate empathetic hypotheses, and select supportive communicative intents without psychological manipulation.

### 4.3 Scope
- Scherer CPM cognitive appraisal checks:
  1. Goal Relevance (Does this event affect the user?).
  2. Goal Congruence (Is this event conducive or obstructive?).
  3. Coping Potential (Can the user manage this situation?).
- Perspective-taking / Theory of Mind (ToM) modeling.
- Supportive strategy selection (`"active_listening"`, `"reassurance"`, `"clarification"`, `"offer_assistance"`).
- Escalation detection and interaction boundary enforcement.

### 4.4 Out-of-Scope Responsibilities
- Surface natural language token generation (owned by ERG).
- Audio vocoding or speech synthesis (owned by ERG).
- Conversation turn-taking arbitration (owned by SIE).
- Medical diagnosis or psychological intervention.

### 4.5 Functional Requirements
- `REQ-ERE-001`: Ingest `EmotionEstimatePayload`, `InteractionContextPayload`, and episodic context.
- `REQ-ERE-002`: Evaluate CPM appraisal variables producing continuous goal congruence scores in $[-1.0, +1.0]$.
- `REQ-ERE-003`: Detect participant distress (Valence $< -0.5$ and Congruence $< -0.5$) and formulate supportive intent.
- `REQ-ERE-004`: Publish `ResponseIntentPayload` within $\le 15\text{ ms}$ of observation receipt.
- `REQ-ERE-005`: Enforce non-manipulative interaction constraints: reject intent generation designed to induce emotional dependency.

### 4.6 Non-Functional Requirements
- Latency: p95 reasoning latency $\le 15\text{ ms}$ on edge CPU.
- Determinism: 100% reproducible intent selection for identical input states.
- Memory: $\le 35\text{ MB}$ heap.

### 4.7 Inputs and Input Schemas
- `EmotionEstimatePayload` (`eon.schemas.emotions`).
- `InteractionContextPayload` (`eon.schemas.context`).
- Proposed `AffectiveStateUpdatePayload`.

### 4.8 Outputs and Output Schemas
- Proposed `ResponseIntentPayload` (`eon.schemas.intents`): Category, strategy, priority, semantic goal, safety constraints (`is_authoritative_stop=False`).

### 4.9 Events Consumed
- `eon.emotion_estimate` (Topic: `emotion.estimate.realtime`)
- `eon.affective_state` (Topic: `ems.state.update`)
- `eon.context_update` (Topic: `context.session.update`)

### 4.10 Events Published
- `eon.response_intent` (Topic: `intent.empathy_reasoned`)
- `eon.component_health` (Topic: `health.ere`)

### 4.11 Public Interfaces
```python
class EreEngineInterface(EonEngineInterface):
    async def evaluate_appraisal(context: AppraisalContext) -> AppraisalOutcome: ...
    async def select_supportive_strategy(outcome: AppraisalOutcome) -> ResponseIntentPayload: ...
```

### 4.12 Internal Component Boundaries
- `CpmAppraisalEvaluator`: Rule-based evaluation of Goal Relevance, Congruence, and Coping.
- `TheoryOfMindTracker`: Estimates participant belief state and emotional needs.
- `SupportiveStrategySelector`: Maps appraisal outcomes to communicative intents.
- `EthicalGuardrailFilter`: Validates intent against anti-manipulation policies.

### 4.13 Dependencies
- Internal: `eon.core.event_bus`, `eon.schemas`, `eon.interfaces`.
- Adapters (L7): `DeterministicRuleAdapter`.

### 4.14 Forbidden Dependencies
- Prohibited from importing large language models, neural network weights, or external cloud APIs.
- Prohibited from commanding robot hardware motors or TTS synthesizers.

### 4.15 Execution Model
- Pure asynchronous CPU evaluation; executes synchronously inside event handler within sub-millisecond budgets.

### 4.16 Lifecycle Requirements
- `initialize()` compiles appraisal decision tables; `start()` activates event subscription; `stop()` completes immediately.

### 4.17 Failure Modes
- Ambiguous or conflicting emotional cues -> Emits neutral exploratory intent (`"clarification_request"`).
- Rule engine exception -> Emits default fallback intent (`"polite_acknowledgment"`).

### 4.18 Timeout and Cancellation Behaviour
- Handler deadline: $20\text{ ms}$. If deadline exceeded, emits fallback listening intent.

### 4.19 Degraded Operation
- **Degraded Mode:** Operates on text sentiment alone when multimodal emotion estimates are unavailable.

### 4.20 Security Requirements
- Strict schema validation; prevents intent tampering or priority inversion.

### 4.21 Privacy Requirements
- Retains zero session state internally; operates as a stateless cognitive evaluator.

### 4.22 Resource Requirements
- CPU: $\le 3\%$ of 1 core. RAM: $\le 35\text{ MB}$.

### 4.23 Logging and Observability
- Logs selected appraisal strategy; metrics: `ere_reasoning_latency_ms`, `ere_intent_categories_total`.

### 4.24 Unit-Test Requirements
- Unit tests for all CPM decision branches; tests verifying rejection of manipulative or sycophantic strategies.

### 4.25 Integration-Test Requirements
- End-to-end event flow: Emotion estimate input -> ERE evaluates CPM -> Emits `ResponseIntentPayload` -> Verified by SIE / ERG.

### 4.26 Acceptance Criteria
- Reasoning latency $\le 15\text{ ms}$; 100% deterministic strategy selection across reference test suite.

### 4.27 Open Technical Questions
- Parameterization of culture-specific appraisal weights for cross-regional robot deployments.

---

## 5. Engine 4: Personality and Social Engine (PSE)

### 5.1 Engine ID and Name
- **Engine ID:** `PSE`
- **Full Name:** Personality and Social Engine
- **Package Location:** `src/eon/engines/pse/`

### 5.2 Mission and Purpose
Maintain and express a consistent, configurable robot personality profile, enforce mathematical anti-drift clamps across interaction styles, and reflect explicit user preferences.

### 5.3 Scope
- Declarative personality profile loading (JSON / YAML persona definitions).
- Dynamic style parameter resolution (formality, verbosity, speaking pace, humor, empathy depth).
- Mathematical style clamping preventing personality drift during extended dialogue.
- Session-level persona overrides based on user preferences.
- Anti-anthropomorphic transparency enforcement.

### 5.4 Out-of-Scope Responsibilities
- Deciding what factual information to speak (owned by ERG).
- Turn-taking arbitration (owned by SIE).
- Cognitive appraisal of user distress (owned by ERE).

### 5.5 Functional Requirements
- `REQ-PSE-001`: Load validated base persona profiles from configuration assets.
- `REQ-PSE-002`: Compute continuous style vectors: `formality` $[0.0, 1.0]$, `verbosity` $[0.0, 1.0]$, `pace_multiplier` $[0.8, 1.3]$.
- `REQ-PSE-003`: Apply hard clamping bounds preventing personality drift regardless of user provocation.
- `REQ-PSE-004`: Publish `PersonaStylePayload` within $\le 5.0\text{ ms}$ upon context change.
- `REQ-PSE-005`: Provide explicit user preference controls allowing users to adjust formality and verbosity.

### 5.6 Non-Functional Requirements
- Latency: Style resolution $\le 5.0\text{ ms}$.
- Consistency: Zero mathematical drift across 10,000 continuous conversational turns.
- Memory: $\le 25\text{ MB}$ heap.

### 5.7 Inputs and Input Schemas
- `InteractionContextPayload` (`eon.schemas.context`).
- Proposed `PersonaConfigurationAsset` and `UserPreferencePayload`.

### 5.8 Outputs and Output Schemas
- Proposed `PersonaStylePayload` (`eon.schemas.persona`): Active persona ID, numerical style parameters, safety clamps verified flag.

### 5.9 Events Consumed
- `eon.context_update` (Topic: `context.session.update`)
- `eon.persona.configure` (Topic: `persona.config.override`)

### 5.10 Events Published
- `eon.persona_style` (Topic: `persona.style.vector`)
- `eon.component_health` (Topic: `health.pse`)

### 5.11 Public Interfaces
```python
class PseEngineInterface(EonEngineInterface):
    async def load_persona(persona_id: str) -> None: ...
    async def resolve_style(context: InteractionContextPayload) -> PersonaStylePayload: ...
```

### 5.12 Internal Component Boundaries
- `PersonaRegistry`: Loads and validates persona configuration files.
- `StyleVectorResolver`: Calculates situational style adjustments.
- `AntiDriftClampingModule`: Enforces hard min/max bounds on all numerical style vectors.

### 5.13 Dependencies
- Internal: `eon.core.event_bus`, `eon.schemas`, `eon.interfaces`.

### 5.14 Forbidden Dependencies
- Prohibited from importing ML inference runtimes, SLM models, audio vocoders, or robot motion APIs.

### 5.15 Execution Model
- Lightweight async event handler; stateless algebraic computation.

### 5.16 Lifecycle Requirements
- `initialize()` validates default persona JSON; `start()` emits initial style vector; `stop()` completes immediately.

### 5.17 Failure Modes
- Invalid persona configuration file -> Falls back to built-in default neutral persona.

### 5.18 Timeout and Cancellation Behaviour
- Handler execution deadline: $10\text{ ms}$.

### 5.19 Degraded Operation
- **Degraded Mode:** Uses static, unadjusted baseline persona parameters.

### 5.20 Security Requirements
- Persona configuration files verified against JSON schema; rejects unauthorized modification of safety clamps.

### 5.21 Privacy Requirements
- Stores no user PII; maintains only numerical style weights.

### 5.22 Resource Requirements
- CPU: $\le 1\%$ of 1 core. RAM: $\le 25\text{ MB}$.

### 5.23 Logging and Observability
- Logs style vector transitions; metrics: `pse_formality_score`, `pse_verbosity_score`.

### 5.24 Unit-Test Requirements
- Unit tests validating that clamped parameters cannot exceed min/max bounds under extreme input values.

### 5.25 Integration-Test Requirements
- Modify persona config -> Verify updated `PersonaStylePayload` received by ERG dialogue generator.

### 5.26 Acceptance Criteria
- Style resolution latency $\le 5\text{ ms}$; zero parameter drift across 10,000 simulated turns.

### 5.27 Open Technical Questions
- Dynamic switching of persona profiles when multiple users with divergent preferences are detected simultaneously.

---

## 6. Engine 5: Social Interaction Engine (SIE)

### 6.1 Engine ID and Name
- **Engine ID:** `SIE`
- **Full Name:** Social Interaction Engine
- **Package Location:** `src/eon/engines/sie/`

### 6.2 Mission and Purpose
Coordinate the global social interaction lifecycle across a 12-stage hierarchical state machine, manage multimodal conversational turn-taking (Transition Relevance Places), arbitrate interruptions, and execute conversational repair protocols.

### 6.3 Scope
- 12-Stage Interaction Hierarchical Finite State Machine (HFSM):
  1. `UNAVAILABLE` -> 2. `IDLE_SCANNING` -> 3. `ENCOUNTER_DETECTED` -> 4. `ATTENTION_ENGAGED` -> 5. `APPROACH_GREETING` -> 6. `CONVERSING` -> 7. `TASK_EXECUTION` -> 8. `INTERRUPTED` -> 9. `CONFIRMATION_CHECK` -> 10. `REPAIR` -> 11. `FAREWELL` -> 12. `DISENGAGED`.
- Multimodal Turn-Taking: Evaluates acoustic prosody, Silero VAD silence, and visual gaze to detect turn transition points (TRP) in $<350\text{ ms}$.
- Instant Audio Halt: Emits immediate barge-in audio cut-off when the user interrupts while the robot is speaking.
- Conversational frame and slot tracking.
- Conversational repair protocol (handling misunderstandings, mis-hearings, and ambiguous intents).

### 6.4 Out-of-Scope Responsibilities
- Natural language token generation or vocoding (owned by ERG).
- Physical robot navigation or motor trajectory planning.
- Emotion feature extraction from sensors (owned by ERS / HBU).

### 6.5 Functional Requirements
- `REQ-SIE-001`: Maintain the 12-stage interaction state machine without invalid state transitions.
- `REQ-SIE-002`: Compute multimodal TRP score: take conversational floor when $\text{TRP} > 0.75$ and silence $> 400\text{ ms}$.
- `REQ-SIE-003`: Detect user interruption during robot speech: publish `instant_audio_halt` within $\le 50\text{ ms}$.
- `REQ-SIE-004`: Publish `TurnActionPayload` events coordinating conversational floor transitions.
- `REQ-SIE-005`: Initiate conversational repair sequence when confidence in speech recognition is low ($<0.4$).

### 6.6 Non-Functional Requirements
- Turn transition latency: $\le 350\text{ ms}$ from user silence to floor acquisition.
- Interruption cut-off latency: $\le 50\text{ ms}$.
- State transition determinism: 100% formal HFSM validation.
- Memory: $\le 45\text{ MB}$ heap.

### 6.7 Inputs and Input Schemas
- `ObservationPayload` (`eon.schemas.observations`): Audio VAD, speech text, gaze tracking.
- `InteractionContextPayload` (`eon.schemas.context`).
- `ResponseProposalPayload`: Tracks ongoing robot speech playback status.

### 6.8 Outputs and Output Schemas
- Proposed `TurnActionPayload` (`eon.schemas.interaction`): Command (`take_floor`, `yield_floor`, `instant_audio_halt`), active stage.
- Proposed `SocialCostmapPayload`: Advisory spatial proxemics preferences.

### 6.9 Events Consumed
- `observation.audio.vad` (Topic: `observation.audio.speech_emotion`)
- `observation.visual.gaze` (Topic: `observation.visual.face_mesh`)
- `observation.text.*` (Topic: `observation.text.sentiment`)
- `actuation.playback.status` (Topic: `actuation.speech.status`)

### 6.10 Events Published
- `interaction.turn_action` (Topic: `interaction.turn.action`)
- `context.stage_transition` (Topic: `context.session.update`)
- `social.navigation_advisory` (Topic: `social.nav.costmap`)
- `eon.component_health` (Topic: `health.sie`)

### 6.11 Public Interfaces
```python
class SieEngineInterface(EonEngineInterface):
    async def get_current_stage() -> InteractionStage: ...
    async def handle_barge_in() -> None: ...
    async def evaluate_turn_transition() -> TurnActionPayload: ...
```

### 6.12 Internal Component Boundaries
- `InteractionStateHfsm`: Enforces formal 12-stage state transitions.
- `TrpDetector`: Multimodal transition relevance place scoring engine.
- `BargeInArbitrator`: Real-time interruption detector and speech halt trigger.
- `DialogueFrameTracker`: Tracks active conversation slots and topic frames.
- `RepairProtocolManager`: Sequences clarification requests.

### 6.13 Dependencies
- Internal: `eon.core.event_bus`, `eon.schemas`, `eon.interfaces`.

### 6.14 Forbidden Dependencies
- Prohibited from commanding robot wheel actuators, motors, or speech synthesis audio buffers directly.

### 6.15 Execution Model
- High-priority async event consumer; runs real-time event checks on the event loop.

### 6.16 Lifecycle Requirements
- `initialize()` sets HFSM to `UNAVAILABLE`; `start()` transitions to `IDLE_SCANNING`; `stop()` transitions to `DISENGAGED` within 1.0s.

### 6.17 Failure Modes
- Conflicting sensor signals -> Transitions to `CONFIRMATION_CHECK` stage.
- HFSM deadlock -> Reset to `IDLE_SCANNING` on 10.0s idle timeout.

### 6.18 Timeout and Cancellation Behaviour
- Barge-in check must complete within $\le 20\text{ ms}$.

### 6.19 Degraded Operation
- **Degraded Mode (Audio Only):** Bypasses visual gaze heuristics; calculates TRP using acoustic pitch and silence alone.

### 6.20 Security Requirements
- State transitions strictly validated; prevents injection of unauthorized stage overrides.

### 6.21 Privacy Requirements
- Flushes active dialogue frame buffers upon transition to `DISENGAGED` or `FAREWELL`.

### 6.22 Resource Requirements
- CPU: $\le 8\%$ of 1 core. RAM: $\le 45\text{ MB}$.

### 6.23 Logging and Observability
- Logs all HFSM transitions; metrics: `sie_stage_duration_seconds`, `sie_barge_in_count`, `sie_trp_latency_ms`.

### 6.24 Unit-Test Requirements
- 100% code coverage of the 12-stage HFSM transition matrix; tests verifying barge-in triggers under simulated audio interruptions.

### 6.25 Integration-Test Requirements
- Simulate user speech while ERG is playing audio -> Verify `instant_audio_halt` event published in $\le 50\text{ ms}$ -> Verify ERG stops audio.

### 6.26 Acceptance Criteria
- Interruption cut-off latency $\le 50\text{ ms}$; zero invalid HFSM state transitions.

### 6.27 Open Technical Questions
- Optimal silence threshold calibration for noisy public environments (crowded malls vs. quiet homes).

---

## 7. Engine 6: Emotion Response Generation Engine (ERG)

### 7.1 Engine ID and Name
- **Engine ID:** `ERG`
- **Full Name:** Emotion Response Generation Engine
- **Package Location:** `src/eon/engines/erg/`

### 7.2 Mission and Purpose
Synthesize contextually appropriate, personality-aligned natural language responses, stream expressive neural speech audio via local TTS, and schedule synchronized facial visemes and advisory kinesic gestures.

### 7.3 Scope
- Dual-path response generation:
  - Deterministic safety template library ($<5\text{ ms}$ response for formulaic interactions and fallbacks).
  - Local quantized Small Language Model (Qwen2.5-1.5B via `llama.cpp` using Outlines grammar-constrained decoding).
- Expressive speech synthesis using local Piper TTS (16kHz PCM audio streaming).
- Phoneme-to-viseme mapping for robot head display lip synchronization.
- Advisory kinesic gesture scheduling (head tilt, nod, communicative arm point).
- Strict non-authoritative actuation enforcement (`is_authoritative_stop=False`).

### 7.4 Out-of-Scope Responsibilities
- Direct motor execution or joint PID control (owned by robot host controller).
- Evaluating whether it is the robot's turn to speak (owned by SIE).
- Cognitive empathy strategy selection (owned by ERE).
- Long-term memory indexing (owned by EMS).

### 7.5 Functional Requirements
- `REQ-ERG-001`: Ingest `ResponseIntentPayload`, `PersonaStylePayload`, and turn authorization from SIE.
- `REQ-ERG-002`: Select generation route: execute deterministic template ($<5\text{ ms}$) or invoke local SLM ($<350\text{ ms}$ Time-to-First-Chunk).
- `REQ-ERG-003`: Synthesize streaming 16kHz PCM audio via Piper TTS with RTF $\le 0.10$.
- `REQ-ERG-004`: Emit synchronized viseme events aligned with phoneme audio timestamps.
- `REQ-ERG-005`: Immediately abort audio playback upon receipt of `instant_audio_halt` from SIE within $\le 50\text{ ms}$.
- `REQ-ERG-006`: Guarantee all emitted gesture proposals carry `is_authoritative_stop=False`.

### 7.6 Non-Functional Requirements
- Latency: Template generation $\le 5\text{ ms}$; SLM TTFS $\le 350\text{ ms}$; TTS audio start $\le 80\text{ ms}$.
- Audio Quality: 16 kHz, 16-bit mono PCM, clean synthesis without clicks or buffer underruns.
- Memory: Heap footprint $\le 120\text{ MB}$ (excluding SLM model weights managed by L7).

### 7.7 Inputs and Input Schemas
- `ResponseIntentPayload` (`eon.schemas.intents`).
- `PersonaStylePayload` (`eon.schemas.persona`).
- `TurnActionPayload` (`eon.schemas.interaction`).
- `InteractionContextPayload` (`eon.schemas.context`).

### 7.8 Outputs and Output Schemas
- Proposed `ResponseProposalPayload` (`eon.schemas.responses`): Text, audio chunk stream, visemes, advisory gesture coordinates.
- Proposed `AudioPlaybackChunkPayload`.
- Proposed `KinesicIntentPayload`.

### 7.9 Events Consumed
- `intent.empathy_reasoned` (Topic: `intent.empathy_reasoned`)
- `persona.style_vector` (Topic: `persona.style.vector`)
- `interaction.turn_action` (Topic: `interaction.turn.action`)

### 7.10 Events Published
- `actuation.speech_stream` (Topic: `actuation.speech.stream`)
- `actuation.viseme_marker` (Topic: `actuation.screen.viseme`)
- `actuation.expressive_gesture` (Topic: `actuation.kinesics.advisory`)
- `eon.component_health` (Topic: `health.erg`)

### 7.11 Public Interfaces
```python
class ErgEngineInterface(EonEngineInterface):
    async def generate_response(
        intent: ResponseIntentPayload, style: PersonaStylePayload
    ) -> ResponseProposalPayload: ...
    async def abort_playback() -> None: ...
```

### 7.12 Internal Component Boundaries
- `ResponsePlanner`: Decides between template fallback and SLM generation.
- `DeterministicTemplateEngine`: Instant retrieval of verified conversational responses.
- `SlmDialogueGenerator`: Interfaces with L7 `llama.cpp` using Outlines JSON schema constraints.
- `PiperTtsStreamer`: Streams synthesized audio chunks from L7 Piper vocoder.
- `VisemeGestureScheduler`: Computes synchronized mouth visemes and head tilt coordinates.

### 7.13 Dependencies
- Internal: `eon.core.event_bus`, `eon.schemas`, `eon.interfaces`.
- Adapters (L7): `LlmAdapterInterface`, `TtsAdapterInterface`, `DeterministicRuleAdapter`.

### 7.14 Forbidden Dependencies
- Prohibited from sending raw CAN or serial motor packets to robot hardware.
- Prohibited from calling external cloud LLM APIs (OpenAI, Anthropic) in standard offline execution.

### 7.15 Execution Model
- Async streaming pipeline; token generation and audio synthesis execute in separate worker threads managed by L7.

### 7.16 Lifecycle Requirements
- `initialize()` loads templates and tests adapter connections; `start()` readies generation queues; `stop()` halts audio streams within 1.0s.

### 7.17 Failure Modes
- SLM generation timeout ($>500\text{ ms}$) -> Instant fallback to deterministic safety template.
- TTS vocoder failure -> Fall back to pre-recorded wav chime and screen text display.

### 7.18 Timeout and Cancellation Behaviour
- Total generation budget: $\le 600\text{ ms}$. If exceeded, template fallback dispatches immediately.

### 7.19 Degraded Operation
- **Degraded Mode (No SLM):** Operates entirely using deterministic templates; zero neural SLM execution; memory footprint drops by 1.2 GB.

### 7.20 Security Requirements
- Grammar-constrained decoding prevents prompt injection; regex output filters scrub prohibited phrases.

### 7.21 Privacy Requirements
- Generates speech without logging user transcripts to disk.

### 7.22 Resource Requirements
- CPU: $\le 30\%$ of 4 cores during active token generation; idle $\le 2\%$. RAM: $\le 120\text{ MB}$ engine heap.

### 7.23 Logging and Observability
- Logs generation latency metrics; metrics: `erg_ttfs_ms`, `erg_tts_rtf`, `erg_template_fallback_count`.

### 7.24 Unit-Test Requirements
- Unit tests for template selector; tests verifying instantaneous response abort on `instant_audio_halt`; tests for non-authoritative flag verification.

### 7.25 Integration-Test Requirements
- End-to-end test: Intent received -> Response generated -> Audio streamed -> Visemes emitted -> Playback completes.

### 7.26 Acceptance Criteria
- Deterministic template latency $\le 5\text{ ms}$; SLM TTFS $\le 350\text{ ms}$; barge-in halt executed in $\le 50\text{ ms}$.

### 7.27 Open Technical Questions
- Evaluation of voice prosody conditioning based on real-time continuous valence/arousal vectors.

---

## 8. Engine 7: Human Behaviour Understanding Engine (HBU)

### 8.1 Engine ID and Name
- **Engine ID:** `HBU`
- **Full Name:** Human Behaviour Understanding Engine
- **Package Location:** `src/eon/engines/hbu/`

### 8.2 Mission and Purpose
Interpret observable physical human behavior, 3D body pose, communicative hand gestures, and spatial proxemics to provide non-verbal context for social interaction, without psychological diagnosis or sensitive-trait inference.

### 8.3 Scope
- 3D skeletal posture tracking (MediaPipe Pose 33 landmarks with ego-motion subtraction).
- Spatial proxemics estimation (Hall's distance zones: Intimate, Personal, Social, Public).
- Communicative gesture classification (pointing deictics, wave greeting, hand open/halt, head nod/shake).
- Physical action classification via ST-GCN (walking forward, reaching, standing idle, carrying object).
- Calibrated confidence and non-inferential behavioral description.

### 8.4 Out-of-Scope Responsibilities
- Facial emotion recognition or Action Unit analysis (owned by ERS).
- Inferring personality traits, psychological diagnosis, or sensitive demographic attributes.
- Direct motor obstacle avoidance (owned by robot base safety controller).

### 8.5 Functional Requirements
- `REQ-HBU-001`: Ingest 3D pose landmarks and robot odometry; subtract robot driving motion.
- `REQ-HBU-002`: Classify spatial proxemic zone relative to the robot base ($<0.45\text{m}$, $0.45\text{--}1.2\text{m}$, $1.2\text{--}3.6\text{m}$, $>3.6\text{m}$).
- `REQ-HBU-003`: Identify communicative hand gestures (pointing direction 3D vector, wave greeting) with confidence $\ge 0.70$.
- `REQ-HBU-004`: Publish behavioral observation payloads within $\le 20\text{ ms}$ of frame receipt.
- `REQ-HBU-005`: Explicitly prohibit sensitive-trait profiling: output purely kinematic and spatial descriptions.

### 8.6 Non-Functional Requirements
- Latency: p95 processing latency $\le 20\text{ ms}$ on edge CPU.
- Tracking consistency: Sustained spatial tracking up to $5.0\text{ m}$ distance.
- Memory: $\le 55\text{ MB}$ heap.

### 8.7 Inputs and Input Schemas
- `ObservationPayload` (`eon.schemas.observations`): Modality `BEHAVIOURAL`.
- `BehaviourObservationData`: Joint coordinates, action label, confidence.
- `OdometryState` from L2.

### 8.8 Outputs and Output Schemas
- `ObservationPayload` (`eon.schemas.observations`): Modality `BEHAVIOURAL` with enriched spatial proxemics and gesture targets.

### 8.9 Events Consumed
- `observation.pose.raw` (Topic: `observation.pose.raw`)
- `robot.odometry` (Topic: `robot.telemetry.odometry`)

### 8.10 Events Published
- `eon.observation` (Topic: `observation.behaviour.fused`)
- `eon.component_health` (Topic: `health.hbu`)

### 8.11 Public Interfaces
```python
class HbuEngineInterface(EonEngineInterface):
    async def process_skeletal_landmarks(
        landmarks: np.ndarray, odom: OdometryState
    ) -> BehaviourObservationData: ...
    async def get_proxemic_zone(distance_meters: float) -> ProxemicZone: ...
```

### 8.12 Internal Component Boundaries
- `EgoMotionCompensator`: Cancels robot wheel velocities from human joint trajectories.
- `ProxemicsEstimator`: Calculates 3D distance and social spatial zones.
- `GestureClassifier`: Identifies discrete communicative hand and arm gestures.
- `ActionSequenceClassifier`: Lightweight ST-GCN classifying temporal activities.

### 8.13 Dependencies
- Internal: `eon.core.event_bus`, `eon.schemas`, `eon.interfaces`.
- Adapters (L7): `OnnxInferenceAdapter` (for ST-GCN).

### 8.14 Forbidden Dependencies
- Prohibited from importing biometric face recognition models or identity databases.
- Prohibited from emitting authoritative motion halt commands to robot wheels.

### 8.15 Execution Model
- Async subscriber on Core Event Bus; tensor operations executed in L7 ONNX threadpool.

### 8.16 Lifecycle Requirements
- `initialize()` loads ST-GCN weights; `start()` begins tracking loop; `stop()` halts workers within 1.5s.

### 8.17 Failure Modes
- Severe skeletal occlusion -> Emits `QualityStatus.DEGRADED` with lowered confidence; preserves last known position.

### 8.18 Timeout and Cancellation Behaviour
- Processing deadline: $25\text{ ms}$. If exceeded, drops frame and returns previous state.

### 8.19 Degraded Operation
- **Degraded Mode (No Skeletal Mesh):** Evaluates bounding box centroids from camera detector alone.

### 8.20 Security Requirements
- Schema validation on all telemetry inputs; rejection of invalid coordinate arrays.

### 2.21 Privacy Requirements
- Non-Inferential Guarantee: Strictly prohibited from inferring medical conditions, gait disorders, or sensitive personal attributes.

### 2.22 Resource Requirements
- CPU: $\le 15\%$ of 1 core. RAM: $\le 55\text{ MB}$.

### 2.23 Logging and Observability
- Logs classified gestures; metrics: `hbu_latency_ms`, `hbu_tracking_distance_m`.

### 2.24 Unit-Test Requirements
- Unit tests for ego-motion subtraction mathematics; tests verifying proxemic zone boundaries; tests for gesture classifier.

### 2.25 Integration-Test Requirements
- Ingest skeletal landmarks -> HBU processes gesture -> Emits `observation.behaviour.fused` -> SIE transitions to `ATTENTION_ENGAGED`.

### 2.26 Acceptance Criteria
- Processing latency $\le 20\text{ ms}$; gesture classification accuracy $\ge 85\%$ on test benchmark.

### 2.27 Open Technical Questions
- Compensation for extreme robot chassis tilting when traversing uneven flooring or ramps.
