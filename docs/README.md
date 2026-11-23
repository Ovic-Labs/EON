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

#### 1.5.1 Foundations & Layered Architecture (Sub-phases 2.1 & 2.2)

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

#### 1.5.2 EON Core Architecture (Sub-phase 2.3)

| Document | Document ID | Description |
|---|---|---|
| [EON Core Architecture](architecture/EON_CORE_ARCHITECTURE.md) | EON-ARCH-CORE-004 | Kernel supervision, component topology, and lifecycle coordination |
| [EON Core Components](architecture/EON_CORE_COMPONENTS.md) | EON-ARCH-CORE-005 | Specification of Core Kernel subcomponents and ownership boundaries |
| [EON Core Initialization](architecture/EON_CORE_INITIALIZATION.md) | EON-ARCH-CORE-006 | Single-pass topological startup sequence and readiness probing |
| [EON Core State Model](architecture/EON_CORE_STATE_MODEL.md) | EON-ARCH-CORE-007 | System-level finite state machine and transition rules |
| [EON Core Failure Handling](architecture/EON_CORE_FAILURE_HANDLING.md) | EON-ARCH-CORE-008 | Three-tier failure recovery supervision, fault isolation, and circuit breaking |

#### 1.5.3 Engine Lifecycle Architecture (Sub-phase 2.4)

| Document | Document ID | Description |
|---|---|---|
| [Engine Lifecycle Architecture](architecture/ENGINE_LIFECYCLE_ARCHITECTURE.md) | EON-ARCH-LIFE-001 | Uniform lifecycle state machine and supervisor coordination |
| [Engine Lifecycle Contract](architecture/ENGINE_LIFECYCLE_CONTRACT.md) | EON-SPEC-LIFE-001 | Formal Python protocol, state hooks, and timeout constraints |
| [Engine State Transitions](architecture/ENGINE_STATE_TRANSITIONS.md) | EON-ARCH-LIFE-002 | Transition rules, state invariants, and concurrency safety |
| [Engine Recovery and Failure Policies](architecture/ENGINE_RECOVERY_AND_FAILURE_POLICIES.md) | EON-POL-LIFE-001 | Restart limits, fallback modes, and progressive degradation |
| [Engine Resource Declarations](architecture/ENGINE_RESOURCE_DECLARATIONS.md) | EON-SPEC-LIFE-002 | CPU, RAM, VRAM, and thread budget enforcement |

#### 1.5.4 Event-Driven Communication Architecture (Sub-phase 2.5)

| Document | Document ID | Description |
|---|---|---|
| [Event-Driven Communication](architecture/EVENT_DRIVEN_COMMUNICATION.md) | EON-ARCH-COMM-001 | Decoupled pub/sub message bus and cross-engine streaming |
| [Event Envelope Specification v2.0.0](architecture/EVENT_ENVELOPE_SPECIFICATION.md) | EON-SPEC-ENV-001 | Universal CloudEvents v1.0.2 event envelope specification |
| [Event Taxonomy](architecture/EVENT_TAXONOMY.md) | EON-SPEC-COMM-001 | Hierarchical topic taxonomy and event payload schema catalog |
| [Event Delivery and Reliability](architecture/EVENT_DELIVERY_AND_RELIABILITY.md) | EON-SPEC-COMM-002 | At-least-once / at-most-once delivery, ack tracking, and backpressure |
| [Event Security and Privacy](architecture/EVENT_SECURITY_AND_PRIVACY.md) | EON-POL-COMM-001 | Topic ACLs, encryption in transit, and ephemeral payload scrubbing |

#### 1.5.5 Shared Context Management Architecture (Sub-phase 2.6)

| Document | Document ID | Description |
|---|---|---|
| [Shared Context Architecture](architecture/SHARED_CONTEXT_ARCHITECTURE.md) | EON-ARCH-CTX-001 | Unified contextual state management for interaction and memory |
| [Context Data Model](architecture/CONTEXT_DATA_MODEL.md) | EON-SPEC-CTX-001 | Working memory, interaction state, and long-term user profile schemas |
| [Context Lifecycle](architecture/CONTEXT_LIFECYCLE.md) | EON-SPEC-CTX-002 | Session demarcations, continuous presence timeouts, and eviction |
| [Context Access Control](architecture/CONTEXT_ACCESS_CONTROL.md) | EON-POL-CTX-001 | Capability-based read/write access and per-engine scopes |
| [Context Privacy and Retention](architecture/CONTEXT_PRIVACY_AND_RETENTION.md) | EON-POL-CTX-002 | GDPR compliance, retention tags, and epistemological qualifications |
| [Context Conflict Resolution](architecture/CONTEXT_CONFLICT_RESOLUTION.md) | EON-SPEC-CTX-003 | Optimistic concurrency control and field-level merge strategies |

#### 1.5.6 Model Adapter Architecture (Sub-phase 2.7)

| Document | Document ID | Description |
|---|---|---|
| [Model Adapter Architecture](architecture/MODEL_ADAPTER_ARCHITECTURE.md) | EON-ARCH-MOD-001 | Provider-neutral neural execution and hardware abstraction |
| [Model Adapter Interface Specification](architecture/MODEL_ADAPTER_INTERFACE_SPECIFICATION.md) | EON-SPEC-MOD-001 | Synchronous and streaming inference protocol specifications |
| [Model Runtime Compatibility](architecture/MODEL_RUNTIME_COMPATIBILITY.md) | EON-SPEC-MOD-002 | ONNX Runtime, TensorRT, PyTorch, and llama.cpp execution profiles |
| [Hardware Capability Abstraction](architecture/HARDWARE_CAPABILITY_ABSTRACTION.md) | EON-SPEC-MOD-003 | Hardware auto-detection, execution tier ranking, and fallback routing |
| [Model Lifecycle](architecture/MODEL_LIFECYCLE.md) | EON-SPEC-MOD-004 | Model registration, memory allocation, warm-up, and hot-swapping |
| [Model Provenance and Governance](architecture/MODEL_PROVENANCE_AND_GOVERNANCE.md) | EON-POL-MOD-001 | License verification, SBOM, and weight checksum validation |

#### 1.5.7 Data Architecture (Sub-phase 2.8)

| Document | Document ID | Description |
|---|---|---|
| [Data Architecture](architecture/DATA_ARCHITECTURE.md) | EON-ARCH-DATA-001 | Edge storage architecture, multi-engine persistence, and synchronization |
| [Data Domain Model](architecture/DATA_DOMAIN_MODEL.md) | EON-SPEC-DATA-001 | Relational, document, and vector domain entities |
| [Data Storage Strategy](architecture/DATA_STORAGE_STRATEGY.md) | EON-SPEC-DATA-002 | SQLite WAL, DuckDB analytics, and vector index configurations |
| [Data Schema Versioning and Migrations](architecture/DATA_SCHEMA_VERSIONING_AND_MIGRATIONS.md) | EON-SPEC-DATA-003 | Automated migration runner, rollback contracts, and backward compatibility |
| [Data Security](architecture/DATA_SECURITY.md) | EON-POL-DATA-001 | AES-256-GCM encryption at rest and OS-keychain master key management |
| [Data Privacy and Retention](architecture/DATA_PRIVACY_AND_RETENTION.md) | EON-POL-DATA-002 | Automated retention sweeps and cryptographic shredding |
| [Edge and Cloud Data Synchronization](architecture/EDGE_AND_CLOUD_DATA_SYNCHRONIZATION.md) | EON-SPEC-DATA-004 | Offline-first sync, differential transfers, and conflict resolution |

#### 1.5.8 API Architecture (Sub-phase 2.9)

| Document | Document ID | Description |
|---|---|---|
| [API Architecture](architecture/API_ARCHITECTURE.md) | EON-ARCH-API-001 | Unified Northbound API Gateway, protocol topologies, and concurrency |
| [API Endpoint Catalog](architecture/API_ENDPOINT_CATALOG.md) | EON-SPEC-API-001 | Complete catalog of 24 REST endpoints and 4 WebSocket streams |
| [API Authentication and Authorization](architecture/API_AUTHENTICATION_AND_AUTHORIZATION.md) | EON-SPEC-API-002 | mTLS, JWT Bearer tokens, and API Key authentication contracts |
| [API Security](architecture/API_SECURITY.md) | EON-POL-API-001 | Threat modeling, token bucket rate limiting, and request validation |
| [API Versioning and Compatibility](architecture/API_VERSIONING_AND_COMPATIBILITY.md) | EON-SPEC-API-003 | URL path versioning, backward compatibility, and sunsetting policy |
| [API Error and Reliability Contract](architecture/API_ERROR_AND_RELIABILITY_CONTRACT.md) | EON-SPEC-API-004 | RFC 7807 problem details, circuit breaking, and reliability SLAs |

#### 1.5.9 Python SDK Architecture (Sub-phase 2.10)

| Document | Document ID | Description |
|---|---|---|
| [Python SDK Architecture](architecture/PYTHON_SDK_ARCHITECTURE.md) | EON-ARCH-SDK-001 | Dual-mode client design, async/sync paradigms, and 9 illustrative examples |
| [Python SDK Package Structure](architecture/PYTHON_SDK_PACKAGE_STRUCTURE.md) | EON-SPEC-SDK-001 | Package layout under `src/eon/`, public exports, and lean dependencies |
| [Python SDK API Contracts](architecture/PYTHON_SDK_API_CONTRACTS.md) | EON-SPEC-SDK-002 | Fully typed interfaces for top-level and subsystem clients |
| [Python SDK Authentication and Security](architecture/PYTHON_SDK_AUTHENTICATION_AND_SECURITY.md) | EON-POL-SDK-001 | Credential resolution, mTLS handling, and token lifecycle management |
| [Python SDK Error Handling](architecture/PYTHON_SDK_ERROR_HANDLING.md) | EON-SPEC-SDK-003 | Deterministic `EonError` hierarchy, status mapping, and full-jitter retry |
| [Python SDK Compatibility](architecture/PYTHON_SDK_COMPATIBILITY.md) | EON-SPEC-SDK-004 | Python 3.10–3.12 compatibility matrix and API version handshake |

#### 1.5.10 Architecture Decision Records (`docs/architecture/decisions/`)

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
| [ADR-012](architecture/decisions/ADR-012-eon-core-architecture.md) | EON Core Architecture & Kernel Orchestration | Approved | Kernel supervision and deterministic lifecycle sequence |
| [ADR-013](architecture/decisions/ADR-013-engine-lifecycle-contract.md) | Engine Lifecycle Contract Protocol | Approved | 6-state engine FSM and escalation recovery policies |
| [ADR-014](architecture/decisions/ADR-014-event-driven-communication-and-delivery-guarantees.md) | Event-Driven Communication and Delivery Guarantees | Approved | Bounded message broker, topic taxonomy, and QoS |
| [ADR-015](architecture/decisions/ADR-015-shared-context-and-access-control.md) | Shared Context Architecture & Access Control | Approved | Optimistic concurrency and capability-scoped contexts |
| [ADR-016](architecture/decisions/ADR-016-provider-neutral-model-adapter-architecture.md) | Provider-Neutral Model Adapter Architecture | Approved | Hardware abstraction, multi-backend routing, and fallback |
| [ADR-017](architecture/decisions/ADR-017-edge-storage-and-data-governance.md) | Edge Data Architecture, Storage & Retention | Approved | Multi-engine edge storage, AES-256-GCM, and shredding |
| [ADR-018](architecture/decisions/ADR-018-api-architecture-and-security.md) | API Gateway Architecture, Protocol & Security | Approved | Northbound API Gateway, OpenAPI 3.1, and token bucket |
| [ADR-019](architecture/decisions/ADR-019-python-sdk-architecture.md) | Dual-Mode Synchronous/Asynchronous Python SDK | Approved | Local in-process and remote client modes, strong typing |

#### 1.5.11 Phase 2 Architectural Qualification Reports

| Document | Document ID | Description |
|---|---|---|
| [Phase 2.1 & 2.2 Qualification Report](architecture/PHASE_2_1_2_2_ARCHITECTURE_QUALIFICATION_REPORT.md) | EON-QUAL-PH2-ARCH-001 | Architecture qualification report for Sub-phases 2.1 & 2.2 |
| [Phase 2.3 Qualification Report](architecture/PHASE_2_3_QUALIFICATION_REPORT.md) | EON-QUAL-PH2.3-001 | Architecture qualification report for Sub-phase 2.3 (EON Core) |
| [Phase 2.4 Qualification Report](architecture/PHASE_2_4_QUALIFICATION_REPORT.md) | EON-QUAL-PH2.4-001 | Architecture qualification report for Sub-phase 2.4 (Engine Lifecycle) |
| [Phase 2.5 Qualification Report](architecture/PHASE_2_5_QUALIFICATION_REPORT.md) | EON-QUAL-PH2.5-001 | Architecture qualification report for Sub-phase 2.5 (Event Communication) |
| [Phase 2.6 Qualification Report](architecture/PHASE_2_6_QUALIFICATION_REPORT.md) | EON-QUAL-PH2.6-001 | Architecture qualification report for Sub-phase 2.6 (Shared Context) |
| [Phase 2.7 Qualification Report](architecture/PHASE_2_7_QUALIFICATION_REPORT.md) | EON-QUAL-PH2.7-001 | Architecture qualification report for Sub-phase 2.7 (Model Adapters) |
| [Phase 2.8 Qualification Report](architecture/PHASE_2_8_QUALIFICATION_REPORT.md) | EON-QUAL-PH2.8-001 | Architecture qualification report for Sub-phase 2.8 (Data Architecture) |
| [Phase 2.9 Qualification Report](architecture/PHASE_2_9_QUALIFICATION_REPORT.md) | EON-QUAL-PH2.9-001 | Architecture qualification report for Sub-phase 2.9 (API Architecture) |
| [Phase 2.10 Qualification Report](architecture/PHASE_2_10_QUALIFICATION_REPORT.md) | EON-QUAL-PH2.10-001 | Architecture qualification report for Sub-phase 2.10 (Python SDK) |
| [Phase 2.3–2.10 Master Qualification Report](architecture/PHASE_2_3_TO_2_10_FINAL_QUALIFICATION_REPORT.md) | EON-QUAL-PH2-FINAL-001 | Master consolidated qualification report for Sub-phases 2.3 through 2.10 |

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
