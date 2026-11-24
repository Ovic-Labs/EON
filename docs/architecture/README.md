# OVIC EON — Architecture Documentation Index

**Document ID:** `EON-INDEX-ARCH-001`  
**Phase:** Phase 2 — System Architecture and Engineering Design (Sub-phases 2.1–2.20)  
**Status:** `QUALIFIED — ACCEPTED (Architecture Baseline)`  
**Target Audience:** System Architects, Core Developers, Robotics Integrators, Security Auditors  
**Related Documents:**  
- Root Documentation Index: [docs/README.md](../README.md)  
- Audit Inventory: [docs/audit/PHASE_2_11_TO_2_20_AUDIT_INVENTORY.md](../audit/PHASE_2_11_TO_2_20_AUDIT_INVENTORY.md)  
- Master Requalification Report: [docs/audit/PHASE_2_FINAL_REQUALIFICATION_REPORT.md](../audit/PHASE_2_FINAL_REQUALIFICATION_REPORT.md)  

---

## 1. Executive Summary

This index catalogues the complete, implementation-ready architecture baseline for **OVIC EON (Emotional Intelligence Infrastructure for Robotics)**, encompassing all twenty Phase 2 sub-phases (Sub-phases 2.1 through 2.20), 28 Architecture Decision Records (ADRs), 18 system visual diagrams, and comprehensive requalification audit reports.

Phase 2 establishes the structural, computational, cryptographic, and middleware foundations of EON. In accordance with project governance, all specifications represent **DESIGNED — NOT IMPLEMENTED** architecture baselines, with runtime engine implementations planned for Phase 3.

---

## 2. Phase 2 Architecture Deliverables Register

### 2.1 Foundations & Layered Architecture (Sub-phases 2.1 & 2.2)

| Document | Description |
|---|---|
| [System Layered Architecture](SYSTEM_LAYERED_ARCHITECTURE.md) | Ten-tier layered architecture model, layer evaluations, and data flows |
| [Inter-Layer Interfaces](INTER_LAYER_INTERFACES.md) | Strongly typed interfaces, SPIs, buffer contracts, and cross-layer boundaries |
| [Architecture Constraints](ARCHITECTURE_CONSTRAINTS.md) | Non-negotiable architectural invariants (DAG, safety, privacy, CPU-first) |
| [Seven Engine Architecture](SEVEN_ENGINE_ARCHITECTURE.md) | Seven intelligence engines overview, mission roster, and coordination model |
| [Engine Boundary Specifications](ENGINE_BOUNDARY_SPECIFICATIONS.md) | Complete 27-item boundary specifications for all seven intelligence engines |
| [Engine Dependency Matrix](ENGINE_DEPENDENCY_MATRIX.md) | Authoritative 7x7 engine interaction matrix, event dependencies, and DAG |
| [Engine Input/Output Contracts](ENGINE_INPUT_OUTPUT_CONTRACTS.md) | Schema mapping, existing Phase 1.2 contracts, and proposed Phase 2 schemas |

### 2.2 Core Runtime, Lifecycle & Event Bus (Sub-phases 2.3–2.5)

| Document | Description |
|---|---|
| [EON Core Architecture](EON_CORE_ARCHITECTURE.md) | Core daemon, process isolation, supervisor tree, and engine orchestration |
| [EON Core Components](EON_CORE_COMPONENTS.md) | Component breakdown of the EON Core execution runtime |
| [EON Core State Model](EON_CORE_STATE_MODEL.md) | 11-state core operational lifecycle state machine |
| [EON Core Initialization](EON_CORE_INITIALIZATION.md) | Deterministic startup sequence, configuration loading, and health validation |
| [EON Core Failure Handling](EON_CORE_FAILURE_HANDLING.md) | Hierarchical fault recovery, fallback mechanisms, and graceful termination |
| [Engine Lifecycle Architecture](ENGINE_LIFECYCLE_ARCHITECTURE.md) | Engine-specific state machine and transition hooks |
| [Engine Lifecycle Contract](ENGINE_LIFECYCLE_CONTRACT.md) | Formal interface contracts for engine state transitions |
| [Engine State Transitions](ENGINE_STATE_TRANSITIONS.md) | State transition rules and validation hooks |
| [Engine Recovery & Failure Policies](ENGINE_RECOVERY_AND_FAILURE_POLICIES.md) | Fault policies, restart limits, and fail-silent shutdown |
| [Engine Resource Declarations](ENGINE_RESOURCE_DECLARATIONS.md) | Memory and CPU quotas declared per engine |
| [Event-Driven Communication](EVENT_DRIVEN_COMMUNICATION.md) | Asynchronous pub/sub architecture, delivery guarantees, and backpressure |
| [Core Event Bus Architecture](CORE_EVENT_BUS_ARCHITECTURE.md) | In-memory asynchronous event bus architecture, priority queues, and lifecycle |
| [Event Envelope Specification](EVENT_ENVELOPE_SPECIFICATION.md) | Universal EventEnvelope[T] specification, causality tracking, and sequence flows |
| [Event Taxonomy](EVENT_TAXONOMY.md) | Categorization and hierarchy of event types |
| [Event Routing & Delivery](EVENT_ROUTING_AND_DELIVERY.md) | Snapshot-based routing, exact and wildcard subscriptions, and delivery outcomes |
| [Event Delivery & Reliability](EVENT_DELIVERY_AND_RELIABILITY.md) | QoS levels, at-least-once delivery, and acknowledgement mechanisms |
| [Event Security & Privacy](EVENT_SECURITY_AND_PRIVACY.md) | Event payload sanitization, encryption, and topic isolation |
| [Backpressure & Priority Policy](BACKPRESSURE_AND_PRIORITY_POLICY.md) | Backpressure policies (WAIT, REJECT, DROP), priority scheduling, and starvation |

### 2.3 Context, Models & Data (Sub-phases 2.6–2.8)

| Document | Description |
|---|---|
| [Shared Context Architecture](SHARED_CONTEXT_ARCHITECTURE.md) | Hierarchical context bus, working memory, and persistent episodic store |
| [Context Data Model](CONTEXT_DATA_MODEL.md) | 8-category context taxonomy and typed data schemas |
| [Context Lifecycle](CONTEXT_LIFECYCLE.md) | Lifecycle of context items from creation to decay and eviction |
| [Context Access Control](CONTEXT_ACCESS_CONTROL.md) | Least-privilege engine access control matrix (EMS sole persistent writer) |
| [Context Conflict Resolution](CONTEXT_CONFLICT_RESOLUTION.md) | Resolution strategies for competing context updates |
| [Context Privacy & Retention Policy](CONTEXT_PRIVACY_AND_RETENTION.md) | Volatile scrubbing, presence timeouts (120s), and cryptographic deletion |
| [Model Adapter Architecture](MODEL_ADAPTER_ARCHITECTURE.md) | Modular pluggable model adapter interface isolating ONNX Runtime |
| [Model Adapter Interface Specification](MODEL_ADAPTER_INTERFACE_SPECIFICATION.md) | Standard C++ / Python model abstraction contracts |
| [Model Lifecycle](MODEL_LIFECYCLE.md) | Lifecycle management for neural network models |
| [Model Runtime Compatibility](MODEL_RUNTIME_COMPATIBILITY.md) | Compatibility matrix across CPU, GPU, and NPU execution providers |
| [Model Provenance & Governance](MODEL_PROVENANCE_AND_GOVERNANCE.md) | Model lineage, license validation, and weight checksum verification |
| [Data Architecture](DATA_ARCHITECTURE.md) | Relational, vector, timeseries, and volatile memory storage strategies |
| [Data Schema Architecture](DATA_SCHEMA_ARCHITECTURE.md) | Foundational data contracts, Pydantic v2 architecture, and security boundaries |
| [Data Storage Strategy](DATA_STORAGE_STRATEGY.md) | Embedded SQLite WAL, in-memory tmpfs, and zero raw media persistence |
| [Data Domain Model](DATA_DOMAIN_MODEL.md) | Domain entity relationships and schema definitions |
| [Data Schema Versioning & Migrations](DATA_SCHEMA_VERSIONING_AND_MIGRATIONS.md) | SemVer 2.0.0 compatibility rules, breaking change classifications, and migrations |
| [Data Security Policy](DATA_SECURITY.md) | SQLCipher AES-256-GCM encryption at rest and key derivation |
| [Data Privacy & Retention Policy](DATA_PRIVACY_AND_RETENTION.md) | Multi-tier deletion lifecycle, WAL checkpointing, and truth-in-specification |

### 2.4 APIs & SDKs (Sub-phases 2.9–2.11)

| Document | Description |
|---|---|
| [API Architecture](API_ARCHITECTURE.md) | Unified edge API gateway supporting REST, WebSockets, and Unix Domain Sockets |
| [API Endpoint Catalog](API_ENDPOINT_CATALOG.md) | Authoritative catalog of 11 REST endpoints and 1 bidirectional WebSocket |
| [API Authentication & Authorization](API_AUTHENTICATION_AND_AUTHORIZATION.md) | Mutual TLS, bearer tokens, RBAC roles, and rate limiting |
| [API Error & Reliability Contract](API_ERROR_AND_RELIABILITY_CONTRACT.md) | Standardized error payloads and retry semantics |
| [API Versioning & Compatibility](API_VERSIONING_AND_COMPATIBILITY.md) | API versioning policies and backward compatibility guarantees |
| [API Security](API_SECURITY.md) | Security controls, TLS configuration, and input validation |
| [Python SDK Architecture](PYTHON_SDK_ARCHITECTURE.md) | High-level ergonomic Python client library architecture (eon-sdk) |
| [Python SDK API Contracts](PYTHON_SDK_API_CONTRACTS.md) | Public classes, asynchronous context managers, and type annotations |
| [Python SDK Package Structure](PYTHON_SDK_PACKAGE_STRUCTURE.md) | Package layout, modular optional dependencies ([ros2], [grpc]) |
| [Python SDK Compatibility](PYTHON_SDK_COMPATIBILITY.md) | CPython 3.10–3.12 compatibility matrix and OS platform tiers |
| [Python SDK Error Handling](PYTHON_SDK_ERROR_HANDLING.md) | Error types, hierarchy, and exception handling patterns |
| [Python SDK Auth & Security](PYTHON_SDK_AUTHENTICATION_AND_SECURITY.md) | Credential management, environment variable precedence, and token refresh |
| [C++ SDK Architecture](CPP_SDK_ARCHITECTURE.md) | Native, deterministic, zero-copy C++17 client library (libeonsdk) |
| [C++ SDK API Contracts](CPP_SDK_API_CONTRACTS.md) | Public C++ interface headers, RAII handles, and Pimpl boundaries |
| [C++ SDK Build & Toolchain](CPP_SDK_BUILD_AND_TOOLCHAIN.md) | CMake 3.22+ configuration, compiler flags, and ament_cmake exports |
| [C++ SDK Package Structure](CPP_SDK_PACKAGE_STRUCTURE.md) | Directory layout and target naming conventions |
| [C++ SDK Compatibility Matrix](CPP_SDK_COMPATIBILITY_MATRIX.md) | Compiler and platform compatibility for C++ SDK |
| [C++ SDK Memory Management](CPP_SDK_MEMORY_MANAGEMENT.md) | POSIX shared memory ring buffers and zero-copy lockless ring queues |
| [C++ SDK Threading & Concurrency](CPP_SDK_THREADING_AND_CONCURRENCY.md) | Deterministic worker thread pools and non-blocking callback dispatch |
| [C++ SDK Error Handling](CPP_SDK_ERROR_HANDLING.md) | Strongly-typed C++ error codes and non-throwing exception boundaries |
| [C++ SDK ABI Compatibility](CPP_SDK_ABI_COMPATIBILITY.md) | Stable C ABI (libeon_c.so) for cross-language FFI integration |
| [C++ SDK Security](CPP_SDK_SECURITY.md) | IPC permissions, memory protection, and secure zeroization |

### 2.5 Robotics Middleware, Hardware & Deployment (Sub-phases 2.12–2.15)

| Document | Description |
|---|---|
| [ROS 2 Architecture](ROS2_ARCHITECTURE.md) | Optional eon_ros2_bridge package bridging ROS 2 DDS to EON Core IPC |
| [ROS 2 Node Specifications](ROS2_NODE_SPECIFICATIONS.md) | Specification of SensorBridgeNode, ResponseBridgeNode, LifecycleManager |
| [ROS 2 Topic & Message Contracts](ROS2_TOPIC_AND_MESSAGE_CONTRACTS.md) | Custom eon_msgs topic definitions (proposals, observations) |
| [ROS 2 Service & Action Contracts](ROS2_SERVICE_AND_ACTION_CONTRACTS.md) | Synchronous service and long-running action definitions |
| [ROS 2 QoS Policies](ROS2_QOS_POLICIES.md) | Tailored QoS profiles for lossy high-frequency sensor data vs reliable proposals |
| [ROS 2 Lifecycle Integration](ROS2_LIFECYCLE_INTEGRATION.md) | Mapping of rclcpp_lifecycle states to EON 7-state operational health |
| [ROS 2 Security & Namespaces](ROS2_SECURITY_AND_NAMESPACES.md) | SROS 2 enclave isolation, node namespaces, and multi-robot domain IDs |
| [ROS 2 Failure Handling](ROS2_FAILURE_HANDLING.md) | Fail-silent proposal withholding, neutral resting poses on bridge fault |
| [ROS 2 Distribution Compatibility](ROS2_DISTRIBUTION_COMPATIBILITY.md) | Tier 1 (Humble, Jazzy), Tier 2 (Kilted), Rolling, and Legacy/EOL (Iron) |
| [Robot Abstraction Architecture](ROBOT_ABSTRACTION_ARCHITECTURE.md) | Robot Abstraction Layer (RAL) isolating EON from physical chassis kinematics |
| [Robot Capability Model](ROBOT_CAPABILITY_MODEL.md) | Formal declarations of robot actuator and sensor capabilities |
| [Robot Sensor Abstraction](ROBOT_SENSOR_ABSTRACTION.md) | Abstract interfaces for visual, auditory, and tactile sensors |
| [Robot Actuator Abstraction](ROBOT_ACTUATOR_ABSTRACTION.md) | Normalized social motion targets (head gaze, torso orient, arm gesture) |
| [Robot Safety Boundaries](ROBOT_SAFETY_BOUNDARIES.md) | Strict non-authoritative boundary (is_authoritative = false), velocity clamping |
| [Robot Platform Compatibility](ROBOT_PLATFORM_COMPATIBILITY.md) | Compatibility matrix across humanoid, mobile, and social robot platforms |
| [Hardware Capability Abstraction](HARDWARE_CAPABILITY_ABSTRACTION.md) | Low-level hardware capability discovery and abstraction |
| [Robot Hardware Adapters](ROBOT_HARDWARE_ADAPTERS.md) | Architecture for writing vendor-specific robot chassis adapters |
| [Robot Interface Contracts](ROBOT_INTERFACE_CONTRACTS.md) | Formal interface specifications between RAL and EON Core |
| [Robot Simulation Architecture](ROBOT_SIMULATION_ARCHITECTURE.md) | Gazebo and Isaac Sim simulation integration architecture |
| [Edge Deployment Architecture](EDGE_DEPLOYMENT_ARCHITECTURE.md) | Edge compute architecture, cgroups resource controls, and systemd daemons |
| [Edge Hardware Compatibility](EDGE_HARDWARE_COMPATIBILITY.md) | Hardware support tiers across x86_64 and ARM64 edge SBCs |
| [Edge Resource Management](EDGE_RESOURCE_MANAGEMENT.md) | Strict 2GB memory cap, 150% CPU limit, and subsystem allocation quotas |
| [Edge Process Supervision](EDGE_PROCESS_SUPERVISION.md) | systemd service units, watchdog integration, and auto-restart policies |
| [Edge Model Deployment](EDGE_MODEL_DEPLOYMENT.md) | Model packaging, quantization, and on-device runtime optimization |
| [Edge Offline Operation](EDGE_OFFLINE_OPERATION.md) | 100% autonomous operation in network-denied / air-gapped environments |
| [Edge & Cloud Data Synchronization](EDGE_AND_CLOUD_DATA_SYNCHRONIZATION.md) | Bidirectional synchronization architecture between edge and cloud |
| [Edge Monitoring & Diagnostics](EDGE_MONITORING_AND_DIAGNOSTICS.md) | On-device health checks, telemetry aggregation, and diagnostics |
| [Edge Update & Rollback](EDGE_UPDATE_AND_ROLLBACK.md) | Atomic A/B updates and automated rollback mechanisms |
| [Edge Installation & Packaging](EDGE_INSTALLATION_AND_PACKAGING.md) | Debian packaging (.deb), standalone tarballs, and OCI container images |
| [Cloud Architecture](CLOUD_ARCHITECTURE.md) | Optional fleet synchronization, remote diagnostics, and model distribution |
| [Cloud Deployment Options](CLOUD_DEPLOYMENT_OPTIONS.md) | Kubernetes, serverless, and multi-cloud deployment topologies |
| [Cloud Edge Synchronization](CLOUD_EDGE_SYNCHRONIZATION.md) | Store-and-forward outbox synchronization over TLS with backoff |
| [Cloud Data Storage](CLOUD_DATA_STORAGE.md) | Multi-tenant cloud storage for telemetry and aggregates |
| [Cloud Tenant Isolation](CLOUD_TENANT_ISOLATION.md) | Logical and physical isolation policies for multi-robot fleets |
| [Cloud API Gateway](CLOUD_API_GATEWAY.md) | External API gateway for fleet telemetry and configuration |
| [Cloud Identity & Access](CLOUD_IDENTITY_AND_ACCESS.md) | IAM policies, fleet authentication, and OAuth2 integration |
| [Cloud Cost & Scalability Model](CLOUD_COST_AND_SCALABILITY_MODEL.md) | Cloud resource modeling and cost optimization |
| [Cloud Failure & Recovery](CLOUD_FAILURE_AND_RECOVERY.md) | Disaster recovery, regional failover, and zero edge impact |

### 2.6 Security, Privacy & Ethics (Sub-phases 2.16 & 2.17)

| Document | Description |
|---|---|
| [Security Architecture](SECURITY_ARCHITECTURE.md) | Zero-trust edge security architecture and cryptographic trust root |
| [Security Threat Model](SECURITY_THREAT_MODEL.md) | STRIDE threat model evaluating edge robotics threat vectors |
| [Security Identity & Authentication](SECURITY_IDENTITY_AND_AUTHENTICATION.md) | Device identity, mTLS certificates, and API key management |
| [Security Authorization & RBAC](SECURITY_AUTHORIZATION_AND_RBAC.md) | Role-based access control policies for local and remote clients |
| [Security Key Management](SECURITY_KEY_MANAGEMENT.md) | Two-tier envelope encryption (TPM KEK -> per-subject DEK) and memory locking |
| [Security Secrets Management](SECURITY_SECRETS_MANAGEMENT.md) | Secure storage of credentials in Linux keyring or hardware keystores |
| [Security Secure Communication](SECURITY_SECURE_COMMUNICATION.md) | TLS 1.3 transport encryption and Unix domain socket access rules |
| [Security Audit & Logging](SECURITY_AUDIT_AND_LOGGING.md) | Security event logging and tamper-evident audit trails |
| [Security Supply Chain](SECURITY_SUPPLY_CHAIN.md) | SBOM generation (CycloneDX), dependency vulnerability scanning |
| [Security Incident Response](SECURITY_INCIDENT_RESPONSE.md) | Vulnerability disclosure policies, patch response timelines, and SLAs |
| [Privacy Architecture](PRIVACY_ARCHITECTURE.md) | Privacy-by-design framework, volatile ingress, and multi-tier deletion |
| [Privacy Consent Model](PRIVACY_CONSENT_MODEL.md) | 3-tier consent model (Anonymous Passerby, Ephemeral Session, Consented) |
| [Privacy Data Classification](PRIVACY_DATA_CLASSIFICATION.md) | 12 authoritative data sensitivity classes and storage rules |
| [Privacy Data Minimization](PRIVACY_DATA_MINIMIZATION.md) | Immediate feature extraction and raw media drop within <= 100 ms |
| [Privacy Retention & Deletion](PRIVACY_RETENTION_AND_DELETION.md) | Six-tier deletion lifecycle, WAL truncation, and physical FTL reality |
| [Privacy Context Isolation](PRIVACY_CONTEXT_ISOLATION.md) | Cryptographic separation between multiple interaction subjects |
| [Privacy Media Processing](PRIVACY_MEDIA_PROCESSING.md) | In-memory ephemeral media tap buffers; strict disk persistence prohibition |
| [Privacy Audit & Transparency](PRIVACY_AUDIT_AND_TRANSPARENCY.md) | Subject data access reports and verifiable cryptographic audit trails |
| [Privacy Cloud Synchronization](PRIVACY_CLOUD_SYNCHRONIZATION.md) | Per-subject ciphertext synchronization with client-side key control |
| [Privacy Verification Requirements](PRIVACY_VERIFICATION_REQUIREMENTS.md) | Automated testing procedures verifying zero media disk leakage |

### 2.7 Observability, Resilience & Review (Sub-phases 2.18–2.20)

| Document | Description |
|---|---|
| [Architecture Scalability Review](ARCHITECTURE_SCALABILITY_REVIEW.md) | Scalability analysis across perception, memory, and reasoning engines |
| [Failure Isolation Review](ARCHITECTURE_FAILURE_ISOLATION_REVIEW.md) | Failure containment review covering 18 systemic fault scenarios |
| [Architecture Resilience Model](ARCHITECTURE_RESILIENCE_MODEL.md) | Dynamic degradation, graceful recovery, and fault tolerance patterns |
| [Resource Budgets Specification](ARCHITECTURE_RESOURCE_BUDGETS.md) | Subsystem memory, CPU, latency, and storage allocation budgets |
| [Bottleneck Analysis Specification](ARCHITECTURE_BOTTLENECK_ANALYSIS.md) | Analysis of IPC bandwidth, SQLite concurrency, and model scheduling bottlenecks |
| [Architecture Acceptance Matrix](ARCHITECTURE_ACCEPTANCE_MATRIX.md) | Acceptance criteria verification matrix for Phase 2 deliverables |
| [Risk Register](ARCHITECTURE_RISK_REGISTER.md) | Systemic risk register covering 9 identified risks and mitigations |
| [Implementation Readiness Review](ARCHITECTURE_IMPLEMENTATION_READINESS.md) | Pre-implementation qualification checklist and Phase 3 prerequisites |

### 2.8 Architecture Decision Records (`docs/architecture/decisions/`)

| ADR | Title | Status |
|---|---|---|
| [ADR-001](decisions/ADR-001-LAYERED-ARCHITECTURE.md) | Layered System Architecture | `APPROVED` |
| [ADR-002](decisions/ADR-002-ENGINE-INDEPENDENCE.md) | Engine Independence and Autonomy | `APPROVED` |
| [ADR-003](decisions/ADR-003-EVENT-DRIVEN-COMMUNICATION.md) | Inter-Engine Event-Driven Communication | `APPROVED` |
| [ADR-004](decisions/ADR-004-SHARED-CONTEXT-OWNERSHIP.md) | Shared Context Ownership and Access Control | `APPROVED` |
| [ADR-005](decisions/ADR-005-MODEL-ADAPTER-BOUNDARIES.md) | Model Adapter Boundaries | `APPROVED` |
| [ADR-006](decisions/ADR-006-CPU-FIRST-EXECUTION.md) | CPU-First Execution Strategy | `APPROVED` |
| [ADR-007](decisions/ADR-007-SDK-BOUNDARIES.md) | SDK Architecture and Public Boundaries | `APPROVED` |
| [ADR-008](decisions/ADR-008-ROS2-INTEGRATION-BOUNDARY.md) | ROS 2 Integration Boundary | `APPROVED` |
| [ADR-009](decisions/ADR-009-ROBOT-ABSTRACTION.md) | Robot Abstraction Layer Boundary | `APPROVED` |
| [ADR-010](decisions/ADR-010-EDGE-CLOUD-SEPARATION.md) | Edge-Cloud Separation | `APPROVED` |
| [ADR-011](decisions/ADR-011-SECURITY-AND-PRIVACY-ARCHITECTURE.md) | Security and Privacy Architecture | `APPROVED` |
| [ADR-012](decisions/ADR-012-eon-core-architecture.md) | EON Core Architecture | `APPROVED` |
| [ADR-013](decisions/ADR-013-engine-lifecycle-contract.md) | Engine Lifecycle Contract | `APPROVED` |
| [ADR-014](decisions/ADR-014-event-driven-communication-and-delivery-guarantees.md) | Event-Driven Delivery Guarantees | `APPROVED` |
| [ADR-015](decisions/ADR-015-shared-context-and-access-control.md) | Shared Context and Access Control | `APPROVED` |
| [ADR-016](decisions/ADR-016-provider-neutral-model-adapter-architecture.md) | Provider-Neutral Model Adapter Architecture | `APPROVED` |
| [ADR-017](decisions/ADR-017-edge-storage-and-data-governance.md) | Edge Storage and Data Governance | `APPROVED` |
| [ADR-018](decisions/ADR-018-api-architecture-and-security.md) | API Architecture and Security | `APPROVED` |
| [ADR-019](decisions/ADR-019-python-sdk-architecture.md) | Python SDK Architecture | `APPROVED` |
| [ADR-020](decisions/ADR-020-cpp-sdk-architecture.md) | C++ SDK Architecture | `APPROVED` |
| [ADR-021](decisions/ADR-021-ros2-integration-strategy.md) | ROS 2 Integration Strategy | `APPROVED` |
| [ADR-022](decisions/ADR-022-hardware-independent-robot-abstraction.md) | Hardware-Independent Robot Abstraction | `APPROVED` |
| [ADR-023](decisions/ADR-023-edge-deployment-and-process-supervision.md) | Edge Deployment and Process Supervision | `APPROVED` |
| [ADR-024](decisions/ADR-024-optional-cloud-architecture-and-sync.md) | Optional Cloud Architecture and Sync | `APPROVED` |
| [ADR-025](decisions/ADR-025-zero-trust-security-and-stride-threat-model.md) | Zero-Trust Security and STRIDE Threat Model | `APPROVED` |
| [ADR-026](decisions/ADR-026-privacy-by-design-and-cryptographic-boundaries.md) | Privacy-by-Design and Cryptographic Boundaries | `APPROVED` |
| [ADR-027](decisions/ADR-027-dual-runtime-interoperability-python-cpp.md) | Dual-Runtime Interoperability (Python/C++) | `APPROVED` |
| [ADR-028](decisions/ADR-028-failure-containment-and-resilience-model.md) | Failure Containment and Resilience Model | `APPROVED` |

---

## 3. Sub-Phase Qualification Reports

- [Phase 2.1 & 2.2 Qualification Report](PHASE_2_1_2_2_ARCHITECTURE_QUALIFICATION_REPORT.md)
- [Phase 2.3 Qualification Report](PHASE_2_3_QUALIFICATION_REPORT.md)
- [Phase 2.4 Qualification Report](PHASE_2_4_QUALIFICATION_REPORT.md)
- [Phase 2.5 Qualification Report](PHASE_2_5_QUALIFICATION_REPORT.md)
- [Phase 2.6 Qualification Report](PHASE_2_6_QUALIFICATION_REPORT.md)
- [Phase 2.7 Qualification Report](PHASE_2_7_QUALIFICATION_REPORT.md)
- [Phase 2.8 Qualification Report](PHASE_2_8_QUALIFICATION_REPORT.md)
- [Phase 2.9 Qualification Report](PHASE_2_9_QUALIFICATION_REPORT.md)
- [Phase 2.10 Qualification Report](PHASE_2_10_QUALIFICATION_REPORT.md)
- [Phase 2.11 Qualification Report](PHASE_2_11_QUALIFICATION_REPORT.md)
- [Phase 2.12 Qualification Report](PHASE_2_12_QUALIFICATION_REPORT.md)
- [Phase 2.13 Qualification Report](PHASE_2_13_QUALIFICATION_REPORT.md)
- [Phase 2.14 Qualification Report](PHASE_2_14_QUALIFICATION_REPORT.md)
- [Phase 2.15 Qualification Report](PHASE_2_15_QUALIFICATION_REPORT.md)
- [Phase 2.16 Qualification Report](PHASE_2_16_QUALIFICATION_REPORT.md)
- [Phase 2.17 Qualification Report](PHASE_2_17_QUALIFICATION_REPORT.md)
- [Phase 2.18 Qualification Report](PHASE_2_18_QUALIFICATION_REPORT.md)
- [Phase 2.19 Qualification Report](PHASE_2_19_QUALIFICATION_REPORT.md)
- [Phase 2.20 Qualification Report](PHASE_2_20_QUALIFICATION_REPORT.md)
- [Phase 2.3–2.10 Correction Audit Report](PHASE_2_3_TO_2_10_CORRECTION_AUDIT.md)
- [Phase 2.3–2.10 Master Qualification Report](PHASE_2_3_TO_2_10_FINAL_QUALIFICATION_REPORT.md)
- [Phase 2.11–2.20 Final Consolidated Qualification Report](PHASE_2_11_TO_2_20_FINAL_QUALIFICATION_REPORT.md)

---

## 4. Requalification and Audit Deliverables (`docs/audit/`)

The complete repository audit and requalification reports are located in `docs/audit/`:
- [Phase 2 Deliverables Inventory](../audit/PHASE_2_11_TO_2_20_AUDIT_INVENTORY.md) (`EON-AUDIT-INV-001`)
- [Privacy Deletion Claims Audit](../audit/PRIVACY_DELETION_CLAIMS_AUDIT.md) (`EON-AUDIT-PRIV-001`)
- [ROS 2 Compatibility Audit](../audit/ROS2_COMPATIBILITY_AUDIT.md) (`EON-AUDIT-ROS2-001`)
- [Documentation Consistency Audit](../audit/DOCUMENTATION_CONSISTENCY_AUDIT.md) (`EON-AUDIT-DOC-001`)
- [Commit and Qualification Evidence Audit](../audit/COMMIT_AND_QUALIFICATION_EVIDENCE_AUDIT.md) (`EON-AUDIT-EVD-001`)
- [Edge Resource Budget Audit](../audit/EDGE_RESOURCE_BUDGET_AUDIT.md) (`EON-AUDIT-RES-001`)
- [Full Phase 2 Architecture Consistency Audit](../audit/PHASE_2_FULL_ARCHITECTURE_CONSISTENCY_AUDIT.md) (`EON-AUDIT-CONSIST-001`)
- [Phase 2 Requirements Traceability Matrix](../audit/PHASE_2_REQUIREMENTS_TRACEABILITY.md) (`EON-AUDIT-RTM-001`)
- [Phase 2 Final Requalification Report](../audit/PHASE_2_FINAL_REQUALIFICATION_REPORT.md) (`EON-QUAL-PH2-FINAL-003`)
