# OVIC EON — Phase 1 Technical Comparison Matrix

**Project:** OVIC EON
**Document ID:** `EON-RES-TCM-001`
**Phase:** Phase 1 — Technical Research and Feasibility
**Scope:** Sub-phases 1.1 through 1.11
**Status:** Approved
**Version:** 1.1.0
**Classification:** Technical Architecture Specification

---

## 1. Overview and Evaluation Framework

This document provides a rigorous, multi-dimensional comparison of machine learning architectures, statistical methods, and sensor processing pipelines evaluated across Sub-phases 1.1 through 1.5.

In accordance with EON's Core Engineering Principles:
1. **CPU-First Execution:** Baseline capability must operate on standard industrial/embedded x86-64 or ARM CPUs without mandatory GPU hardware.
2. **Deterministic Fallbacks:** Probabilistic neural inferences must degrade gracefully to rule-based or low-dimensional statistical baselines under computational distress.
3. **Commercial Feasibility:** Model weights, architectures, and evaluation datasets must be legally viable for commercial deployment or provide clear enterprise licensing pathways.

Each candidate approach is assessed against eight standardized technical dimensions:
- **CPU Suitability:** Latency, thread scalability, and memory footprint on modern multi-core CPUs (e.g., 4-core Intel Core i5 / ARM Cortex-A76).
- **Optional Acceleration:** Scalability to TensorRT (NVIDIA GPU), OpenVINO (Intel iGPU/NPU), or ONNX Runtime DirectML/NNAPI.
- **Model Complexity:** Parameter count, floating-point operations (FLOPs), and cache requirements.
- **Data Requirements:** Training volume, annotation difficulty, and cross-cultural generalization.
- **Deployment Complexity:** Runtime library footprint, system dependencies, and cold-start latency.
- **Key Limitations:** Inherent failure modes, physical vulnerabilities, and edge cases.
- **Licensing Classification:** Permissive Open Source (MIT/Apache 2.0/BSD), Copyleft (GPL/LGPL), Academic Non-Commercial, or Proprietary.
- **EON Recommendation:** Proposed role in EON perception architecture (`RECOMMENDED`, `EXPERIMENTAL`, `OPTIONAL_ACCELERATED`, or `UNSUITABLE`).

---

## 2. Sub-phase 1.1 — Emotion Recognition Representations and Methods

| Architecture / Method | Representation Model | CPU Suitability (Single / 4-Core) | Optional Acceleration | Model Complexity | Data Requirements | Deployment Complexity | Key Scientific & Engineering Limitations | Licensing Classification | EON Recommendation |
|---|---|---|---|---|---|---|---|---|---|
| **Ekman Discrete Classifier (CNN / MLP)** | Categorical (6/7 discrete classes) | **High** ($<5\text{ms}$ on CPU) | OpenVINO, TensorRT | Small ($<5\text{M}$ params) | Moderate (Labeled face/speech datasets) | Low (Standalone ONNX runtime) | Masks blended emotions; oversimplifies complex social states; assumes universality (Barrett et al., 2019). | Permissive (Code: MIT/Apache; Datasets: Non-commercial) | **RECOMMENDED** (as discrete interpretation layer) |
| **Russell Continuous VAD Regressor** | Dimensional ($V, A, D \in [-1, 1]$) | **High** ($<8\text{ms}$ on CPU) | OpenVINO, TensorRT | Small to Moderate ($2\text{M}\text{--}10\text{M}$ params) | High (Requires continuous annotator agreement) | Low (Single regression head) | Less intuitive for downstream rule generation; annotator variance on valence vs arousal. | Permissive (Code: MIT/Apache) | **RECOMMENDED** (as core internal continuous representation) |
| **Appraisal-Based Evaluator (Scherer CPM)** | Cognitive Appraisals (Novelty, Goal, Coping) | **High** ($<2\text{ms}$ rule / bayesian) | Not needed (CPU logic) | Very Low (Deterministic / Bayesian graph) | Domain Knowledge + Event Logs | Low (Pure Python / C++ logic) | Difficult to train end-to-end from raw sensor signals; requires structured conversational context. | Permissive (Algorithmic implementation) | **RECOMMENDED** (in downstream ERE / PSE reasoning engines) |
| **Compound Emotion Classifier (Du et al.)** | Categorical Compound (e.g., Happily Surprised) | **Medium** ($10\text{--}15\text{ms}$ on CPU) | OpenVINO | Moderate ($15\text{M}\text{--}25\text{M}$ params) | Very High (Sparse real-world labels) | Medium | Severe class imbalance in real-world human-robot interaction. | Permissive Code / Non-commercial academic data | **EXPERIMENTAL** (defer to Phase 2) |
| **Generative LLM Emotion Prompting** | Unstructured Text / Chain-of-Thought | **Unsuitable on Edge CPU** ($>1500\text{ms}$) | Requires large GPU (CUDA) | Massive ($7\text{B}\text{--}70\text{B}$ params) | Massive pretraining corpora | High (vLLM / Ollama runtime overhead) | Non-deterministic; high latency; violates offline edge-first CPU mandate for perception. | Mixed (Llama Community / Apache) | **UNSUITABLE** (for real-time perception pipeline) |

---

## 3. Sub-phase 1.2 — Facial Expression and Action Unit Analysis

| Technology / Candidate Pipeline | Primary Output | CPU Latency (4-Core x86 / ARM) | Memory Footprint (RAM) | Landmark / Feature Resolution | Robustness to Head Pose ($\pm 45^\circ$) | Robustness to Illumination / Masks | Commercial Licensing Status | EON Recommendation |
|---|---|---|---|---|---|---|---|---|
| **SCRFD-500M + MediaPipe Face Mesh** | 468 3D Landmarks + Iris coordinates | **$8\text{--}14\text{ms}$** ($>60\text{ fps}$) | $\sim 45\text{ MB}$ | High (468 dense 3D points) | Moderate to High (Maintains mesh up to $45^\circ$) | Moderate (Degrades under severe backlight or full mask) | **Apache 2.0** (Google MediaPipe) / **MIT** (SCRFD) | **RECOMMENDED** (Primary visual landmark pipeline) |
| **Dlib 68-Point Facial Landmark Detector** | 68 2D Facial Landmarks | **$25\text{--}40\text{ms}$** ($25\text{ fps}$) | $\sim 100\text{ MB}$ | Low (68 sparse 2D points) | Poor (Fails past $30^\circ$ yaw/pitch) | Poor (Severe failure with partial facial occlusion) | **Boost Software License 1.0** | **UNSUITABLE** (Superseded by modern dense 3D meshes) |
| **RetinaFace (ResNet-50 backbone)** | Face BBoxes + 5 Landmarks | **$65\text{--}90\text{ms}$** ($12\text{ fps}$) | $\sim 180\text{ MB}$ | Very Low (5 points) | Very High ($>60^\circ$ extreme angles) | High | **MIT License** (InsightFace) | **OPTIONAL_ACCELERATED** (When GPU available or crowded scenes) |
| **OpenFace 2.0 (AU Recognition)** | 18 Action Units (Presence & Intensity) | **$35\text{--}55\text{ms}$** ($18\text{ fps}$) | $\sim 250\text{ MB}$ | 68 Points + HOG + AUs | Moderate | Moderate | **Non-Commercial Academic Only** (OpenFace license restrictions) | **UNSUITABLE FOR COMMERCIAL EON** (Must re-implement AU head) |
| **Lightweight MobileNetV3-AU Regressor** | 12 Essential AUs (Intensity $\in [0, 1]$) | **$6\text{--}10\text{ms}$** ($>100\text{ fps}$) | $\sim 20\text{ MB}$ | Input: 468 mesh landmarks or cropped face | High (Normalized landmark input invariant to pose) | High (Operates on geometric mesh distances) | **Apache 2.0 / MIT** (Trained on internal/permissive data) | **RECOMMENDED** (Clean-room AU extraction on top of MediaPipe) |

---

## 4. Sub-phase 1.3 — Speech Emotion Recognition (SER) Architectures

| Architecture / Framework | Feature Representation | CPU Inference Latency (3s audio window) | Model Parameter Count | Multilingual Capability | Robot Acoustic Noise Robustness | Audio Privacy Guarantees | Licensing Classification | EON Recommendation |
|---|---|---|---|---|---|---|---|---|
| **openSMILE eGeMAPS + LightGBM / MLP** | 88 Statistical Acoustic Parameters | **$<5\text{ms}$** ($>200\text{x}$ real-time) | $<1\text{M}$ params | High (Language-agnostic acoustic prosody) | Moderate (Requires spectral subtraction / VAD) | **Guaranteed** (Raw audio discarded immediately after feature extraction) | **Dual License:** AGPL-3.0 / Commercial (audEERING GmbH) | **RECOMMENDED WITH PERMISSIVE C++ EXTRACTOR** (Avoid AGPL) |
| **DistilHuBERT-SER (ONNX INT8)** | Self-Supervised Acoustic Embeddings | **$25\text{--}35\text{ms}$** ($30\text{x}$ real-time) | $\sim 23.5\text{M}$ params | Moderate to High | High (Tolerant to reverberation and noise) | **Guaranteed** (RAM tensor discarded after inference) | **Apache 2.0** | **RECOMMENDED** (Primary neural speech emotion candidate) |
| **wav2vec 2.0 Base (HuggingFace)** | Raw Waveform $\to$ Transformer Latents | **$320\text{--}480\text{ms}$** ($6\text{x}$ real-time) | $\sim 94.4\text{M}$ params | High | High | Guaranteed in-memory | **Apache 2.0 / MIT** | **OPTIONAL_ACCELERATED** (Excessive CPU latency on low-end edge nodes) |
| **WavLM Large** | Raw Waveform $\to$ Denoised Latents | **$1200\text{--}1800\text{ms}$** (Near real-time bottleneck) | $\sim 316\text{M}$ params | Very High | Very High (State-of-the-art denoising) | Guaranteed in-memory | **MIT License** | **UNSUITABLE FOR EDGE CPU** (Viable only on discrete server/workstation GPU) |
| **Log-Mel Spectrogram + MobileNetV3-Audio** | 2D Time-Frequency Spectrogram | **$8\text{--}12\text{ms}$** ($80\text{x}$ real-time) | $\sim 3.8\text{M}$ params | Moderate | Moderate | Guaranteed in-memory | **Apache 2.0** | **RECOMMENDED** (Lightweight neural acoustic fallback) |

---

## 5. Sub-phase 1.4 — Multimodal Fusion Architectures

| Fusion Architecture | Synchronization Mechanism | CPU Processing Latency | Tolerance to Missing Modalities | Cross-Modal Interaction Modeling | Handling of Conflicting Signals | Deployment & Pipeline Complexity | Licensing | EON Recommendation |
|---|---|---|---|---|---|---|---|---|
| **Early Fusion (Feature Concat)** | Rigid timestamp frame matching | **Low** ($<2\text{ms}$) | **Extremely Poor** (Fails if camera or mic drops) | Linear concatenation; lacks deep cross-attention | Flattens conflict into noisy compromise | Low | MIT / Apache 2.0 | **UNSUITABLE** (Robotics sensors drop frames constantly) |
| **Late Fusion (Decision Ensemble / Bayesian)** | Independent asynchronous polling | **Ultra-Low** ($<1\text{ms}$) | **Excellent** (Falls back to single available modality) | **None** (Modality predictions made in total isolation) | Detects conflict via divergent distributions; averages output | Very Low | MIT / Apache 2.0 | **RECOMMENDED AS DETERMINISTIC FALLBACK** |
| **Multimodal Transformer (MulT / Cross-Attention)** | Unaligned cross-modal self-attention | **Medium to High** ($40\text{--}70\text{ms}$ on CPU) | Moderate (Requires learned mask tokens) | **Very High** (Models fine-grained inter-modal dynamics) | Learns complex non-linear combinations | High | MIT / Apache 2.0 | **OPTIONAL_ACCELERATED** (Best accuracy when GPU/NPU available) |
| **Hybrid Hierarchical Reliability-Aware Fusion** | Sliding temporal window ($500\text{ms}$) + Quality Gating | **Low to Medium** ($8\text{--}15\text{ms}$ on CPU) | **High** (Dynamic gating weights missing sensors to zero) | **High** (Gated cross-attention over unimodal embeddings) | Preserves explicit `conflict_flag` for downstream reasoning | Moderate (Structured multi-stage pipeline) | MIT / Apache 2.0 | **RECOMMENDED** (Primary EON Perception Architecture) |

---

## 6. Sub-phase 1.5 — Human Activity Recognition (HAR) Approaches

| HAR Technology Pipeline | Input Representation | CPU Latency (4-Core CPU) | Robustness to Occlusion & Clothing | Viewpoint / Distance Invariance | 3D Spatial Geometry | Privacy Protection Level | Commercial Licensing | EON Recommendation |
|---|---|---|---|---|---|---|---|---|
| **BlazePose (MediaPipe) + ST-GCN / Lightweight TCN** | 33 3D Skeletal Keypoints | **$12\text{--}18\text{ms}$** ($>50\text{ fps}$) | High (Keypoint tracking infers occluded limbs) | High (Normalized skeletal coordinate frame) | High (Relative 3D coordinates) | **Very High** (Zero raw RGB stored; skeletal coordinates are non-biometric) | **Apache 2.0** | **RECOMMENDED** (Primary EON Activity Pipeline) |
| **RTMPose + 2s-AGCN (ONNX INT8)** | 17/26 Skeletal Joints + Bone Vectors | **$20\text{--}30\text{ms}$** ($35\text{ fps}$) | Very High | Very High | Moderate to High | Very High | **Apache 2.0** | **RECOMMENDED** (Alternative multi-person skeletal pipeline) |
| **3D-CNN (I3D / SlowFast) on Raw RGB Video** | Spatio-Temporal RGB Voxel Tensor ($16\text{--}64\text{ frames}$) | **$350\text{--}900\text{ms}$** (Severe lag) | Moderate (Sensitive to lighting, clothing color) | Poor (Requires extensive multi-view augmentation) | None (2D projection only) | **Extremely Low** (Requires buffering multi-frame raw video) | Apache 2.0 / Research | **UNSUITABLE FOR EDGE CPU** (Prohibitive compute and privacy violations) |
| **VideoMAE / Spatio-Temporal Transformers** | Video Patch Tokens | **$>1500\text{ms}$** (Unusable on CPU) | High | Moderate | None | Extremely Low | Apache 2.0 | **UNSUITABLE** (Requires datacenter-class GPU acceleration) |
| **Depth Point-Cloud (Intel RealSense) + PointNet** | 3D IR Depth Point Cloud | **$45\text{--}70\text{ms}$** ($15\text{ fps}$) | Very High (Unaffected by zero-light or dark rooms) | High (Direct Euclidean metric space) | Full Metric 3D Depth | **Maximum** (Zero facial texture or color information) | Apache 2.0 | **OPTIONAL_ACCELERATED** (Valuable for night-time or industrial environments) |

---

## 7. Sub-phase 1.6 — Gesture and Posture Recognition

| Framework / Architecture | Tracking Representation | CPU Latency (4-Core x86) | Tracking Memory (RAM) | Static vs Dynamic | Occlusion Tolerance | Commercial License | EON Recommendation |
|---|---|---|---|---|---|---|---|
| **MediaPipe Hands + Geometric Rules** | 21 3D Hand Landmarks | **$6.5\text{ms}$ per hand** | $\sim 24\text{MB}$ | Static + Simple Dynamic | Moderate (Recovers tracking via palm anchor) | **Apache 2.0** | **RECOMMENDED PRIMARY** |
| **MediaPipe Pose Posture Classifier** | 33 3D Skeletal Angles | **$<1.0\text{ms}$** | $\sim 28\text{MB}$ | Static Posture | High (Infers occluded joints) | **Apache 2.0** | **RECOMMENDED POSTURE STACK** |
| **Trajectory Dynamic Time Warping (DTW)** | Spatial Keypoint Trajectory | **$<1.2\text{ms}$** | $<2\text{MB}$ | Dynamic Gesture | High (Aligns variable-speed motion) | **MIT / Public Domain** | **RECOMMENDED DYNAMIC MATCHER** |
| **Skeletal ST-GCN / 1D-TCN Gesture** | Graph Convolution on Joints | **$4.2\text{ms}$** | $\sim 14\text{MB}$ | Complex Dynamic Gesture | High | **Apache 2.0** | **RECOMMENDED NEURAL GESTURE** |
| **OpenPose Hand** | 21 2D Keypoints | $75.0\text{ms}$ per hand | $\sim 350\text{MB}$ | Static | Poor | Non-Commercial | **UNSUITABLE (Latency & license)** |

---

## 8. Sub-phase 1.7 — Long-Term Memory Architectures

| Architecture Alternative | Primary Storage Technology | Read Latency (10k records, CPU) | Write Latency (WAL Mode) | Data Types Supported | Deletion Verification (GDPR Art 17) | Edge CPU Footprint | EON Recommendation |
|---|---|---|---|---|---|---|---|
| **Option A: Structured Relational** | SQLite (SQLCipher Encrypted) | **$<0.5\text{ms}$** | **$<2.0\text{ms}$** | SQL Rows, JSON payloads | **Trivial** (`PRAGMA secure_delete`) | **$<15\text{MB}$ RAM** | **RECOMMENDED MINIMAL BASELINE** |
| **Option B: Pure Semantic Vector** | Qdrant / FAISS Standalone | $4.0\text{ms}\text{--}8.0\text{ms}$ | $12.0\text{ms}$ | Dense Vector Embeddings | Complex (Index tombstoning) | $\sim 120\text{MB}$ RAM | **UNSUITABLE AS SOLE STORE** |
| **Option C: Hybrid Hierarchical** | SQLite Facts + Qdrant Embedded Vectors | **$<2.0\text{ms}$** | **$<6.0\text{ms}$** | Relational Facts + Vector Pointers | **Coordinated Purge + Crypto-Shred** | **$\sim 60\text{MB}$ RAM** | **RECOMMENDED TARGET ARCHITECTURE** |
| **Graph Database** | Neo4j / RDF Triple Store | $15.0\text{ms}\text{--}45.0\text{ms}$ | $25.0\text{ms}$ | Graph Entities & Relations | Moderate | $>350\text{MB}$ RAM | **UNSUITABLE (Heavy edge memory)** |

---

## 9. Sub-phase 1.8 — Empathy Reasoning Approaches

| Approach | Reasoning Engine | Execution Latency (CPU) | Determinism & Auditability | Edge Memory Overhead | Anthropomorphic Risk | EON Recommendation |
|---|---|---|---|---|---|---|
| **Deterministic Decision Trees / FSM** | Scherer CPM Appraisal Checks | **$<0.5\text{ms}$** | **100% Deterministic** | $<2\text{MB}$ RAM | **Zero** (Explicit machine boundary) | **RECOMMENDED SAFETY CORE** |
| **Bayesian Decision Networks** | Graphical Belief Propagation | **$1.8\text{ms}$** | High (Mathematical probability) | $\sim 5\text{MB}$ RAM | Low | **RECOMMENDED PROBABILISTIC** |
| **Generative LLM Prompting** | End-to-end prompt-based empathy | $85.0\text{ms}\text{--}250.0\text{ms}$ | Low (Stochastic tokens) | $>1.2\text{GB}$ RAM | **High** (May feign human feelings) | **RESTRICTED TO CONSTRAINED ADVISOR** |
| **Hybrid Policy Engine** | FSM Safety Guard + Bayesian Appraisal | **$<2.5\text{ms}$** | **High** (Deterministic override) | $\sim 8\text{MB}$ RAM | Low | **RECOMMENDED TARGET ARCHITECTURE** |

---

## 10. Sub-phase 1.9 — Personality Modelling Approaches

| Persona Architecture | Parameter Representation | Execution Latency | Stability & Consistency | Vulnerability to Drift | User Customization | EON Recommendation |
|---|---|---|---|---|---|---|
| **Option A: Fixed Profiles** | Rigid Hardcoded Configurations | **$<0.1\text{ms}$** | **Maximum** (100% constant) | **Zero** | None | Minimal Baseline |
| **Option B: Unconstrained RL** | Neural Policy Gradient | $>50.0\text{ms}$ | Extremely Poor | **Severe** (Drifts unpredictably) | Opaque | **REJECTED AS UNSAFE** |
| **Option C: Hybrid Persona Engine** | Base JSON + Context Modulation + Clamps | **$<0.5\text{ms}$** | **High** (Bounded by math clamps) | **Zero** (Hard clamp invariants) | **Full Explicit Control** | **RECOMMENDED TARGET ARCHITECTURE** |

---

## 11. Sub-phase 1.10 — Social Interaction Systems

| Interaction System Architecture | Coordination Framework | Turn-Taking Latency | Edge CPU Footprint | Interruption Resilience | Multi-Party Support | EON Recommendation |
|---|---|---|---|---|---|---|
| **Option A: Deterministic HFSM** | Hierarchical Finite State Machine | Fixed Timer ($>1.2\text{s}$) | **$<1\text{MB}$ RAM** | Moderate | Basic | Minimal Baseline |
| **Option B: Pure LLM Agent** | Autoregressive Next-Action LLM | Slow ($>800\text{ms}$) | $>2.5\text{GB}$ RAM | Extremely Poor | Poor | **UNSUITABLE ON EDGE CPU** |
| **Option C: Hybrid Social Engine** | HFSM Macro + Multimodal TRP + Frame/Slot | **Adaptive ($<350\text{ms}$)** | **$<15\text{MB}$ RAM** | **Instant ($<50\text{ms}$ halt)** | **High** (F-Formation tracking) | **RECOMMENDED TARGET ARCHITECTURE** |

---

## 12. Sub-phase 1.11 — Response Generation Technologies

| Generation & Synthesis Stack | Component Architectures | Latency (TTFS on 4-Core CPU) | Resident Memory (RAM) | Offline Capability | Commercial License | EON Recommendation |
|---|---|---|---|---|---|---|
| **Template-Only NLG + Piper TTS** | Parameter Substitution + VITS TTS | **$<85\text{ms}$** | $\sim 75\text{MB}$ | **100% Offline** | MIT License | **RECOMMENDED FAST FALLBACK** |
| **Quantized SLM (Qwen2.5-1.5B) + Piper** | `llama.cpp` Q4_K_M + Piper VITS | **$<350\text{ms}$ (streaming)** | $\sim 1.25\text{GB}$ | **100% Offline** | Apache 2.0 / MIT | **RECOMMENDED PRIMARY HYBRID** |
| **Cloud LLM API (OpenAI / Claude)** | Proprietary Cloud API over HTTP | $1200\text{ms}\text{--}2500\text{ms}$ | $<10\text{MB}$ local | **Zero (Fails offline)** | Proprietary Paid API | **UNSUITABLE FOR BASE PLATFORM** |
| **Full LLM (7B / 14B) on Edge CPU** | `llama.cpp` 7B Q4 | $>2500\text{ms}$ (Unusable) | $>4.5\text{GB}$ | 100% Offline | Apache 2.0 | **UNSUITABLE FOR REAL-TIME CPU** |

---

## 13. Consolidated Cross-Domain Synthesis (Sub-phases 1.1 through 1.11)

| Sub-phase | Selected Baseline Architecture | Fallback Architecture | Target CPU Budget | Max Permissible Latency (p95) | Safety Invariant |
|---|---|---|---|---|---|
| **1.1 Emotion Methods** | Continuous VAD Regression + Discrete Softmax | Unimodal Rules / Majority Voting | $<10\text{ms}$ | $15\text{ms}$ | Probabilistic observation only; non-diagnostic. |
| **1.2 Facial Analysis** | SCRFD-500M + MediaPipe Face Mesh + AU Regressor | Landmark Distance Heuristics | $<15\text{ms}$ | $25\text{ms}$ | Ephemeral tracking IDs; zero face biometrics stored. |
| **1.3 Speech Emotion** | Silero VAD + DistilHuBERT-SER (ONNX INT8) | eGeMAPS + LightGBM | $<25\text{ms}$ | $40\text{ms}$ | Ephemeral in-memory audio buffers; zero persistent audio. |
| **1.4 Multimodal Fusion** | Hybrid Reliability-Aware Gated Cross-Attention | Late Bayesian Decision Averaging | $<12\text{ms}$ | $20\text{ms}$ | Explicit conflict flags; never forces consensus. |
| **1.5 Activity (HAR)** | MediaPipe Pose + ST-GCN Skeletal Classifier | Kinematic Velocity Thresholds | $<20\text{ms}$ | $30\text{ms}$ | Non-inferential; physical motion classification only. |
| **1.6 Gesture & Posture**| MediaPipe Hands + DTW Trajectory Matching | Geometric Angular Finger Flexion | $<15\text{ms}$ | $20\text{ms}$ | Gestures are advisory; cannot bypass safety stops. |
| **1.7 Long-Term Memory**| Option C: Hybrid SQLite Facts + Qdrant Vectors | SQLite Relational Alone | $<5\text{ms}$ | $10\text{ms}$ | Anti-profiling; hard deletion; untrusted data boundary. |
| **1.8 Empathy Reasoning**| Cognitive Appraisal FSM + Bayesian Belief Net | Static Policy Table | $<3\text{ms}$ | $5\text{ms}$ | Never claim subjective feeling; clarify before assuming. |
| **1.9 Personality PSE** | Base Persona Asset + Dynamic Clamps | Fixed Unmodulated Profile | $<1\text{ms}$ | $2\text{ms}$ | Bounded style parameters; anti-drift mathematical clamps. |
| **1.10 Social Interaction**| HFSM Macro Stages + Multimodal TRP | Fixed Timer Turn-Taking | $<5\text{ms}$ | $10\text{ms}$ | Social costmaps are advisory; safety nav is authoritative. |
| **1.11 Response Gen ERG** | Qwen2.5-1.5B (llama.cpp) + Piper Neural TTS | Parameterized Templates + Piper | $<350\text{ms}$ | $500\text{ms}$ | Language models never directly command physical motors. |
