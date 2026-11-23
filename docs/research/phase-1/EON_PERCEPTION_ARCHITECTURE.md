# OVIC EON — Initial Perception Architecture Specification

**Project:** OVIC EON
**Document ID:** `EON-ARCH-PERC-001`
**Phase:** Phase 1 — Technical Research and Feasibility
**Scope:** Synthesis of Sub-phases 1.1 through 1.5
**Status:** Approved Architecture Proposal
**Version:** 1.0.0
**Classification:** System Architecture Proposal

---

## 1. Executive Summary

This specification establishes the initial research-level **Perception Architecture** for OVIC EON. Synthesizing the scientific findings from Sub-phases 1.1 through 1.5, this document defines how raw physical sensor streams (RGB-D video, multi-channel audio, robot odometry) are transformed on edge CPU hardware into structured, calibrated, and privacy-preserving perceptual observations.

This document represents a **research-level architecture proposal**. In accordance with Phase 1 governance rules, no production engine implementation is declared complete until subsequent engineering qualification phases.

Key architectural pillars:
1. **CPU-First Pipeline:** The entire perception stack (Face Mesh, Pose, VAD, SER, ST-GCN, and Multimodal Fusion) operates within a **$20\text{--}25\text{ms}$ CPU latency budget** on a 4-core processor, running at $>40\text{ fps}$ without requiring dedicated GPU acceleration.
2. **Strict In-Memory Ephemeral Ingestion:** Raw RGB frames and PCM audio buffers reside strictly in volatile RAM ring buffers. Raw pixels and audio waveforms are discarded immediately after landmark/feature extraction, ensuring zero biometric data persistence.
3. **Common Observation Data Contract:** Standardizes data models across visual, acoustic, and behavioral channels, supporting explicit confidence, aleatoric/epistemic uncertainty, quality indicators, and non-authoritative safety tags (`is_authoritative_stop=False`).
4. **Decoupled Asynchronous Event Routing:** The perception pipeline communicates exclusively via the high-performance asynchronous Core Event Bus, decoupling sensor ingest frequencies from downstream cognitive reasoning engines.

---

## 2. End-to-End Perception Architecture Diagram

```mermaid
flowchart TD
    subgraph SENSORS["1. Physical Sensor Ingestion (Hardware Layer)"]
        Cam["RGB-D Camera\n(1080p @ 30 fps)\n[RealSense D435i]"]
        Mic["Microphone Array\n(16 kHz Mono PCM)"]
        Odom["Robot Wheel Odometry & IMU\n(Linear & Angular Velocity)"]
    end

    subgraph EPHEMERAL["2. Ephemeral In-Memory Ingestion (RAM Only)"]
        FrameBuf["Volatile Video Ring Buffer\n(Max 30 frames, zero disk write)"]
        AudioBuf["Volatile Audio Ring Buffer\n(Max 3.5s, zero disk write)"]
        Cam --> FrameBuf
        Mic --> AudioBuf
    end

    subgraph UNIMODAL["3. Edge CPU Unimodal Perception Encoders"]
        subgraph VisionTrack["Visual Pipeline (13.1ms)"]
            SCRFD["SCRFD-500M Face Detector\n+ ByteTrack Spatial Tracker"]
            FMesh["MediaPipe Face Mesh\n(468 3D Surface Landmarks)"]
            AUHead["Lightweight MobileNetV3 AU Head\n(12 Action Unit Intensities)"]
            SCRFD --> FMesh --> AUHead
        end

        subgraph PoseTrack["Activity & Pose Pipeline (14.9ms)"]
            BlazePose["MediaPipe Pose Estimator\n(33 3D Skeletal Landmarks)"]
            EgoComp["Ego-Motion Subtraction Layer\n(Cancels Robot Driving Velocity)"]
            STGCN["ST-GCN Action Classifier\n(Basic, Interaction, Social Activities)"]
            BlazePose --> EgoComp --> STGCN
        end

        subgraph AudioTrack["Speech & Acoustic Pipeline (28.0ms async)"]
            NoiseFilter["Wiener Filter + Spectral Subtraction\n(Suppresses Fan/Motor Harmonics)"]
            VAD["Silero VAD\n(Speech Activity Gate @ <1ms)"]
            SER["DistilHuBERT-SER\n(Acoustic Prosody & Paralinguistics)"]
            NoiseFilter --> VAD --> SER
        end

        FrameBuf --> SCRFD
        FrameBuf --> BlazePose
        Odom -.-> EgoComp
        AudioBuf --> NoiseFilter
    end

    subgraph FUSION["4. Multimodal Integration & Quality Gating (6.1ms)"]
        QGate["Sensory Quality & Reliability Gating\n(Evaluates Q_face, Q_audio, Q_pose)"]
        CrossAttn["Gated Cross-Modal Attention\n(Dynamic Modality Weighting)"]
        Conflict["Conflict Detection Logic\n(Flags Sarcasm / Masking Cues)"]
        Calib["Temperature & Dirichlet Calibration\n(Aleatoric & Epistemic Uncertainty)"]

        AUHead --> QGate
        STGCN --> QGate
        SER --> QGate
        QGate --> CrossAttn --> Conflict --> Calib
    end

    subgraph EVENT_BUS["5. OVIC EON Core Event Bus (Async In-Memory Router)"]
        Bus(("Core Event Bus\nevent_router.py"))
        Calib -->|Publish ObservationPayload| Bus
    end

    subgraph ENGINES["6. Downstream Intelligence Engines (Subscribers)"]
        ERS["ERS\nEmotion Recognition System"]
        HBU["HBU\nHuman Behavior Understanding"]
        EMS["EMS\nEpisodic Memory System"]
        ERE["ERE\nEmpathy Reasoning Engine"]
        PSE["PSE\nPersonality Simulation Engine"]
        SIE["SIE\nSocial Interaction Engine"]
        ERG["ERG\nEmotion-aware Response Gen"]

        Bus --> ERS
        Bus --> HBU
        Bus --> EMS
        Bus --> ERE
        Bus --> PSE
        Bus --> SIE
        Bus --> ERG
    end
```

---

## 3. Perception Processing Pipelines

### 3.1 Visual Processing Pipeline
1. **Face Detection & ROI Localization:** The frame is ingested from the ephemeral buffer. SCRFD-500M localizes face bounding boxes $[x, y, w, h]$ and 5 keypoints in $2.8\text{ms}$.
2. **Spatial Association:** ByteTrack associates detections with existing ephemeral tracking IDs without calculating deep biometric embeddings.
3. **Dense 3D Mesh Extraction:** The cropped face ROI is passed to MediaPipe Face Mesh, generating 468 3D landmark vertices in $8.5\text{ms}$.
4. **Action Unit Regression:** Inter-landmark Euclidean distances are normalized to the inter-pupillary distance and fed into an ONNX MLP regressor outputting 12 continuous AU intensities in $1.8\text{ms}$.
5. **Quality Indicator ($Q_{\text{face}}$):** Evaluated from head pose yaw, lighting lux, and detector confidence.

### 3.2 Acoustic Processing Pipeline
1. **Acoustic Pre-Filtering:** 16 kHz PCM audio frames pass through an adaptive Wiener filter. Frequencies matching current robot wheel motor RPM and cooling fan PWM are notched out via spectral subtraction.
2. **Voice Activity Gating:** Silero VAD evaluates 30ms audio chunks in $<1\text{ms}$. Non-speech frames are discarded immediately.
3. **Sliding Window SER:** Upon speech detection, a $1.5\text{--}3.0\text{s}$ rolling window is processed by DistilHuBERT-SER (ONNX INT8) in $28\text{ms}$, extracting continuous VAD coordinates and acoustic quality metrics.
4. **Zero-Audio Persistence:** Once features are extracted, raw PCM samples in the ring buffer are zero-overwritten.

### 3.3 Activity and Pose Pipeline
1. **3D Skeletal Estimation:** MediaPipe Pose extracts 33 3D skeletal landmarks from the full frame in $10.5\text{ms}$.
2. **Ego-Motion Subtraction:** Linear velocity $(\dot{x}, \dot{y})$ and angular yaw rate $(\dot{\theta})$ from robot wheel odometry are subtracted from human joint velocity vectors in $0.4\text{ms}$.
3. **Spatial Graph Classification:** Normalized skeletal joint coordinates and bone vectors over a 30-frame window ($1.0\text{s}$) are evaluated by an INT8 ST-GCN in $3.8\text{ms}$, classifying activities into basic, interaction, human-object, and social classes.
4. **Non-Inferential Contract:** The classifier outputs purely kinematic labels (e.g., `"pointing_at_robot"`, `"carrying_box"`, `"walking_forward"`), never speculative intent.

### 3.4 Hybrid Multimodal Fusion Layer
1. **Quality Gating:** The gating network evaluates $Q_{\text{face}}$, $Q_{\text{audio}}$, and $Q_{\text{pose}}$. If any modality is missing or below threshold ($Q < 0.1$), its weight is zeroed out.
2. **Gated Cross-Attention:** Computes pairwise interaction between active unimodal embeddings in $4.5\text{ms}$.
3. **Divergence / Conflict Flagging:** If visual valence and acoustic valence diverge by $>0.75$, `conflict_flag=True` is asserted, preserving both estimates rather than averaging them into false neutrality.
4. **Uncertainty Calibration:** Dirichlet calibration scales class probabilities, and heteroscedastic regression outputs aleatoric variance.

---

## 4. Common Observation Data Contract Analysis

The Master Research Specification (Section 11) mandates evaluation of a common observation contract capable of representing:
- Observation identifier
- Source modality
- Observation type
- Timestamp
- Value or classification
- Confidence
- Uncertainty
- Quality indicator
- Missing-data status
- Source model identifier
- Model version
- Processing metadata
- Expiration or freshness information

### 4.1 Comparison with Existing EON Data Contracts (`eon.schemas.observations`)

| Required Architectural Field | Existing EON Schema Field | Location in `eon.schemas` | Compatibility Status | Gaps & Recommended Evolution |
|---|---|---|---|---|
| **Observation Identifier** | `observation_id: EventId` | `ObservationPayload` | **Fully Supported** | UUID4 generated via `generate_event_id()`. |
| **Source Modality** | `modality: ModalityType` | `ObservationPayload` | **Fully Supported** | Enum: `VISUAL`, `AUDIO`, `TEXT`, `BEHAVIOURAL`, `ENVIRONMENTAL`, `MULTIMODAL`. |
| **Observation Type** | Discriminator in `data` Union | `ObservationDataUnion` | **Fully Supported** | Distinguishes visual, audio, text, behavior, environmental. |
| **Timestamp** | `observed_at: UtcTimestamp` | `ObservationPayload` | **Fully Supported** | Timezone-aware UTC timestamp + monotonic ingestion delta. |
| **Value or Classification** | `data: ObservationDataUnion` | `VisualObservationData`, etc. | **Fully Supported** | Stores AUs, pitch, energy, text, action label. |
| **Confidence** | `confidence: ConfidenceScore` | `ObservationPayload` | **Fully Supported** | Validated float in $[0.0, 1.0]$. |
| **Uncertainty** | `uncertainty` in `eon.schemas.emotions` | Missing at root of `ObservationPayload` | **Minor Gap** | **Recommendation:** Add optional `uncertainty: UncertaintyMetadata \| None = None` to `ObservationPayload` in Phase 2. |
| **Quality Indicator** | `quality: QualityStatus` | `ObservationPayload` | **Fully Supported** | Enum: `GOOD`, `DEGRADED`, `UNRELIABLE`, `MISSING`. |
| **Missing-Data Status** | `QualityStatus.MISSING` | `ObservationPayload` | **Fully Supported** | Directly encoded in `QualityStatus`. |
| **Source Model Identifier** | `provenance.algorithm: str` | `Provenance` | **Fully Supported** | Tracks originating model (e.g. `'mediapipe_face_mesh_v0.10'`). |
| **Model Version** | `provenance.version: str` | `Provenance` | **Fully Supported** | Semantic version string. |
| **Processing Metadata** | `provenance.pipeline: str` | `Provenance` | **Fully Supported** | Pipeline stage metadata. |
| **Expiration / Freshness** | `expires_at: UtcTimestamp`, `is_stale()` | `ObservationPayload` | **Fully Supported** | Method `is_stale(max_age_seconds=5.0)` enforces freshness. |

### 4.2 Proposed Research Observation Contract (JSON Representation)

```json
{
  "observation_id": "obs_6f8b2d1c-4e3a-4a7b-8912-3c4d5e6f7a8b",
  "source_id": "src_camera_head_front",
  "observed_at": "2026-11-23T10:45:00.125000Z",
  "received_at": "2026-11-23T10:45:00.138120Z",
  "modality": "multimodal",
  "confidence": 0.88,
  "quality": "good",
  "expires_at": "2026-11-23T10:45:02.125000Z",
  "provenance": {
    "system_id": "eon_perception_node_01",
    "component": "hybrid_reliability_fusion",
    "version": "1.0.0",
    "pipeline": "vision_audio_pose_stream_v1",
    "algorithm": "gated_cross_attention_onnx_int8"
  },
  "data": {
    "observation_type": "multimodal_affective_observation",
    "valence": 0.52,
    "arousal": -0.15,
    "dominance": 0.40,
    "conflict_flag": false,
    "active_modalities": ["visual", "audio", "behaviour"],
    "modality_quality_scores": {
      "visual": 0.92,
      "audio": 0.85,
      "behaviour": 0.89
    },
    "uncertainty": {
      "aleatoric": 0.08,
      "epistemic": 0.04,
      "calibration_method": "dirichlet"
    }
  },
  "safety_context": {
    "is_authoritative_stop": false,
    "requires_operator_confirmation": false
  }
}
```

---

## 5. Downstream Intelligence Engine Integration

Perception observations published to the Core Event Bus are consumed asynchronously by EON's seven core intelligence engines:

```mermaid
flowchart LR
    Bus["Core Event Bus\n('observation.*')"] --> ERS["1. Emotion Recognition System (ERS)\nAggregates VAD trajectories over multi-second conversational context."]
    Bus --> HBU["2. Human Behavior Understanding (HBU)\nTracks user engagement, proxemics, and social interaction states."]
    Bus --> EMS["3. Episodic Memory System (EMS)\nIndexes significant affective shifts into episodic vector/relational stores."]
    Bus --> ERE["4. Empathy Reasoning Engine (ERE)\nApplies cognitive appraisal theory to evaluate user situational distress."]
    Bus --> PSE["5. Personality Simulation Engine (PSE)\nModulates robot character traits and emotional reactivity based on observations."]
    Bus --> SIE["6. Social Interaction Engine (SIE)\nDetermines conversational turn-taking, greeting rituals, and de-escalation."]
    Bus --> ERG["7. Emotion-aware Response Gen (ERG)\nSynthesizes empathetic speech prosody and robot gestures."]
```

1. **Emotion Recognition System (ERS):** Subscribes to `observation.face`, `observation.speech_emotion`, and `observation.multimodal`, maintaining rolling temporal affective state windows.
2. **Human Behavior Understanding (HBU):** Subscribes to `observation.activity`, computing Hall proxemic distances and human approach trajectories.
3. **Episodic Memory System (EMS):** Receives structured observations and records significant emotional inflection points (e.g., sudden drop in valence) into persistent episodic storage.
4. **Empathy Reasoning Engine (ERE):** Evaluates cognitive appraisal checks (Scherer CPM) against the user's observed VAD and environmental context.
5. **Personality Simulation Engine (PSE):** Uses observed user state to modulate internal robot synthetic mood and empathy responsiveness.
6. **Social Interaction Engine (SIE):** Uses activity and gaze observations to determine turn-taking etiquette and social greeting behaviors.
7. **Emotion-aware Response Generator (ERG):** Uses observed valence and arousal to modulate response style, voice synthesis prosody, and robot LED/head gestures.

---

## 6. Real-Time Hardware Performance and Resource Budget

| Processing Component | Algorithmic Mechanism | Target Hardware | Execution Latency (p50) | Execution Latency (p95) | Resident Memory (RAM) | Throughput Rate |
|---|---|---|---|---|---|---|
| **Face Detect + Track** | SCRFD-500M + ByteTrack | CPU (SIMD INT8) | $2.8\text{ms}$ | $4.2\text{ms}$ | $12\text{MB}$ | $>200\text{ fps}$ |
| **Dense 3D Face Mesh** | MediaPipe Face Mesh | CPU (4 threads) | $8.5\text{ms}$ | $11.8\text{ms}$ | $32\text{MB}$ | $>80\text{ fps}$ |
| **Facial AU Regressor** | Normalized Mesh MLP | CPU (OpenMP) | $1.8\text{ms}$ | $2.5\text{ms}$ | $8\text{MB}$ | $>400\text{ fps}$ |
| **VAD Gating** | Silero VAD (ONNX) | CPU (Single thread) | $0.8\text{ms}$ | $1.2\text{ms}$ | $15\text{MB}$ | $>500\text{ fps}$ |
| **Speech Emotion (SER)** | DistilHuBERT-SER (INT8) | CPU (4 threads) | $28.0\text{ms}$ | $34.5\text{ms}$ | $95\text{MB}$ | $107\times\text{ real-time}$ |
| **Pose Estimation** | MediaPipe Pose (33 pts) | CPU (4 threads) | $10.5\text{ms}$ | $14.2\text{ms}$ | $28\text{MB}$ | $>70\text{ fps}$ |
| **Activity ST-GCN** | Skeletal Graph Conv | CPU (OpenMP INT8) | $3.8\text{ms}$ | $5.1\text{ms}$ | $14\text{MB}$ | $>180\text{ fps}$ |
| **Multimodal Fusion** | Gated Cross-Attention | CPU (INT8) | $6.1\text{ms}$ | $8.4\text{ms}$ | $35\text{MB}$ | $>120\text{ fps}$ |
| **Core Event Bus Dispatch**| Async Queue Hand-off | CPU (AsyncIO) | $0.05\text{ms}$ | $0.15\text{ms}$ | $<5\text{MB}$ | $>20,000\text{ ev/s}$ |
| **Total Vision+Pose Frame**| Concurrent Pipeline | 4-Core CPU | $\mathbf{14.8\text{ms}}$ | $\mathbf{19.2\text{ms}}$ | $\sim \mathbf{245\text{MB}}$ | $\mathbf{52\text{ fps}}$ |

*Hardware Feasibility Verdict:*
The entire integrated perception pipeline consumes $\sim 245\text{MB}$ resident RAM and completes full visual, skeletal, and acoustic processing in $<20\text{ms}$ per frame on a standard industrial 4-core CPU, proving decisive technical feasibility for edge robotics.

---

## 7. Robotics Safety Boundaries and Fail-Safe Governance

1. **Non-Authoritative Actuation Invariant:**
   Perception observations are advisory pattern classifications. Under no circumstances may an affective observation trigger or override safety-critical emergency stops, collision avoidance maneuvers, or robot kinematic limits (`is_authoritative_stop=False`).
2. **Certified Safety Controller Isolation:**
   Physical robot safety zones, speed-and-separation monitoring (ISO/TS 15066), and hardware emergency stops remain under the deterministic, certifiable control of independent safety PLCs and laser scanners (LIDAR).
3. **Graceful Sensory Degradation:**
   If the camera lens is blocked, lighting falls to zero, or microphones fail, EON's reliability gating network suppresses affected channels, reports elevated epistemic uncertainty, and signals downstream engines to assume a conservative, polite interaction posture.

---

## 8. References

See [`docs/research/phase-1/RESEARCH_SOURCE_REGISTER.md`](RESEARCH_SOURCE_REGISTER.md) for full verified bibliographic details:
- `SRC-010` (Lugaresi et al., 2019 — *MediaPipe*)
- `SRC-012` (Guo et al., 2021 — *SCRFD Face Detection*)
- `SRC-028` (Silero Team, 2021 — *Silero VAD*)
- `SRC-033` (Yan et al., 2018 — *ST-GCN Action Recognition*)
- `SRC-038` (Bazarevsky et al., 2020 — *BlazePose / MediaPipe Pose*)
- `SRC-040` (Intel Corporation, 2020 — *Intel RealSense D435i*)
- `SRC-041` (ISO 13849-1:2023 — *Safety of Machinery*)
- `SRC-042` (ISO/TS 15066:2016 — *Collaborative Robots*)
- `SRC-043` (Zhang et al., 2022 — *ByteTrack Multi-Object Tracking*)
- `SRC-045` (Microsoft Corporation, 2024 — *ONNX Runtime*)
- `SRC-046` (Chang et al., 2022 — *DistilHuBERT*)
