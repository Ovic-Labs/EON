# OVIC EON — Documentation Index

**Emotional Intelligence Infrastructure for Robotics**  
**Organization:** OVIC Labs  
**Repository:** [https://github.com/Ovic-Labs/EON.git](https://github.com/Ovic-Labs/EON.git)  
**Milestone:** Phase 0 — Foundation and Documentation Qualification (FOUNDER APPROVED — BASELINE ACCEPTED)  
**Next Milestone:** Phase 1 — Engineering Infrastructure & Core Runtime Foundation (AUTHORIZED TO BEGIN — NOT YET VERIFIED)  
**Status:** Phase 0: FOUNDER APPROVED — BASELINE ACCEPTED | Implementation: NOT STARTED (0%) | Production Readiness: NOT QUALIFIED  

Welcome to the central documentation index for **OVIC EON**. This document catalogues all 15 Phase 0 engineering and product specifications, outlines their relationships, and provides structured reading guides for various stakeholders.

---

## 1. Phase 0 Documentation Matrix

The Phase 0 documentation suite comprises 16 foundational specifications across three core domains:

### 1.1 Product Documentation (`docs/product/`)

| Document | Document ID | Description |
|---|---|---|
| [Product Vision](product/PRODUCT_VISION.md) | EON-PV-001 | Long-term vision, core mission, architectural principles, and seven-engine overview |
| [Engine Scope](product/ENGINE_SCOPE.md) | EON-ENG-SCOPE-001 | Functional boundaries, responsibilities, input/output contracts, and non-goals for all seven engines |
| [Customer Segments](product/CUSTOMER_SEGMENTS.md) | EON-CUST-001 | Target markets, buyer personas, value propositions, and robotics industry use environments |
| [Use Cases](product/USE_CASES.md) | EON-UC-001 | Operational scenarios across humanoid, service, industrial, and social robotics |
| [Functional Requirements](product/FUNCTIONAL_REQUIREMENTS.md) | EON-FR-001 | Comprehensive specification of functional capabilities (`EON-FR-001` through `EON-FR-060`) |
| [Non-Functional Requirements](product/NON_FUNCTIONAL_REQUIREMENTS.md) | EON-NFR-001 | Reliability, security, maintainability, modularity, and resource efficiency requirements (`EON-NFR-001` through `EON-NFR-078`) |
| [Performance Requirements](product/PERFORMANCE_REQUIREMENTS.md) | EON-PROD-PERF-001 | Detailed latency, throughput, memory, and CPU targets, benchmarks, and qualification criteria (`EON-PERF-001` through `EON-PERF-066`) |
| [Privacy and Safety Requirements](product/PRIVACY_AND_SAFETY_REQUIREMENTS.md) | EON-PSR-001 | Data minimization, retention/deletion controls, physical safety boundaries, and responsible AI (`EON-PSR-001` through `EON-PSR-086`) |
| [Commercial Licensing Strategy](product/COMMERCIAL_LICENSING_STRATEGY.md) | EON-LIC-001 | Open-core boundaries, dependency whitelisting, model/dataset compliance, and OEM licensing models |
| [Product Requirements Document](product/PRD.md) | EON-PRD-001 | Master product specification uniting vision, commercial direction, architecture, and milestone roadmap |

### 1.2 Engineering Requirements (`docs/requirements/`)

| Document | Document ID | Description |
|---|---|---|
| [Software Requirements Specification](requirements/SRS.md) | EON-SRS-001 | Technical software-level engineering requirements for EON Core and all seven engines (`EON-SRS-001` through `EON-SRS-203`) |
| [Requirement Traceability Matrix](requirements/REQUIREMENT_TRACEABILITY.md) | EON-RTM-001 | End-to-end forward and backward traceability matrix mapping product needs to software specs, tests, and evidence |

### 1.3 Acceptance and Qualification (`docs/acceptance/`)

| Document | Document ID | Description |
|---|---|---|
| [Acceptance Criteria](acceptance/ACCEPTANCE_CRITERIA.md) | EON-AC-001 | Objective acceptance criteria and verification gates for all components, engines, and platform capabilities |
| [Test Evidence Register](acceptance/TEST_EVIDENCE_REGISTER.md) | EON-TE-001 | Master register tracking test execution records, artifact links, and qualification evidence |
| [Defect Register](acceptance/DEFECT_REGISTER.md) | EON-DEF-001 | Repository defect catalog, classification scheme, severity/priority matrices, and lifecycle workflows |
| [Release Acceptance](acceptance/RELEASE_ACCEPTANCE.md) | EON-ACC-REL-001 | Release governance policies, mandatory milestone release gates, and founder sign-off procedures |
| [Phase 0 Verification Report](acceptance/PHASE_0_FINAL_VERIFICATION_REPORT.md) | EON-REP-P0-FINAL-001 | Final verification, qualification report, requirement audit, and formal founder approval record |
| [Phase 0 Production Qualification Report](acceptance/PHASE_0_PRODUCTION_QUALIFICATION_REPORT.md) | EON-REP-P0-PROD-001 | Final production implementation, hardening, and qualification report |
| [Phase 0 Repository Cleanup Report](acceptance/PHASE_0_REPOSITORY_CLEANUP_REPORT.md) | EON-REP-P0-CLN-001 | Repository cleanup audit, preservation ledger, and verification record |

### 1.4 Engineering Roadmap (`docs/roadmap/`)

| Document | Document ID | Description |
|---|---|---|
| [Phase 1 Execution Plan](roadmap/PHASE_1_EXECUTION_PLAN.md) | EON-PLN-PH1-001 | Phase 1 engineering infrastructure, core runtime, module boundaries, and acceptance criteria |

### 1.5 Architecture Documentation (`docs/architecture/`)

| Document | Document ID | Description |
|---|---|---|
| [Data Schema Architecture](architecture/DATA_SCHEMA_ARCHITECTURE.md) | EON-ARCH-SCHEMA-001 | Foundational data contracts, Pydantic v2 architecture, and security boundaries |
| [Event Envelope Specification](architecture/EVENT_ENVELOPE_SPECIFICATION.md) | EON-SPEC-ENV-001 | Universal EventEnvelope[T] specification, causality tracking, and sequence flows |
| [Schema Versioning Policy](architecture/SCHEMA_VERSIONING_POLICY.md) | EON-POL-VER-001 | SemVer 2.0.0 compatibility rules, breaking change classifications, and deprecation |
| [Core Event Bus Architecture](architecture/CORE_EVENT_BUS_ARCHITECTURE.md) | EON-ARCH-CORE-001 | In-memory asynchronous event bus architecture, priority queues, and lifecycle |
| [Event Routing and Delivery](architecture/EVENT_ROUTING_AND_DELIVERY.md) | EON-ARCH-CORE-002 | Snapshot-based routing, exact and wildcard subscriptions, and delivery outcomes |
| [Backpressure and Priority Policy](architecture/BACKPRESSURE_AND_PRIORITY_POLICY.md) | EON-ARCH-CORE-003 | Backpressure policies (WAIT, REJECT, DROP), priority scheduling, and starvation |
| [System Layered Architecture](architecture/SYSTEM_LAYERED_ARCHITECTURE.md) | EON-ARCH-LAYERS-001 | Ten-tier layered architecture model, layer evaluations, and data flows |
| [Inter-Layer Interfaces](architecture/INTER_LAYER_INTERFACES.md) | EON-ARCH-INT-001 | Strongly typed interfaces, SPIs, buffer contracts, and cross-layer boundaries |
| [Architecture Constraints](architecture/ARCHITECTURE_CONSTRAINTS.md) | EON-ARCH-CONST-001 | Non-negotiable architectural invariants (DAG, safety, privacy, CPU-first) |
| [Seven Engine Architecture](architecture/SEVEN_ENGINE_ARCHITECTURE.md) | EON-ARCH-ENG-001 | Seven intelligence engines overview, mission roster, and coordination model |
| [Engine Boundary Specifications](architecture/ENGINE_BOUNDARY_SPECIFICATIONS.md) | EON-SPEC-ENG-001 | Complete 27-item boundary specifications for all seven intelligence engines |
| [Engine Dependency Matrix](architecture/ENGINE_DEPENDENCY_MATRIX.md) | EON-ARCH-DEP-002 | Authoritative 7x7 engine interaction matrix, event dependencies, and DAG |
| [Engine Input/Output Contracts](architecture/ENGINE_INPUT_OUTPUT_CONTRACTS.md) | EON-SPEC-ENG-IO-001 | Schema mapping, existing Phase 1.2 contracts, and proposed Phase 2 schemas |
| [Phase 2.1 & 2.2 Qualification Report](architecture/PHASE_2_1_2_2_ARCHITECTURE_QUALIFICATION_REPORT.md) | EON-QUAL-PH2-ARCH-001 | Architecture qualification report and acceptance matrix for Sub-phases 2.1 & 2.2 |

#### 1.5.1 Architecture Decision Records (`docs/architecture/decisions/`)

| ADR | Title | Status | Scope |
|---|---|---|---|
| [ADR-001](architecture/decisions/ADR-001-LAYERED-ARCHITECTURE.md) | Ten-Tier Layered Architecture Model | Approved | System-wide layered architecture decomposition |
| [ADR-002](architecture/decisions/ADR-002-ENGINE-INDEPENDENCE.md) | Seven Engine Independence and Decoupling | Approved | Zero direct coupling and modular engine design |
| [ADR-003](architecture/decisions/ADR-003-EVENT-DRIVEN-COMMUNICATION.md) | Asynchronous Event-Driven Communication | Approved | Core Event Bus messaging and bounded queues |
| [ADR-004](architecture/decisions/ADR-004-SHARED-CONTEXT-OWNERSHIP.md) | Shared Context and Memory Layer Ownership | Approved | L6 memory architecture and EMS custodianship |
| [ADR-005](architecture/decisions/ADR-005-MODEL-ADAPTER-BOUNDARIES.md) | Model and Algorithm Adapter Boundaries | Approved | L7 adapter interfaces and framework isolation |
| [ADR-006](architecture/decisions/ADR-006-CPU-FIRST-EXECUTION.md) | CPU-First and Edge-First Execution Invariant | Approved | Real-time baseline operation on 4-core edge CPU |
| [ADR-007](architecture/decisions/ADR-007-SDK-BOUNDARIES.md) | SDK and Client Integration Boundaries | Approved | Dual-mode in-process and IPC client bindings |
| [ADR-008](architecture/decisions/ADR-008-ROS2-INTEGRATION-BOUNDARY.md) | ROS 2 Integration and Lifecycle Node Boundary | Approved | Optional ROS 2 package and lifecycle node bridge |
| [ADR-009](architecture/decisions/ADR-009-ROBOT-ABSTRACTION.md) | Robot Hardware Abstraction & Non-Authoritative Actuation | Approved | Strict advisory boundaries; zero direct motor control |
| [ADR-010](architecture/decisions/ADR-010-EDGE-CLOUD-SEPARATION.md) | Edge-First Execution and Cloud Separation Boundary | Approved | Air-gapped edge autonomy with zero cloud dependency |
| [ADR-011](architecture/decisions/ADR-011-SECURITY-AND-PRIVACY-ARCHITECTURE.md) | Security, Privacy, and Verifiable Data Governance | Approved | Zero raw media persistence and cryptographic shredding |

### 1.6 Engineering Implementation Reports (`docs/engineering/`)

| Document | Document ID | Description |
|---|---|---|
| [Phase 1.1 Implementation Report](engineering/PHASE_1_1_IMPLEMENTATION_REPORT.md) | EON-REP-PH1.1-001 | Phase 1.1 packaging scaffolding, build configuration, tests, and qualification report |
| [Phase 1.2 Implementation Report](engineering/PHASE_1_2_IMPLEMENTATION_REPORT.md) | EON-REP-PH1.2-001 | Phase 1.2 data schemas, event envelopes, serialization suite, and qualification report |
| [Phase 1.3 Implementation Report](engineering/PHASE_1_3_IMPLEMENTATION_REPORT.md) | EON-REP-PH1.3-001 | Phase 1.3 core event bus, bounded queues, benchmarks, and qualification report |

### 1.7 Developer Documentation (`docs/developer/`)

| Document | Document ID | Description |
|---|---|---|
| [Developer Installation Guide](developer/INSTALLATION.md) | EON-DEV-INST-001 | Setup, virtual environments, editable installation, quality tools, and troubleshooting |
| [Data Contracts Developer Guide](developer/DATA_CONTRACTS_GUIDE.md) | EON-DEV-SCHEMA-001 | Developer guide with copy-pasteable examples for observations, emotions, and events |
| [Event Bus Developer Guide](developer/EVENT_BUS_DEVELOPER_GUIDE.md) | EON-DEV-CORE-001 | Integration guide for publishers, subscribers, failure isolation, and metrics |

### 1.8 Technical Research and Feasibility (`docs/research/phase-1/`)

| Document | Document ID | Description |
|---|---|---|
| [Phase 1 Research Overview](research/phase-1/README.md) | EON-RES-OVR-001 | Phase 1 research objective, scope boundaries, methodology, and navigational index |
| [Scientific Terminology Glossary](research/phase-1/GLOSSARY.md) | EON-RES-GLOSS-001 | Definitions for affective computing, vision, acoustics, memory, social reasoning, NLG, hardware, and ROS 2 |
| [Research Source Register](research/phase-1/RESEARCH_SOURCE_REGISTER.md) | EON-RES-SRC-001 | 130 independently audited, verifiable scientific sources (`SRC-001`–`SRC-130`) |
| [Technical Comparison Matrix](research/phase-1/TECHNICAL_COMPARISON_MATRIX.md) | EON-RES-TCM-001 | Multi-dimensional comparison of algorithms, CPU suitability, latency, and licensing across all 18 sub-phases |
| [Engine Dependency Matrix](research/phase-1/ENGINE_DEPENDENCY_MATRIX.md) | EON-ARCH-DEP-001 | Cross-engine interactions, event hand-offs, and capability mappings for all seven engines |
| [Initial Perception Architecture](research/phase-1/EON_PERCEPTION_ARCHITECTURE.md) | EON-ARCH-PERC-001 | Proposed edge-CPU perception pipeline, Mermaid diagram, and data contracts |
| [Social Intelligence Architecture](research/phase-1/EON_SOCIAL_INTELLIGENCE_ARCHITECTURE.md) | EON-ARCH-SOC-001 | Proposed social intelligence pipeline, memory lifecycle, and multimodal response architecture |
| [Licensing Compliance Matrix](research/phase-1/LICENSING_COMPLIANCE_MATRIX.md) | EON-RES-LIC-001 | Comprehensive IP compliance register covering all evaluated models, weights, datasets, and voice checkpoints |
| [Hardware Compatibility Matrix](research/phase-1/HARDWARE_COMPATIBILITY_MATRIX.md) | EON-RES-HW-001 | Edge compute platform compatibility matrix across Raspberry Pi 5, RK3588, Core Ultra 5, Ryzen 7, and Jetson |
| [Edge Deployment Architecture](research/phase-1/EDGE_DEPLOYMENT_ARCHITECTURE.md) | EON-ARCH-EDGE-001 | Multi-process runtime architecture, zero-copy shared memory IPC, CPU pinning, and memory budgets |
| [ROS 2 Integration Architecture](research/phase-1/ROS2_INTEGRATION_ARCHITECTURE.md) | EON-ARCH-ROS2-001 | ROS 2 Jazzy/Humble lifecycle node mapping, message definitions (`.msg`, `.srv`, `.action`), and safety boundaries |
| [Emotion Recognition Methods](research/phase-1/1.1-emotion-recognition-methods.md) | EON-RES-SUB-1.1 | Sub-phase 1.1: Foundations, VAD representation, calibration, and datasets |
| [Facial Expression Analysis](research/phase-1/1.2-facial-expression-analysis.md) | EON-RES-SUB-1.2 | Sub-phase 1.2: MediaPipe Face Mesh, FACS Action Units, and ephemeral tracking |
| [Speech Emotion Analysis](research/phase-1/1.3-speech-emotion-analysis.md) | EON-RES-SUB-1.3 | Sub-phase 1.3: Silero VAD, DistilHuBERT-SER, acoustics, and noise resilience |
| [Multimodal Fusion Methods](research/phase-1/1.4-multimodal-fusion-methods.md) | EON-RES-SUB-1.4 | Sub-phase 1.4: Hybrid Gated Cross-Attention, sliding windows, and conflict flags |
| [Human Activity Recognition](research/phase-1/1.5-human-activity-recognition.md) | EON-RES-SUB-1.5 | Sub-phase 1.5: 3D BlazePose + ST-GCN, taxonomy, and non-inferential safety |
| [Gesture & Posture Recognition](research/phase-1/1.6-gesture-and-posture-recognition.md) | EON-RES-SUB-1.6 | Sub-phase 1.6: MediaPipe Hands, DTW trajectories, pointing deictics, and posture semantics |
| [Long-Term Memory Architectures](research/phase-1/1.7-long-term-memory-architectures.md) | EON-RES-SUB-1.7 | Sub-phase 1.7: Hybrid hierarchical memory (SQLite + Qdrant), anti-profiling, and GDPR deletion |
| [Empathy Reasoning Approaches](research/phase-1/1.8-empathy-reasoning-approaches.md) | EON-RES-SUB-1.8 | Sub-phase 1.8: Cognitive appraisal (Scherer CPM), perspective-taking, and anti-manipulation |
| [Personality Modelling](research/phase-1/1.9-personality-modelling.md) | EON-RES-SUB-1.9 | Sub-phase 1.9: Parametric style profiles, anti-drift clamps, and user preference controls |
| [Social Interaction Systems](research/phase-1/1.10-social-interaction-systems.md) | EON-RES-SUB-1.10 | Sub-phase 1.10: 12-stage interaction HFSM, multimodal TRP turn-taking, and social navigation |
| [Response Generation](research/phase-1/1.11-response-generation.md) | EON-RES-SUB-1.11 | Sub-phase 1.11: Hybrid NLG (Qwen2.5-1.5B via `llama.cpp`), Piper neural TTS, and motor safety firewalls |
| [Open-Source Model Research](research/phase-1/1.12-open-source-model-research.md) | EON-RES-SUB-1.12 | Sub-phase 1.12: Comprehensive 20-field model comparison across all 7 engines |
| [Commercial Licensing & Due-Diligence](research/phase-1/1.13-commercial-model-and-dataset-licensing.md) | EON-RES-SUB-1.13 | Sub-phase 1.13: 10-tier IP due-diligence, SBOM generation, and license whitelist |
| [CPU, GPU & NPU Requirements](research/phase-1/1.14-cpu-gpu-npu-hardware-requirements.md) | EON-RES-SUB-1.14 | Sub-phase 1.14: 4 hardware tiers, memory bandwidth analysis, SIMD vectorization, and Core Ultra 5 deep dive |
| [Edge Computing Feasibility](research/phase-1/1.15-edge-computing-feasibility.md) | EON-RES-SUB-1.15 | Sub-phase 1.15: Hybrid multi-process worker pools, priority scheduling, and 5 degraded modes |
| [ROS 2 Integration Requirements](research/phase-1/1.16-ros2-integration-requirements.md) | EON-RES-SUB-1.16 | Sub-phase 1.16: ROS 2 Jazzy Jalisco lifecycle nodes, message definitions, and SROS2 safety boundaries |
| [Comprehensive Technical Feasibility](research/phase-1/1.17-comprehensive-technical-feasibility-report.md) | EON-RES-SUB-1.17 | Sub-phase 1.17: Master technical, commercial, and operational feasibility report with risk register |
| [Model & Dataset Selection Register](research/phase-1/1.18-model-and-dataset-selection-register.md) | EON-RES-SUB-1.18 | Sub-phase 1.18: Authoritative model, dataset, and algorithm selection register with SHA-256 checksums |
| [Phase 1 Master Qualification Report](research/phase-1/PHASE_1_FINAL_QUALIFICATION_REPORT.md) | EON-QUAL-PHASE1-MASTER | Master Phase 1 Final Technical Qualification Report covering all 18 sub-phases |

---

## 2. The Seven Intelligence Engines

OVIC EON organizes intelligence processing into seven specialized engines coordinated by **EON Core**:

1. **ERS — Emotion Recognition System:** Interprets supported observable signals (facial features, vocal cues, speech characteristics) as probabilistic observations.
2. **EMS — Emotional Memory System:** Maintains governed interaction history, memory lifecycle, retention limits, and deletion policies.
3. **ERE — Empathy Reasoning Engine:** Evaluates interaction context, conflicting signals, and social conventions to formulate structured reasoning outcomes.
4. **PSE — Personality Simulation Engine:** Maintains consistent, configurable behavioral characteristics within manufacturer-defined safety boundaries.
5. **SIE — Social Interaction Engine:** Manages turn-taking, conversation states, social protocols, and interruption dynamics.
6. **ERG — Emotional Response Generation:** Formulates structured multimodal response plans (speech tone, gestures, facial cues).
7. **HBU — Human Behaviour Understanding:** Identifies observable behavioral patterns, engagement indicators, and interaction dynamics over time.

---

## 3. Recommended Reading Order

### For Founders and Product Leaders
1. [Product Vision](product/PRODUCT_VISION.md)
2. [Customer Segments](product/CUSTOMER_SEGMENTS.md)
3. [Use Cases](product/USE_CASES.md)
4. [Product Requirements Document (PRD)](product/PRD.md)
5. [Release Acceptance](acceptance/RELEASE_ACCEPTANCE.md)
6. [Phase 0 Verification Report](acceptance/PHASE_0_FINAL_VERIFICATION_REPORT.md)
7. [Phase 1 Execution Plan](roadmap/PHASE_1_EXECUTION_PLAN.md)

### For Robotics Software Integrators
1. [Developer Installation Guide](developer/INSTALLATION.md)
2. [Engine Scope](product/ENGINE_SCOPE.md)
3. [Functional Requirements](product/FUNCTIONAL_REQUIREMENTS.md)
4. [Software Requirements Specification (SRS)](requirements/SRS.md)
5. [Performance Requirements](product/PERFORMANCE_REQUIREMENTS.md)
6. [Acceptance Criteria](acceptance/ACCEPTANCE_CRITERIA.md)
7. [Phase 1.1 Implementation Report](engineering/PHASE_1_1_IMPLEMENTATION_REPORT.md)

### For Safety, Privacy, and Systems Engineers
1. [Privacy and Safety Requirements](product/PRIVACY_AND_SAFETY_REQUIREMENTS.md)
2. [Non-Functional Requirements](product/NON_FUNCTIONAL_REQUIREMENTS.md)
3. [Requirement Traceability Matrix](requirements/REQUIREMENT_TRACEABILITY.md)
4. [Test Evidence Register](acceptance/TEST_EVIDENCE_REGISTER.md)
5. [Security Policy](../SECURITY.md)

---

## 4. Requirement ID Taxonomy

The project enforces strict, unambiguous identifier prefixes:

- `EON-PV-*`: Product Vision items
- `EON-FR-*`: Functional Requirements (`001`–`060`)
- `EON-NFR-*`: Non-Functional Requirements (`001`–`078`)
- `EON-PERF-*`: Performance Requirements (`001`–`066`)
- `EON-PSR-*`: Privacy and Safety Requirements (`001`–`086`)
- `EON-SRS-*`: Software Requirements Specification (`001`–`203`)
- `AC-*`: Acceptance Criteria
- `EON-EVD-*`: Test Evidence Identifiers
- `EON-TST-*`: Test Identifiers
- `DEF-*`: Defect Identifiers

---

## 5. Engineering Evidence Rules

In accordance with Phase 0 governance:

- **Provisional Targets:** Numerical performance targets remain labeled `PROVISIONAL` until empirical benchmark data is captured on documented reference hardware.
- **Evidence Integrity:** Test entries and evidence registers preserve `NOT_STARTED` and `TBD` until tests are formally run. No test may be marked `PASSED` without reproducible evidence.
- **Physical Safety Boundary:** OVIC EON outputs must never bypass independent robot safety systems or directly authorize physical motion.

---

## 6. Repository Links

- [Root README](../README.md)
- [Contributing Guidelines](../CONTRIBUTING.md)
- [Security Policy](../SECURITY.md)
