# OVIC EON — Documentation Index

**Emotional Intelligence Infrastructure for Robotics**  
**Organization:** OVIC Labs  
**Repository:** [https://github.com/Ovic-Labs/EON.git](https://github.com/Ovic-Labs/EON.git)  
**Current Phase:** Phase 2 — System Architecture and Engineering Design (Completed & Qualified: Sub-phases 2.1–2.20)  
**Core Runtime Status:** Phase 1 Foundation Implemented & Verified (Sub-phases 1.1–1.3: 203 passing tests)  
**Research Status:** Phase 1 Technical Feasibility Qualified With Conditions (Sub-phases 1.1–1.18)  
**Product Baseline:** Phase 0 Product Foundation Production-Qualified (290 source requirements, 100% spec traceability)  
**Intelligence Engines Status:** Seven Engine Runtimes Not Implemented (0%) — Architecture & Boundaries Specified  
**Production Readiness:** Not Qualified — Emotional Intelligence Infrastructure in Active Architecture & Engineering  

Welcome to the central documentation index for **OVIC EON**. This document catalogues all engineering specifications, product documentation, technical research, architecture baselines, and qualification reports across Phases 0, 1, and 2.

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

For the dedicated, comprehensive index of all Phase 2 architecture specifications, ADRs, diagrams, and reports, see the [Architecture Documentation Index](architecture/README.md).

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

#### 1.5.10 C++ SDK Architecture (Sub-phase 2.11)

| Document | Document ID | Description |
|---|---|---|
| [C++ SDK Architecture](architecture/CPP_SDK_ARCHITECTURE.md) | EON-ARCH-CPP-001 | Native C++17 SDK architecture, Pimpl idiom, zero-copy SHM, and non-authoritative motion |
| [C++ SDK Package Structure](architecture/CPP_SDK_PACKAGE_STRUCTURE.md) | EON-ARCH-CPP-002 | CMake build layout, public/private header separation, and packaging deliverables |
| [C++ SDK API Contracts](architecture/CPP_SDK_API_CONTRACTS.md) | EON-SPEC-CPP-001 | Strongly typed interfaces, Result monad, and 7-state EngineState enum mapping |
| [C++ SDK Memory Management](architecture/CPP_SDK_MEMORY_MANAGEMENT.md) | EON-SPEC-CPP-002 | RAII memory management, bounded ring buffers, and std::pmr allocator support |
| [C++ SDK Threading and Concurrency](architecture/CPP_SDK_THREADING_AND_CONCURRENCY.md) | EON-SPEC-CPP-003 | Thread isolation, lock-free queues, thread pool, and cooperative cancellation |
| [C++ SDK Error Handling](architecture/CPP_SDK_ERROR_HANDLING.md) | EON-SPEC-CPP-004 | Exception boundaries, Result monadic error propagation, and recovery actions |
| [C++ SDK ABI Compatibility](architecture/CPP_SDK_ABI_COMPATIBILITY.md) | EON-SPEC-CPP-005 | Pimpl idiom, flat C-ABI bridge header (eon_c.h), and symbol visibility controls |
| [C++ SDK Build and Toolchain](architecture/CPP_SDK_BUILD_AND_TOOLCHAIN.md) | EON-SPEC-CPP-006 | ISO C++17 standard, GCC 11+/Clang 14+/MSVC 2022 support, and ament_cmake integration |
| [C++ SDK Security](architecture/CPP_SDK_SECURITY.md) | EON-SPEC-CPP-007 | IPC socket permissions, SO_PEERCRED credential checks, and memory zeroing |
| [C++ SDK Compatibility Matrix](architecture/CPP_SDK_COMPATIBILITY_MATRIX.md) | EON-SPEC-CPP-008 | OS/compiler matrix and future hardware benchmark protocol (p50, p95, p99) |

#### 1.5.11 ROS 2 Architecture (Sub-phase 2.12)

| Document | Document ID | Description |
|---|---|---|
| [ROS 2 Architecture](architecture/ROS2_ARCHITECTURE.md) | EON-ARCH-ROS-001 | Complete ROS 2 integration architecture, decoupling principles, and middleware topology |
| [ROS 2 Node Specifications](architecture/ROS2_NODE_SPECIFICATIONS.md) | EON-ARCH-ROS-002 | Managed lifecycle node architecture (rclcpp_lifecycle) and bridge node specifications |
| [ROS 2 Topic and Message Contracts](architecture/ROS2_TOPIC_AND_MESSAGE_CONTRACTS.md) | EON-SPEC-ROS-001 | Custom message definitions (eon_msgs) and topic catalog for observations and proposals |
| [ROS 2 Service and Action Contracts](architecture/ROS2_SERVICE_AND_ACTION_CONTRACTS.md) | EON-SPEC-ROS-002 | Custom service and action definitions for state queries and social interactions |
| [ROS 2 QoS Policies](architecture/ROS2_QOS_POLICIES.md) | EON-SPEC-ROS-003 | Quality of Service profiles (SensorData, Reliable Events, TransientLocal Diagnostics) |
| [ROS 2 Lifecycle Integration](architecture/ROS2_LIFECYCLE_INTEGRATION.md) | EON-SPEC-ROS-004 | Bidirectional coordination between rclcpp_lifecycle and EON 7-state operational health |
| [ROS 2 Security and Namespaces](architecture/ROS2_SECURITY_AND_NAMESPACES.md) | EON-SPEC-ROS-005 | SROS 2 / DDS Security, X.509 cert validation, and multi-robot fleet namespacing |
| [ROS 2 Failure Handling](architecture/ROS2_FAILURE_HANDLING.md) | EON-SPEC-ROS-006 | Fail-silent social motion principle, deadline monitoring, and neutral posture fallback |
| [ROS 2 Distribution Compatibility](architecture/ROS2_DISTRIBUTION_COMPATIBILITY.md) | EON-SPEC-ROS-007 | Support policy for ROS 2 Humble (LTS), Iron, and Jazzy (LTS), and standalone independence |

#### 1.5.12 Robot Abstraction Architecture (Sub-phase 2.13)

| Document | Document ID | Description |
|---|---|---|
| [Robot Abstraction Architecture](architecture/ROBOT_ABSTRACTION_ARCHITECTURE.md) | EON-ARCH-ROB-001 | Vendor-neutral Robot Abstraction Layer (RAL) topology and decoupled intelligence |
| [Robot Capability Model](architecture/ROBOT_CAPABILITY_MODEL.md) | EON-SPEC-ROB-001 | Dynamic capability negotiation schema and expressive fallback matrix |
| [Robot Interface Contracts](architecture/ROBOT_INTERFACE_CONTRACTS.md) | EON-SPEC-ROB-002 | C++ abstract interfaces, normalized sensor packets, and proposal structures |
| [Robot Hardware Adapters](architecture/ROBOT_HARDWARE_ADAPTERS.md) | EON-SPEC-ROB-003 | Plugin architecture for ROS 2, gRPC, and shared memory hardware adapters |
| [Robot Sensor Abstraction](architecture/ROBOT_SENSOR_ABSTRACTION.md) | EON-SPEC-ROB-004 | Normalization for cameras, 16kHz microphone arrays, and robot odometry |
| [Robot Actuator Abstraction](architecture/ROBOT_ACTUATOR_ABSTRACTION.md) | EON-SPEC-ROB-005 | Expressive channels (gaze, display, audio, locomotion) and kinematic clamping |
| [Robot Safety Boundaries](architecture/ROBOT_SAFETY_BOUNDARIES.md) | EON-SPEC-ROB-006 | Strict physical safety barrier, non-authoritative invariant, and safety controller primacy |
| [Robot Simulation Architecture](architecture/ROBOT_SIMULATION_ARCHITECTURE.md) | EON-SPEC-ROB-007 | Synthetic evaluation pipeline for NVIDIA Isaac Sim, Gazebo, and Webots |
| [Robot Platform Compatibility](architecture/ROBOT_PLATFORM_COMPATIBILITY.md) | EON-SPEC-ROB-008 | Compatibility tiers for humanoid, wheeled, social desktop, and industrial robots |

#### 1.5.13 Edge Deployment Architecture (Sub-phase 2.14)

| Document | Document ID | Description |
|---|---|---|
| [Edge Deployment Architecture](architecture/EDGE_DEPLOYMENT_ARCHITECTURE.md) | EON-ARCH-EDGE-001 | CPU-first edge packaging, deployment profiles, and runtime stacking |
| [Edge Resource Management](architecture/EDGE_RESOURCE_MANAGEMENT.md) | EON-SPEC-EDGE-001 | Resource budgets by profile (Low-Resource, Standard, Accelerated) and cgroups v2 caps |
| [Edge Installation and Packaging](architecture/EDGE_INSTALLATION_AND_PACKAGING.md) | EON-SPEC-EDGE-002 | Debian/RPM packages, OCI containers, tarballs, and standard filesystem layout |
| [Edge Process Supervision](architecture/EDGE_PROCESS_SUPERVISION.md) | EON-SPEC-EDGE-003 | systemd service specification, sandboxing, and 2.0-second watchdog keepalive |
| [Edge Model Deployment](architecture/EDGE_MODEL_DEPLOYMENT.md) | EON-SPEC-EDGE-004 | ONNX Runtime execution providers (CPU, OpenVINO, TensorRT, QNN) and INT8 quantization |
| [Edge Offline Operation](architecture/EDGE_OFFLINE_OPERATION.md) | EON-SPEC-EDGE-005 | 100% autonomous offline guarantee, local clocking, and zero cloud dependency |
| [Edge Update and Rollback](architecture/EDGE_UPDATE_AND_ROLLBACK.md) | EON-SPEC-EDGE-006 | A/B dual-slot atomic updates, 3-strike bootloader recovery, and SQLite backup |
| [Edge Monitoring and Diagnostics](architecture/EDGE_MONITORING_AND_DIAGNOSTICS.md) | EON-SPEC-EDGE-007 | CLI diagnostics (eon-cli), REST health endpoints, and journald structured logging |
| [Edge Hardware Compatibility](architecture/EDGE_HARDWARE_COMPATIBILITY.md) | EON-SPEC-EDGE-008 | Hardware profiles for Jetson, Intel Core Ultra, AMD Ryzen, Raspberry Pi, Qualcomm |

#### 1.5.14 Optional Cloud Architecture (Sub-phase 2.15)

| Document | Document ID | Description |
|---|---|---|
| [Optional Cloud Architecture](architecture/CLOUD_ARCHITECTURE.md) | EON-ARCH-CLD-001 | Optional cloud control plane topology, fleet telemetry, and local vs. cloud separation |
| [Cloud-Edge Synchronization](architecture/CLOUD_EDGE_SYNCHRONIZATION.md) | EON-SPEC-CLD-001 | Resilient store-and-forward sync queue, vector clocks, and CRDT conflict resolution |
| [Cloud API Gateway](architecture/CLOUD_API_GATEWAY.md) | EON-SPEC-CLD-002 | Envoy API gateway, mTLS robot termination, rate limiting, and tenant routing |
| [Cloud Tenant Isolation](architecture/CLOUD_TENANT_ISOLATION.md) | EON-SPEC-CLD-003 | Logical schema isolation, dedicated tenant DBs, and per-tenant KMS encryption |
| [Cloud Data Storage](architecture/CLOUD_DATA_STORAGE.md) | EON-SPEC-CLD-004 | PostgreSQL context store, TimescaleDB telemetry, and S3 artifact repository |
| [Cloud Identity and Access](architecture/CLOUD_IDENTITY_AND_ACCESS.md) | EON-SPEC-CLD-005 | Device X.509 identities, OAuth2/OIDC operator login, and multi-tenant RBAC |
| [Cloud Failure and Recovery](architecture/CLOUD_FAILURE_AND_RECOVERY.md) | EON-SPEC-CLD-006 | Zero edge degradation on cloud outage and exponential jittered reconnect |
| [Cloud Deployment Options](architecture/CLOUD_DEPLOYMENT_OPTIONS.md) | EON-SPEC-CLD-007 | Public SaaS, private cloud VPC, and on-premises air-gapped hybrid appliances |
| [Cloud Cost and Scalability](architecture/CLOUD_COST_AND_SCALABILITY_MODEL.md) | EON-SPEC-CLD-008 | FinOps cost model (~$1.50/robot/month) and horizontal gateway scaling |

#### 1.5.15 Security Architecture (Sub-phase 2.16)

| Document | Document ID | Description |
|---|---|---|
| [Security Architecture](architecture/SECURITY_ARCHITECTURE.md) | EON-ARCH-SEC-001 | Zero-Trust architecture, five security domains, and three trust boundaries |
| [Security Threat Model](architecture/SECURITY_THREAT_MODEL.md) | EON-SPEC-SEC-001 | STRIDE threat analysis matrix with mitigations and automated verification methods |
| [Security Identity and Authentication](architecture/SECURITY_IDENTITY_AND_AUTHENTICATION.md) | EON-SPEC-SEC-002 | TPM 2.0 device identities, SO_PEERCRED IPC auth, and pseudonymous UUIDs |
| [Security Authorization and RBAC](architecture/SECURITY_AUTHORIZATION_AND_RBAC.md) | EON-SPEC-SEC-003 | Capability-based authorization model and default component role assignments |
| [Security Key Management](architecture/SECURITY_KEY_MANAGEMENT.md) | EON-SPEC-SEC-004 | Two-tier envelope encryption (TPM KEK + per-subject DEKs) and shredding |
| [Security Secure Communication](architecture/SECURITY_SECURE_COMMUNICATION.md) | EON-SPEC-SEC-005 | Transport encryption standards (IPC memory isolation, SROS 2, TLS 1.3) |
| [Security Secrets Management](architecture/SECURITY_SECRETS_MANAGEMENT.md) | EON-SPEC-SEC-006 | Zero hardcoded secrets, TPM sealing, and mlock/explicit_bzero memory hygiene |
| [Security Audit and Logging](architecture/SECURITY_AUDIT_AND_LOGGING.md) | EON-SPEC-SEC-007 | Tamper-evident append-only SHA-256 hash-chained audit trail and log redaction |
| [Security Supply Chain](architecture/SECURITY_SUPPLY_CHAIN.md) | EON-SPEC-SEC-008 | CycloneDX/SPDX SBOM generation, Cosign artifact signing, and CVE scanning |
| [Security Incident Response](architecture/SECURITY_INCIDENT_RESPONSE.md) | EON-SPEC-SEC-009 | Robotic fleet compromise containment, key revocation, and forensic readiness |

#### 1.5.16 Privacy Architecture (Sub-phase 2.17)

| Document | Document ID | Description |
|---|---|---|
| [Privacy Architecture](architecture/PRIVACY_ARCHITECTURE.md) | EON-ARCH-PRIV-001 | Privacy-by-design framework, epistemic modesty, and four non-negotiable pillars |
| [Privacy Consent Model](architecture/PRIVACY_CONSENT_MODEL.md) | EON-SPEC-PRIV-001 | 3-tier consent model (Anonymous, Ephemeral Session, Consented Personalization) |
| [Privacy Data Classification](architecture/PRIVACY_DATA_CLASSIFICATION.md) | EON-SPEC-PRIV-002 | Five-tier data sensitivity taxonomy and volatile vs. encrypted storage rules |
| [Privacy Data Minimization](architecture/PRIVACY_DATA_MINIMIZATION.md) | EON-SPEC-PRIV-003 | Dimension reduction, landmark extraction, and strict purpose limitation |
| [Privacy Retention and Deletion](architecture/PRIVACY_RETENTION_AND_DELETION.md) | EON-SPEC-PRIV-004 | Truth-in-specification regarding SSD wear-leveling and mathematical shredding |
| [Privacy Context Isolation](architecture/PRIVACY_CONTEXT_ISOLATION.md) | EON-SPEC-PRIV-005 | Subject context memory boundaries and automated session expiration |
| [Privacy Media Processing](architecture/PRIVACY_MEDIA_PROCESSING.md) | EON-SPEC-PRIV-006 | Ephemeral volatile ring buffers (/dev/shm) and recording indicator LED policy |
| [Privacy Audit and Transparency](architecture/PRIVACY_AUDIT_AND_TRANSPARENCY.md) | EON-SPEC-PRIV-007 | Right of access data exports and immutable privacy audit logging |
| [Privacy Cloud Synchronization](architecture/PRIVACY_CLOUD_SYNCHRONIZATION.md) | EON-SPEC-PRIV-008 | Unbypassable edge privacy filter dropping raw media and geographic pinning |
| [Privacy Verification Requirements](architecture/PRIVACY_VERIFICATION_REQUIREMENTS.md) | EON-SPEC-PRIV-009 | Automated test procedures for zero disk media and cryptographic shredding |

#### 1.5.17 Architecture Decision Records (`docs/architecture/decisions/`)

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
| [ADR-013](architecture/decisions/ADR-013-engine-lifecycle-contract.md) | Engine Lifecycle Contract Protocol | Approved | 11-state engine lifecycle FSM and 7-state operational health projection |
| [ADR-014](architecture/decisions/ADR-014-event-driven-communication-and-delivery-guarantees.md) | Event-Driven Communication and Delivery Guarantees | Approved | Bounded message broker, topic taxonomy, and QoS |
| [ADR-015](architecture/decisions/ADR-015-shared-context-and-access-control.md) | Shared Context Architecture & Access Control | Approved | Optimistic concurrency and capability-scoped contexts |
| [ADR-016](architecture/decisions/ADR-016-provider-neutral-model-adapter-architecture.md) | Provider-Neutral Model Adapter Architecture | Approved | Hardware abstraction, multi-backend routing, and fallback |
| [ADR-017](architecture/decisions/ADR-017-edge-storage-and-data-governance.md) | Edge Data Architecture, Storage & Retention | Approved | Multi-engine edge storage, AES-256-GCM, and shredding |
| [ADR-018](architecture/decisions/ADR-018-api-architecture-and-security.md) | API Gateway Architecture, Protocol & Security | Approved | Northbound API Gateway, OpenAPI 3.1, and token bucket |
| [ADR-019](architecture/decisions/ADR-019-python-sdk-architecture.md) | Dual-Mode Synchronous/Asynchronous Python SDK | Approved | Local in-process and remote client modes, strong typing |
| [ADR-020](architecture/decisions/ADR-020-cpp-sdk-architecture.md) | Native C++ SDK Architecture (libeonsdk) | Approved | ISO C++17, Pimpl ABI stability, and zero-copy SHM |
| [ADR-021](architecture/decisions/ADR-021-ros2-integration-strategy.md) | ROS 2 Decoupled Integration Strategy | Approved | Decoupled eon_ros2_bridge, lifecycle nodes, and SROS 2 |
| [ADR-022](architecture/decisions/ADR-022-hardware-independent-robot-abstraction.md) | Robot Abstraction Layer (RAL) | Approved | Vendor-neutral abstraction, capability negotiation, and safety gate |
| [ADR-023](architecture/decisions/ADR-023-edge-deployment-and-process-supervision.md) | Edge Deployment & Process Supervision | Approved | CPU-first edge profiles, systemd watchdog, cgroups v2, and A/B updates |
| [ADR-024](architecture/decisions/ADR-024-optional-cloud-architecture-and-sync.md) | Optional Cloud Architecture & Sync | Approved | 100% offline edge autonomy, CRDT sync, and multi-tenancy |
| [ADR-025](architecture/decisions/ADR-025-zero-trust-security-and-stride-threat-model.md) | Zero-Trust Security & STRIDE Model | Approved | 5 security domains, STRIDE mitigations, and TPM/DEK envelope crypto |
| [ADR-026](architecture/decisions/ADR-026-privacy-by-design-and-cryptographic-boundaries.md) | Privacy-by-Design & Cryptographic Boundaries | Approved | Zero raw media persistence, epistemic modesty, and mathematical shredding |
| [ADR-027](architecture/decisions/ADR-027-dual-runtime-interoperability-python-cpp.md) | Dual-Runtime Interoperability (Python & C++) | Approved | Unified event schemas, 7-state health model, and benchmark protocols |
| [ADR-028](architecture/decisions/ADR-028-failure-containment-and-resilience-model.md) | Failure Containment & Resilience Model | Approved | Fail-silent social motion, priority queue drops, and worker restarts |

#### 1.5.18 System Architecture Visual Suite (`docs/architecture/diagrams/`)

| Diagram File | Description |
|---|---|
| [COMPLETE_SYSTEM_ARCHITECTURE.mmd](architecture/diagrams/COMPLETE_SYSTEM_ARCHITECTURE.mmd) | End-to-end system context from human environment to robot actuators |
| [COMPLETE_COMPONENT_ARCHITECTURE.mmd](architecture/diagrams/COMPLETE_COMPONENT_ARCHITECTURE.mmd) | 5-layer component architecture from OS to application layer |
| [SEVEN_ENGINE_INTERACTION.mmd](architecture/diagrams/SEVEN_ENGINE_INTERACTION.mmd) | Information flow across ERS, EMS, ERE, PSE, SIE, ERG, HBU |
| [EON_CORE_INTERNAL_ARCHITECTURE.mmd](architecture/diagrams/EON_CORE_INTERNAL_ARCHITECTURE.mmd) | Internal subsystems of eond (IPC, Bus, Context, Lifecycle, Adapters) |
| [CPP_SDK_ARCHITECTURE.mmd](architecture/diagrams/CPP_SDK_ARCHITECTURE.mmd) | Public API, Pimpl barrier, C-ABI bridge, and private threading core |
| [PYTHON_CPP_INTEROPERABILITY.mmd](architecture/diagrams/PYTHON_CPP_INTEROPERABILITY.mmd) | Cross-language contracts, shared schemas, and FFI bridging |
| [ROS2_INTEGRATION_ARCHITECTURE.mmd](architecture/diagrams/ROS2_INTEGRATION_ARCHITECTURE.mmd) | ROS 2 middleware graph, managed lifecycle nodes, and topics |
| [ROBOT_ABSTRACTION_ARCHITECTURE.mmd](architecture/diagrams/ROBOT_ABSTRACTION_ARCHITECTURE.mmd) | RAL sensors, capability manifests, expressive fallback, and safety |
| [EDGE_DEPLOYMENT_ARCHITECTURE.mmd](architecture/diagrams/EDGE_DEPLOYMENT_ARCHITECTURE.mmd) | Host hardware, Linux OS, cgroups v2, and runtime sandboxes |
| [CLOUD_EDGE_ARCHITECTURE.mmd](architecture/diagrams/CLOUD_EDGE_ARCHITECTURE.mmd) | Edge autonomous domain and optional cloud control plane |
| [SECURITY_TRUST_BOUNDARIES.mmd](architecture/diagrams/SECURITY_TRUST_BOUNDARIES.mmd) | Trust Boundaries A, B, C across five security domains |
| [PRIVACY_DATA_FLOW.mmd](architecture/diagrams/PRIVACY_DATA_FLOW.mmd) | Ephemeral volatile media processing, 3-tier consent, and shredding |
| [EVENT_COMMUNICATION_ARCHITECTURE.mmd](architecture/diagrams/EVENT_COMMUNICATION_ARCHITECTURE.mmd) | Priority lanes (CRITICAL to LOW), queues, and DROP_OLDEST policy |
| [ENGINE_LIFECYCLE_STATE_MACHINE.mmd](architecture/diagrams/ENGINE_LIFECYCLE_STATE_MACHINE.mmd) | Full 11-State internal FSM transitions and failure containment |
| [FAILURE_ISOLATION_ARCHITECTURE.mmd](architecture/diagrams/FAILURE_ISOLATION_ARCHITECTURE.mmd) | Fault triggers, containment boundaries, and fail-silent robotics contract |
| [DATA_STORAGE_AND_RETENTION.mmd](architecture/diagrams/DATA_STORAGE_AND_RETENTION.mmd) | Volatile RAM vs. LUKS disk, envelope encryption, and WAL truncation |
| [COMPLETE_DEPLOYMENT_TOPOLOGY.mmd](architecture/diagrams/COMPLETE_DEPLOYMENT_TOPOLOGY.mmd) | Physical robot enclosure, compute edge, safety MCU, and sensors |
| [SYSTEM_STARTUP_AND_SHUTDOWN.mmd](architecture/diagrams/SYSTEM_STARTUP_AND_SHUTDOWN.mmd) | Deterministic sequence diagram for service startup and clean exit |

#### 1.5.19 Scalability, Failure Isolation, and Resilience Review (Sub-phase 2.20)

| Document | Document ID | Description |
|---|---|---|
| [Architecture Scalability Review](architecture/ARCHITECTURE_SCALABILITY_REVIEW.md) | EON-REV-SCAL-001 | Single-robot, multi-user, and fleet scalability modeling |
| [Architecture Failure Isolation Review](architecture/ARCHITECTURE_FAILURE_ISOLATION_REVIEW.md) | EON-REV-FAIL-001 | 18 deterministic failure scenarios, triggers, containment, and recovery |
| [Architecture Resource Budgets](architecture/ARCHITECTURE_RESOURCE_BUDGETS.md) | EON-SPEC-BUD-001 | Resource budgets across Low-Resource, Standard, and Accelerated tiers |
| [Architecture Bottleneck Analysis](architecture/ARCHITECTURE_BOTTLENECK_ANALYSIS.md) | EON-REV-BOT-001 | Analysis of perception serialization, GIL, WAL, and thermal limits |
| [Architecture Resilience Model](architecture/ARCHITECTURE_RESILIENCE_MODEL.md) | EON-REV-RES-001 | Four-layer resilience model (Prevention, Detection, Degradation, Recovery) |
| [Architecture Risk Register](architecture/ARCHITECTURE_RISK_REGISTER.md) | EON-REG-RISK-001 | Systemic risk register with 8 systemic risks and architectural mitigations |
| [Architecture Implementation Readiness](architecture/ARCHITECTURE_IMPLEMENTATION_READINESS.md) | EON-REV-READY-001 | Subsystem readiness audit confirming readiness for Phase 3 engineering |
| [Architecture Acceptance Matrix](architecture/ARCHITECTURE_ACCEPTANCE_MATRIX.md) | EON-REG-ACCP-001 | Traceability verification for all core architectural acceptance criteria |

#### 1.5.20 Phase 2 Architectural Qualification Reports

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
| [Phase 2.11 Qualification Report](architecture/PHASE_2_11_QUALIFICATION_REPORT.md) | EON-QUAL-PH2.11-001 | Architecture qualification report for Sub-phase 2.11 (C++ SDK) |
| [Phase 2.12 Qualification Report](architecture/PHASE_2_12_QUALIFICATION_REPORT.md) | EON-QUAL-PH2.12-001 | Architecture qualification report for Sub-phase 2.12 (ROS 2 Architecture) |
| [Phase 2.13 Qualification Report](architecture/PHASE_2_13_QUALIFICATION_REPORT.md) | EON-QUAL-PH2.13-001 | Architecture qualification report for Sub-phase 2.13 (Robot Abstraction) |
| [Phase 2.14 Qualification Report](architecture/PHASE_2_14_QUALIFICATION_REPORT.md) | EON-QUAL-PH2.14-001 | Architecture qualification report for Sub-phase 2.14 (Edge Deployment) |
| [Phase 2.15 Qualification Report](architecture/PHASE_2_15_QUALIFICATION_REPORT.md) | EON-QUAL-PH2.15-001 | Architecture qualification report for Sub-phase 2.15 (Optional Cloud) |
| [Phase 2.16 Qualification Report](architecture/PHASE_2_16_QUALIFICATION_REPORT.md) | EON-QUAL-PH2.16-001 | Architecture qualification report for Sub-phase 2.16 (Security Architecture) |
| [Phase 2.17 Qualification Report](architecture/PHASE_2_17_QUALIFICATION_REPORT.md) | EON-QUAL-PH2.17-001 | Architecture qualification report for Sub-phase 2.17 (Privacy Architecture) |
| [Phase 2.18 Qualification Report](architecture/PHASE_2_18_QUALIFICATION_REPORT.md) | EON-QUAL-PH2.18-001 | Architecture qualification report for Sub-phase 2.18 (Architecture Decisions) |
| [Phase 2.19 Qualification Report](architecture/PHASE_2_19_QUALIFICATION_REPORT.md) | EON-QUAL-PH2.19-001 | Architecture qualification report for Sub-phase 2.19 (System Diagrams) |
| [Phase 2.20 Qualification Report](architecture/PHASE_2_20_QUALIFICATION_REPORT.md) | EON-QUAL-PH2.20-001 | Architecture qualification report for Sub-phase 2.20 (Scalability & Failure Isolation) |
| [Phase 2.3–2.10 Architecture Correction Audit](architecture/PHASE_2_3_TO_2_10_CORRECTION_AUDIT.md) | EON-AUDIT-PH2-001 | Defect audit, reconciliation, and requalification report for Sub-phases 2.3–2.10 |
| [Phase 2.3–2.10 Master Qualification Report](architecture/PHASE_2_3_TO_2_10_FINAL_QUALIFICATION_REPORT.md) | EON-QUAL-PH2-FINAL-001 | Master consolidated qualification report for Sub-phases 2.3 through 2.10 |
| [Phase 2.11–2.20 Final Consolidated Qualification Report](architecture/PHASE_2_11_TO_2_20_FINAL_QUALIFICATION_REPORT.md) | EON-QUAL-PH2-FINAL-002 | Master consolidated qualification report for Sub-phases 2.11 through 2.20 |

#### 1.5.21 Complete Architecture Audit and Requalification Reports (`docs/audit/`)

| Document | Document ID | Description |
|---|---|---|
| [Phase 2 Deliverables Inventory](audit/PHASE_2_11_TO_2_20_AUDIT_INVENTORY.md) | `EON-AUDIT-INV-001` | Complete 111-file deliverables register, audit status, and action plan |
| [Privacy Deletion Claims Audit](audit/PRIVACY_DELETION_CLAIMS_AUDIT.md) | `EON-AUDIT-PRIV-001` | Multi-tier deletion lifecycle, SSD wear-leveling realities, and 12-class taxonomy |
| [ROS 2 Compatibility Audit](audit/ROS2_COMPATIBILITY_AUDIT.md) | `EON-AUDIT-ROS2-001` | Reclassification of ROS 2 Iron as EOL/Legacy; Tier 1 Humble/Jazzy qualification |
| [Documentation Consistency Audit](audit/DOCUMENTATION_CONSISTENCY_AUDIT.md) | `EON-AUDIT-DOC-001` | Comprehensive README, index, and cross-reference reconciliation audit |
| [Commit and Qualification Evidence Audit](audit/COMMIT_AND_QUALIFICATION_EVIDENCE_AUDIT.md) | `EON-AUDIT-EVD-001` | Git history verification, CI workflow IDs, and empirical evidence integrity |
| [Edge Resource Budget Audit](audit/EDGE_RESOURCE_BUDGET_AUDIT.md) | `EON-AUDIT-RES-001` | 2GB memory cap breakdown, profiles A/B/C, and reproducible benchmark protocol |
| [Full Phase 2 Architecture Consistency Audit](audit/PHASE_2_FULL_ARCHITECTURE_CONSISTENCY_AUDIT.md) | `EON-AUDIT-CONSIST-001` | Cross-cutting audit of state models, API catalogs, RAL safety, and diagrams |
| [Phase 2 Requirements Traceability Matrix](audit/PHASE_2_REQUIREMENTS_TRACEABILITY.md) | `EON-AUDIT-RTM-001` | Complete traceability mapping from PRD/SRS requirements to Phase 2 architecture |
| [Phase 2 Final Requalification Report](audit/PHASE_2_FINAL_REQUALIFICATION_REPORT.md) | `EON-QUAL-PH2-FINAL-003` | Master Phase 2 requalification report and unconditional acceptance decision |

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
