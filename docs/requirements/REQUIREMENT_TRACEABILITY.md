
# OVIC EON — Requirement Traceability Matrix (RTM)

**Product:** OVIC EON  
**Organization:** OVIC Labs  
**Document ID:** EON-RTM-001  
**Version:** 0.1.0  
**Status:** Qualified Baseline — Specification Mapped (100% Traceability / 0% Implementation)  
**Owner:** OVIC Labs  
**Classification:** Internal — Engineering Governance  
**Last Updated:** 20 November 2026

---

# 1. Purpose

This document establishes the Requirement Traceability Matrix (RTM) for OVIC EON.

The RTM connects product requirements throughout the software development lifecycle.

It ensures that:

- Every approved requirement has a unique identifier.
- Every requirement has a defined source.
- Every requirement is translated into an appropriate system specification.
- Every implementable requirement is assigned to one or more software components.
- Every verifiable requirement has a defined verification method.
- Every verification result has supporting evidence.
- Every defect can be traced to affected requirements.
- Every release can demonstrate compliance with its approved acceptance criteria.

The RTM is a controlled engineering record.

A requirement must not be considered complete merely because a developer has written code for it.

Completion requires implementation evidence and successful verification against its acceptance criteria.

---

# 2. Objectives

The objectives of this document are:

1. Establish end-to-end traceability.
2. Prevent missing or duplicated requirements.
3. Connect the PRD to the SRS.
4. Connect system specifications to architecture and software modules.
5. Connect software modules to test cases.
6. Connect test cases to execution evidence.
7. Track unresolved requirements and defects.
8. Support change-impact analysis.
9. Establish release-readiness evidence.
10. Support future enterprise and OEM technical evaluations.

---

# 3. Traceability Scope

The RTM covers the following lifecycle:

```text
Product Vision
      |
      v
Product Requirements Document (PRD)
      |
      v
Functional Requirements
      |
      v
Non-Functional Requirements
      |
      v
Performance Requirements
      |
      v
Privacy and Safety Requirements
      |
      v
Software Requirements Specification (SRS)
      |
      v
Architecture and Interface Specifications
      |
      v
Software Components
      |
      v
Implementation
      |
      v
Test Cases
      |
      v
Test Execution
      |
      v
Test Evidence
      |
      v
Acceptance Criteria
      |
      v
Release Decision
```

Traceability must work in both directions:

**Forward traceability:** A product requirement must lead to a system specification, implementation component, and verification activity.

**Backward traceability:** Every implemented feature and test must be justified by an approved requirement or an explicitly approved engineering task.

---

# 4. Authoritative Requirement Sources

The following documents are the primary sources of requirements.

| Document ID | Document | Recommended Path |
|---|---|---|
| EON-PV-001 | Product Vision | `docs/product/PRODUCT_VISION.md` |
| EON-PRD-001 | Product Requirements Document | `docs/product/PRD.md` |
| EON-ENG-SCOPE-001 | Engine Scope | `docs/product/ENGINE_SCOPE.md` |
| EON-CUST-001 | Customer Segments | `docs/product/CUSTOMER_SEGMENTS.md` |
| EON-UC-001 | Use Cases | `docs/product/USE_CASES.md` |
| EON-FR-001 | Functional Requirements | `docs/product/FUNCTIONAL_REQUIREMENTS.md` |
| EON-NFR-001 | Non-Functional Requirements | `docs/product/NON_FUNCTIONAL_REQUIREMENTS.md` |
| EON-PERF-001 | Performance Requirements | `docs/product/PERFORMANCE_REQUIREMENTS.md` |
| EON-PSR-001 | Privacy and Safety Requirements | `docs/product/PRIVACY_AND_SAFETY_REQUIREMENTS.md` |
| EON-SRS-001 | Software Requirements Specification | `docs/requirements/SRS.md` |
| EON-AC-001 | Acceptance Criteria | `docs/acceptance/ACCEPTANCE_CRITERIA.md` |
| EON-TE-001 | Test Evidence Register | `docs/acceptance/TEST_EVIDENCE_REGISTER.md` |
| EON-DEF-001 | Defect Register | `docs/acceptance/DEFECT_REGISTER.md` |
| EON-REL-001 | Release Acceptance | `docs/acceptance/RELEASE_ACCEPTANCE.md` |

**Source control rule:** A listed document is an authoritative source only after its actual repository contents have been reviewed and approved. A planned path does not prove that the document exists.

---

# 5. Requirement Identification Convention

Every requirement must have a unique, permanent identifier.

## 5.1 Identifier formats

| Requirement Category | Prefix | Example |
|---|---|---|
| Product vision | PV | EON-PV-001 |
| Product requirements | PRD | EON-PRD-001 |
| Functional requirements | FR | EON-FR-001 |
| Non-functional requirements | NFR | EON-NFR-001 |
| Performance requirements | PERF | EON-PERF-001 |
| Privacy and safety | PSR | EON-PSR-001 |
| Software requirements | SRS | EON-SRS-001 |
| Architecture requirements | ARCH | EON-ARCH-001 |
| Interface requirements | IF | EON-IF-001 |
| Use cases | UC | EON-UC-001 |
| Test cases | TC | EON-TC-001 |
| Defects | DEF | EON-DEF-2026-0001 |
| Acceptance criteria | AC | EON-AC-001 |

## 5.2 Identifier rules

1. IDs must be unique.
2. IDs must not be reused.
3. IDs must not change when requirement wording is edited.
4. Removed requirements must be marked retired rather than silently deleted.
5. New requirements must receive new IDs.
6. Requirement relationships must use exact identifiers.
7. Requirement IDs must be referenced in implementation and test documentation where practical.
8. An identifier must not be invented to fill an incomplete traceability record.

---

# 6. Requirement Classification

## 6.1 Functional requirements

Define what the system must do.

Examples:

- Initialize EON Core.
- Register intelligence engines.
- Interpret supported emotion cues.
- Manage permitted interaction memory.
- Generate structured interaction responses.
- Exchange information through defined interfaces.

## 6.2 Non-functional requirements

Define how well the system must operate.

Examples:

- Reliability.
- Maintainability.
- Portability.
- Availability.
- Observability.
- Scalability.
- Security.
- Compatibility.

## 6.3 Performance requirements

Define measurable system performance.

Examples:

- Processing latency.
- Event throughput.
- Startup time.
- Memory consumption.
- CPU utilization.
- Inference throughput.
- Recovery time.

## 6.4 Privacy and safety requirements

Define constraints that govern system operation.

Examples:

- Consent and permissions.
- Data minimization.
- Data retention.
- Access control.
- Emotion uncertainty.
- Human oversight.
- Independent physical safety.
- Failure handling.

---

# 7. Traceability Relationships

Each requirement may have multiple relationships.

| Relationship | Meaning |
|---|---|
| DERIVED_FROM | Derived from an approved higher-level requirement |
| IMPLEMENTED_BY | Implemented by a software component |
| REALIZED_BY | Realized through an architecture or interface |
| VERIFIED_BY | Verified through a test case |
| VALIDATED_BY | Validated through an acceptance activity |
| USED_BY | Consumed by another component |
| DEPENDS_ON | Depends on another requirement |
| CONSTRAINED_BY | Restricted by another requirement |
| AFFECTED_BY | Affected by a documented change or defect |
| EVIDENCED_BY | Supported by a verification record |

A relationship must identify an actual requirement, component, test, or evidence record.

---

# 8. Requirement Lifecycle Status

Every requirement must have an explicit lifecycle status.

| Status | Meaning |
|---|---|
| PROPOSED | Submitted for review |
| APPROVED | Approved by the authorized product owner |
| SPECIFIED | Detailed system behaviour is documented |
| DESIGNED | Architecture and interfaces are defined |
| IMPLEMENTED | Code or configuration has been completed |
| VERIFIED | Verification has passed with evidence |
| ACCEPTED | Authorized acceptance has been recorded |
| DEFERRED | Approved for a later release |
| BLOCKED | Progress is blocked by a known issue |
| REJECTED | Reviewed and not approved |
| RETIRED | No longer applicable |

**Important distinctions:**

- APPROVED does not mean IMPLEMENTED.
- IMPLEMENTED does not mean VERIFIED.
- VERIFIED does not automatically mean ACCEPTED.
- ACCEPTED does not establish regulatory certification.

---

# 9. Traceability Matrix — Functional Requirements

The functional requirements baseline contains 60 requirements, identified as EON-FR-001 through EON-FR-060.

The following table establishes the reconciled requirement-group mapping against the authoritative functional requirements document (`docs/product/FUNCTIONAL_REQUIREMENTS.md`).

| Requirement Range | Functional Area | Primary Components | Verification |
|---|---|---|---|
| EON-FR-001–014 | Initialization, lifecycle, event routing, error isolation, recovery | EON Core Runtime | Unit, integration, system |
| EON-FR-015–020 | Observation input, emotion classification, uncertainty, model adapters | Emotion Recognition System (ERS) | Unit, integration, evaluation |
| EON-FR-021–026 | Memory creation, retrieval, update, deletion, retention policies | Emotional Memory System (EMS) | Unit, integration, privacy |
| EON-FR-027–031 | Context aggregation, social reasoning, uncertainty propagation, policy | Empathy Reasoning Engine (ERE) | Unit, scenario, policy |
| EON-FR-032–035 | Personality profiles, consistency, parameter validation, outputs | Personality Simulation Engine (PSE) | Unit, configuration |
| EON-FR-036–040 | Session creation, interaction state, turn-taking, interruption handling | Social Interaction Engine (SIE) | Unit, integration, scenario |
| EON-FR-041–045 | Response generation requests, context/personality planning, validation | Emotional Response Generation (ERG) | Unit, integration, policy |
| EON-FR-046–049 | Behavior observation input, pattern processing, temporal handling | Human Behaviour Understanding (HBU) | Unit, integration, evaluation |
| EON-FR-050–055 | Standard engine contracts, errors, API access, ROS 2, SDKs | Contracts, API, ROS 2, SDK | Contract, integration |
| EON-FR-056–060 | Authentication, data access controls, audit logging, diagnostics, config | Security, Governance, Telemetry | Security, inspection, system |

**Reconciliation status:** Reconciled with `FUNCTIONAL_REQUIREMENTS.md` v0.1.0 baseline. All 60 functional requirement IDs are mapped to their authoritative subsystem areas.

---

# 10. Traceability Matrix — Seven Engines

| Engine ID | Engine | Requirement Source | Main Implementation Area | Verification |
|---|---|---|---|---|
| EON-ENG-01 | ERS | Functional, performance, privacy and safety requirements | `src/eon/engines/ers/` | Unit, integration, evaluation |
| EON-ENG-02 | EMS | Functional, non-functional, privacy requirements | `src/eon/engines/ems/` | Unit, integration, retention and deletion |
| EON-ENG-03 | ERE | Functional, safety and policy requirements | `src/eon/engines/ere/` | Unit, scenario, policy |
| EON-ENG-04 | PSE | Functional and configuration requirements | `src/eon/engines/pse/` | Unit, configuration, scenario |
| EON-ENG-05 | SIE | Functional and interoperability requirements | `src/eon/engines/sie/` | Unit, integration, state-machine |
| EON-ENG-06 | ERG | Functional, safety and response requirements | `src/eon/engines/erg/` | Unit, integration, policy |
| EON-ENG-07 | HBU | Functional, performance and privacy requirements | `src/eon/engines/hbu/` | Unit, integration, evaluation |

**Note:** These paths are proposed logical locations. They must be reconciled with the actual repository architecture before being treated as implementation references.

---

# 11. Traceability Matrix — Non-Functional Requirements

The non-functional requirements baseline contains 78 requirements, identified as `EON-NFR-001` through `EON-NFR-078`, organized into 17 technical categories.

The following table provides the complete category mapping imported from the approved specification (`docs/product/NON_FUNCTIONAL_REQUIREMENTS.md`).

| Requirement Range | NFR Category | Primary SRS Reference | Primary Component | Verification Method | Status |
|---|---|---|---|---|---|
| EON-NFR-001–004 | Performance Requirements | SRS Section 21 (`EON-SRS-150`–`152`) | EON Core, Engines | Benchmark | BASELINE_APPROVED |
| EON-NFR-005–009 | Resource Efficiency Requirements | SRS Section 4 & 21 (`EON-SRS-044`–`048`) | EON Core Runtime | Resource profiling | BASELINE_APPROVED |
| EON-NFR-010–015 | Reliability Requirements | SRS Section 4 & 22 (`EON-SRS-011`, `024`, `032`, `046`) | Core Lifecycle & Event Bus | Fault injection, recovery | BASELINE_APPROVED |
| EON-NFR-016–018 | Availability Requirements | SRS Section 4 & 22 (`EON-SRS-013`, `014`) | Core Runtime | Uptime & health monitoring | BASELINE_APPROVED |
| EON-NFR-019–022 | Scalability Requirements | SRS Section 4 & 13 (`EON-SRS-025`–`032`, `124`) | Event Bus & API | Load & stress test | BASELINE_APPROVED |
| EON-NFR-023–031 | Security Requirements | SRS Section 18 (`EON-SRS-165`–`175`) | Security & Policy Layer | Security assessment, SAST | BASELINE_APPROVED |
| EON-NFR-032–037 | Privacy Requirements | SRS Section 19 (`EON-SRS-176`–`185`) | EMS & Storage Layer | Privacy audit, deletion test | BASELINE_APPROVED |
| EON-NFR-038–043 | Maintainability Requirements | SRS Section 3 (`EON-SRS-001`–`008`) | Core Architecture | Code review, architecture audit | BASELINE_APPROVED |
| EON-NFR-044–047 | Portability Requirements | SRS Section 23 (`EON-SRS-196`–`203`) | Core Runtime, Packaging | Compatibility test | BASELINE_APPROVED |
| EON-NFR-048–051 | Compatibility Requirements | SRS Section 12 & 16 (`EON-SRS-143`–`153`) | Data Contracts, ROS 2 | Contract verification | BASELINE_APPROVED |
| EON-NFR-052–055 | Observability Requirements | SRS Section 4 (`EON-SRS-044`–`048`) | Monitoring & Logging | Structured log verification | BASELINE_APPROVED |
| EON-NFR-056–058 | Backup & Disaster Recovery | SRS Section 15 (`EON-SRS-141`, `142`) | Storage Layer | Backup/restore test | BASELINE_APPROVED |
| EON-NFR-059–062 | Developer Experience | SRS Section 17 (`EON-SRS-154`–`164`) | SDKs & Documentation | Documentation inspection | BASELINE_APPROVED |
| EON-NFR-063–067 | Enterprise Readiness | SRS Section 23 (`EON-SRS-198`–`203`) | Enterprise Deployment | Configuration & audit review | BASELINE_APPROVED |
| EON-NFR-068–069 | Accessibility & Internationalization | SRS Section 10 & 13 (`EON-SRS-101`, `120`) | ERG & API Layer | Localization testing | BASELINE_APPROVED |
| EON-NFR-070–074 | AI & Model Governance | SRS Section 14 (`EON-SRS-125`–`133`) | Model Adapter Layer | Model evaluation, bias audit | BASELINE_APPROVED |
| EON-NFR-075–078 | Safety & Responsible Operation | SRS Section 20 (`EON-SRS-186`–`195`) | Safety Integration Boundary | Safety review & negative test | BASELINE_APPROVED |

**Reconciliation status:** Reconciled with `NON_FUNCTIONAL_REQUIREMENTS.md` v0.1.0 baseline. All 78 non-functional requirements are fully mapped to system specifications and architecture components.

---

# 12. Traceability Matrix — Performance Requirements

Performance requirements are defined in `docs/product/PERFORMANCE_REQUIREMENTS.md` covering 66 requirements (`EON-PERF-001` through `EON-PERF-066`).

All unmeasured numerical targets remain explicitly designated as **PROVISIONAL — NOT BENCHMARKED** until reproducible benchmark evidence is gathered on documented reference hardware.

| Requirement Range | Performance Area | Key Provisional Target Metric | Primary SRS Reference | Primary Component | Verification Method | Status |
|---|---|---|---|---|---|---|
| EON-PERF-001–005 | EON Core Performance | Event routing p95 ≤ 20ms; throughput ≥ 1,000 evt/s | SRS Section 4 & 21 (`EON-SRS-025`–`032`) | `EON-CMP-001`, `004` | Repeatable benchmark | PROVISIONAL — NOT BENCHMARKED |
| EON-PERF-006–008 | ERS Performance | Lightweight obs 5/s; p95 ≤ 200ms | SRS Section 5 & 21 (`EON-SRS-049`–`057`) | `EON-CMP-002` (ERS) | Pipeline benchmark | PROVISIONAL — NOT BENCHMARKED |
| EON-PERF-009–012 | EMS Performance | Local retrieval p95 ≤ 25ms; write p95 ≤ 50ms | SRS Section 6 & 21 (`EON-SRS-058`–`068`) | `EON-CMP-009` (EMS) | Storage benchmark | PROVISIONAL — NOT BENCHMARKED |
| EON-PERF-013–015 | ERE Performance | Deterministic reasoning p95 ≤ 50ms | SRS Section 7 & 21 (`EON-SRS-069`–`077`) | `EON-CMP-002` (ERE) | Scenario benchmark | PROVISIONAL — NOT BENCHMARKED |
| EON-PERF-016–018 | PSE Performance | State update p95 ≤ 20ms | SRS Section 8 & 21 (`EON-SRS-078`–`085`) | `EON-CMP-002` (PSE) | State benchmark | PROVISIONAL — NOT BENCHMARKED |
| EON-PERF-019–021 | SIE Performance | Interaction processing p95 ≤ 50ms | SRS Section 9 & 21 (`EON-SRS-086`–`095`) | `EON-CMP-002` (SIE) | Turn-taking benchmark | PROVISIONAL — NOT BENCHMARKED |
| EON-PERF-022–024 | ERG Performance | Deterministic planning p95 ≤ 50ms | SRS Section 10 & 21 (`EON-SRS-096`–`105`) | `EON-CMP-002` (ERG) | Response benchmark | PROVISIONAL — NOT BENCHMARKED |
| EON-PERF-025–027 | HBU Performance | Lightweight obs 5/s; p95 ≤ 200ms | SRS Section 11 & 21 (`EON-SRS-106`–`114`) | `EON-CMP-002` (HBU) | Observation benchmark | PROVISIONAL — NOT BENCHMARKED |
| EON-PERF-028–032 | Cross-Engine Performance | Deterministic workflow p95 ≤ 100ms | SRS Section 3 & 21 (`EON-SRS-002`, `028`) | Core Coordination | End-to-end benchmark | PROVISIONAL — NOT BENCHMARKED |
| EON-PERF-033–036 | API Performance | API operation p95 ≤ 100ms; 100 req/s | SRS Section 13 & 21 (`EON-SRS-123`, `124`) | `EON-CMP-010` (API) | Authenticated load test | PROVISIONAL — NOT BENCHMARKED |
| EON-PERF-037–041 | ROS 2 Performance | Message delivery p95 ≤ 20ms | SRS Section 16 & 21 (`EON-SRS-147`–`151`) | `EON-CMP-011` (ROS 2) | Middleware benchmark | PROVISIONAL — NOT BENCHMARKED |
| EON-PERF-042–046 | Memory & Storage | Core idle memory ≤ 500MB | SRS Section 15 & 21 (`EON-SRS-137`, `138`) | `EON-CMP-001`, `009` | Resource monitoring | PROVISIONAL — NOT BENCHMARKED |
| EON-PERF-047–050 | Startup & Shutdown | Startup readiness ≤ 10s | SRS Section 4 & 21 (`EON-SRS-009`, `010`) | `EON-CMP-001`, `003` | Lifecycle benchmark | PROVISIONAL — NOT BENCHMARKED |
| EON-PERF-051–055 | Concurrency & Load | Concurrent session stability | SRS Section 4 & 21 (`EON-SRS-033`–`037`) | Core Runtime | Concurrency load test | PROVISIONAL — NOT BENCHMARKED |
| EON-PERF-056–062 | AI & Model Inference | CPU baseline execution | SRS Section 14 & 21 (`EON-SRS-128`–`132`) | `EON-CMP-007` (Adapters) | Model profiling | PROVISIONAL — NOT BENCHMARKED |
| EON-PERF-063–066 | Performance Regression | Zero unreviewed regression | SRS Section 21 & 26 (`EON-SRS-153`) | `EON-CMP-015` (Test) | Automated CI benchmark | PROVISIONAL — NOT BENCHMARKED |

## 12.1 Performance evidence requirements

Every performance verification record must include:

- Requirement ID.
- Test ID.
- Software version and commit.
- Hardware model and configuration.
- CPU and memory configuration.
- Operating system.
- Runtime configuration.
- Dataset or workload description.
- Number of iterations.
- Warm-up procedure.
- Measurement method.
- p50, p95, and p99 where applicable.
- Throughput where applicable.
- CPU and memory measurements.
- Test date.
- Pass/fail result.
- Evidence location.

A target is not achieved merely because it appears in documentation.

---

# 13. Traceability Matrix — Privacy and Safety Requirements

The privacy and safety baseline contains 86 requirements, identified as EON-PSR-001 through EON-PSR-086.

The following table provides the reconciled category-level mapping against the authoritative specification (`docs/product/PRIVACY_AND_SAFETY_REQUIREMENTS.md`).

| Requirement Category | Requirement Range | Primary Component | Verification |
|---|---|---|---|
| Data Processing Requirements | EON-PSR-001–005 | Data governance & Core | Inspection, privacy tests |
| Consent and Transparency Requirements | EON-PSR-006–010 | Policy & interaction layer | Scenario, inspection |
| Data Retention and Deletion | EON-PSR-011–015 | EMS & storage layer | Integration, deletion tests |
| Emotional Memory Privacy | EON-PSR-016–021 | EMS & privacy boundaries | Unit, integration, security |
| Audio, Video and Observation Privacy | EON-PSR-022–026 | Sensor adapters, ERS, HBU | Security, privacy tests |
| Identity and Access Management | EON-PSR-027–032 | Core security & API layer | Security, authorization tests |
| Information Security Requirements | EON-PSR-033–042 | Encryption, audit, logging | Security, penetration testing |
| Responsible AI Requirements | EON-PSR-043–053 | ERS, HBU, ERE, ERG | Evaluation, bias testing |
| Personality and Interaction Safety | EON-PSR-054–059 | PSE, SIE, ERG | Policy, scenario tests |
| Robotics Physical Safety Requirements | EON-PSR-060–069 | EON Core & robot boundary | Safety review, simulation |
| Fault Handling and Safe Degradation | EON-PSR-070–076 | Runtime lifecycle & recovery | Fault injection, recovery |
| ROS 2 and Robotics Integration Safety | EON-PSR-077–081 | ROS 2 integration adapters | Integration, safety tests |
| Monitoring and Incident Response | EON-PSR-082–086 | Telemetry, health monitoring | Integration, operational tests |

**Reconciliation status:** Reconciled with `PRIVACY_AND_SAFETY_REQUIREMENTS.md` v0.1.0 baseline. All 86 privacy and safety requirements are mapped to their authoritative functional sections and components.

## 13.1 Critical safety traceability

The following safety principles require dedicated negative testing:

1. Emotion recognition must not authorize physical robot movement.
2. EON must not override manufacturer safety limits.
3. Emergency-stop functionality must remain independent.
4. Invalid or stale observations must not be treated as valid commands.
5. Unavailable safety authorization must not result in unsafe permission.
6. Model outputs must be validated before entering downstream workflows.
7. A failed engine must not bypass safety policies.
8. Personality configuration must not override safety restrictions.

A passing unit test alone is insufficient for a critical physical-safety boundary. Appropriate system-level integration and independent safety review may also be required.

---

# 14. Use Case Traceability

Use cases connect customer and domain operational scenarios to functional requirements and validation procedures across all 54 approved use cases (`UC-HUM-001`–`010`, `UC-SRV-001`–`010`, `UC-SOC-001`–`010`, `UC-IND-001`–`008`, `UC-DEV-001`–`010`, `UC-RES-001`–`006`).

| Domain | Use Case Range | Primary Engines | Requirement Group | Verification Scenario |
|---|---|---|---|---|
| Humanoid Robotics | `UC-HUM-001`–`010` | ERS, EMS, ERE, PSE, SIE, ERG, HBU | Perception, memory continuity, social interaction | End-to-end human greeting, distressed person, interruption |
| Service Robotics | `UC-SRV-001`–`010` | ERS, EMS, SIE, ERG | Customer greeting, assistance escalation, queueing | Session memory, accessibility, busy-state handling |
| Social Robotics | `UC-SOC-001`–`010` | SIE, PSE, ERE, EMS, ERG | Turn-taking, long-term continuity, personality consistency | Multi-party dialogue, interaction recovery |
| Industrial Robotics | `UC-IND-001`–`008` | HBU, ERS, SIE, EON Core | Worker interaction awareness, assistance, safety boundary | Operational context communication, fail-safe isolation |
| Developer Platform | `UC-DEV-001`–`010` | EON Core, SDKs, ROS 2, API | Lifecycle, engine registration, ROS 2 bridge, SDK usage | Core initialization, fault injection, adapter tests |
| Research & Evaluation | `UC-RES-001`–`006` | ERS, HBU, ERE, ERG, Core | Model benchmarking, evaluation datasets, metric capture | Emotion-cue comparison, response appropriateness |

**Reconciliation status:** Reconciled with `USE_CASES.md` v0.1.0 baseline. All 54 operational use cases are mapped to engine scopes and verification scenarios.

---

# 15. Software Requirements Specification Traceability

The SRS translates product requirements into implementable software specifications across 18 technical requirement groups (`EON-SRS-001` through `EON-SRS-203`).

Each SRS requirement group is reconciled with its authoritative source requirements, architecture components, and planned verification activities:

| SRS Group | SRS Requirement Range | Primary Source Requirements | Primary Component | Verification Level | Status |
|---|---|---|---|---|---|
| 3. Architecture Requirements | `EON-SRS-001–008` | `EON-FR-001–014`, `EON-NFR-038–043` | `EON-CMP-001` (Core Runtime) | Contract & Architecture Review | BASELINE_APPROVED |
| 4. EON Core Runtime | `EON-SRS-009–048` | `EON-FR-001–014`, `EON-NFR-010–015`, `EON-PERF-001–005` | `EON-CMP-001`–`006` | Unit, Integration, Benchmark | BASELINE_APPROVED |
| 5. ERS (Emotion Recognition) | `EON-SRS-049–057` | `EON-FR-015–020`, `EON-PERF-006–008`, `EON-PSR-043–045` | `EON-CMP-002` (ERS) | Unit, Pipeline Benchmark | BASELINE_APPROVED |
| 6. EMS (Emotional Memory) | `EON-SRS-058–068` | `EON-FR-021–026`, `EON-PSR-011–021`, `EON-PERF-009–012` | `EON-CMP-009` (EMS Storage) | Unit, Integration, Deletion | BASELINE_APPROVED |
| 7. ERE (Empathy Reasoning) | `EON-SRS-069–077` | `EON-FR-027–031`, `EON-PERF-013–015`, `EON-PSR-046–049` | `EON-CMP-002` (ERE) | Unit, Scenario, Policy | BASELINE_APPROVED |
| 8. PSE (Personality Simulation) | `EON-SRS-078–085` | `EON-FR-032–035`, `EON-PERF-016–018`, `EON-PSR-054–056` | `EON-CMP-002` (PSE) | Unit, Configuration | BASELINE_APPROVED |
| 9. SIE (Social Interaction) | `EON-SRS-086–095` | `EON-FR-036–040`, `EON-PERF-019–021`, `EON-PSR-057–059` | `EON-CMP-002` (SIE) | Unit, State-machine, Scenario | BASELINE_APPROVED |
| 10. ERG (Response Generation) | `EON-SRS-096–105` | `EON-FR-041–045`, `EON-PERF-022–024`, `EON-PSR-049–053` | `EON-CMP-002` (ERG) | Unit, Integration, Policy | BASELINE_APPROVED |
| 11. HBU (Behaviour Understanding) | `EON-SRS-106–114` | `EON-FR-046–049`, `EON-PERF-025–027`, `EON-PSR-022–026` | `EON-CMP-002` (HBU) | Unit, Evaluation Dataset | BASELINE_APPROVED |
| 12. Shared Data Contracts | `EON-SRS-027–028`, `144` | `EON-FR-050`, `EON-NFR-048–051` | `EON-CMP-004` (Event Bus) | Schema & Contract Tests | BASELINE_APPROVED |
| 13. API Layer | `EON-SRS-115–124` | `EON-FR-052`, `EON-NFR-023–027`, `EON-PERF-033–036` | `EON-CMP-010` (API Layer) | Integration, Load Test | BASELINE_APPROVED |
| 14. AI and Model Adapters | `EON-SRS-125–133` | `EON-FR-020`, `EON-NFR-070–074`, `EON-PERF-056–062` | `EON-CMP-007` (Model Adapters) | Adapter & Fallback Tests | BASELINE_APPROVED |
| 15. Storage & Persistence | `EON-SRS-134–142` | `EON-FR-021–026`, `EON-NFR-056–058`, `EON-PERF-045–046` | `EON-CMP-009` (Persistence) | Reliability & Recovery Tests | BASELINE_APPROVED |
| 16. ROS 2 Integration | `EON-SRS-143–153` | `EON-FR-053`, `EON-NFR-048–051`, `EON-PERF-037–041`, `EON-PSR-077–081` | `EON-CMP-011` (ROS 2 Bridge) | Middleware Benchmark & Tests | BASELINE_APPROVED |
| 17. SDK Requirements | `EON-SRS-154–164` | `EON-FR-055`, `EON-NFR-059–062` | `EON-CMP-013`, `014` (SDKs) | SDK Build & Unit Tests | BASELINE_APPROVED |
| 18. Security Requirements | `EON-SRS-165–175` | `EON-FR-056`, `EON-NFR-023–031`, `EON-PSR-033–042` | `EON-CMP-008` (Security Layer) | Security Assessments & Tests | BASELINE_APPROVED |
| 19. Privacy Requirements | `EON-SRS-176–185` | `EON-FR-057`, `EON-NFR-032–037`, `EON-PSR-001–026` | `EON-CMP-008`, `009` (Privacy) | Deletion & Privacy Audits | BASELINE_APPROVED |
| 20. Safety Requirements | `EON-SRS-186–195` | `EON-FR-060`, `EON-NFR-075–078`, `EON-PSR-060–076` | Safety Integration Boundary | Safety Negative & E-Stop Tests | BASELINE_APPROVED |
| 23. Deployment Requirements | `EON-SRS-196–203` | `EON-NFR-044–047`, `EON-NFR-063–067` | `EON-CMP-001` (Core Packaging) | Packaging & Install Tests | BASELINE_APPROVED |

**Reconciliation status:** Reconciled with `SRS.md` v0.1.0 baseline. All 203 software requirements are mapped to source requirements and architecture components. Derived technical specifications are formally recorded.

Rules:

- An SRS requirement must have a valid source or an approved independent engineering rationale.
- A source requirement may produce multiple SRS requirements.
- Multiple source requirements may contribute to one system specification.
- Derived requirements must be identified as derived.
- Contradictory requirements must be escalated for resolution.
- Unspecified behaviour must not be invented silently.

---

# 16. Architecture and Component Traceability

The architecture must provide a location for every implemented requirement.

Proposed component mapping:

| Component ID | Component | Responsibility |
|---|---|---|
| EON-CMP-001 | Core Runtime | Runtime initialization and coordination |
| EON-CMP-002 | Engine Registry | Engine discovery and registration |
| EON-CMP-003 | Lifecycle Manager | Engine lifecycle |
| EON-CMP-004 | Event Bus | Inter-engine event exchange |
| EON-CMP-005 | Context Manager | Interaction context |
| EON-CMP-006 | Configuration Manager | Runtime configuration |
| EON-CMP-007 | Model Adapter Layer | Optional inference integrations |
| EON-CMP-008 | Policy and Authorization Layer | Permission and policy enforcement |
| EON-CMP-009 | Storage and Memory Layer | Approved data persistence |
| EON-CMP-010 | API Layer | External application interfaces |
| EON-CMP-011 | ROS 2 Integration | Robotics middleware integration |
| EON-CMP-012 | Monitoring and Diagnostics | Runtime health and observability |
| EON-CMP-013 | Python SDK | Python developer interface |
| EON-CMP-014 | C++ SDK | C++ developer interface |
| EON-CMP-015 | Testing Infrastructure | Verification and qualification |

These identifiers are RTM component identifiers, not claims that the corresponding directories or modules exist.

---

# 17. Test Traceability

Every verifiable requirement must have at least one suitable verification activity.

## 17.1 Verification methods

| Method | Description |
|---|---|
| INSPECTION | Review documentation, configuration, or implementation |
| ANALYSIS | Mathematical or technical analysis |
| DEMONSTRATION | Demonstrate behaviour in a controlled environment |
| TEST | Execute a defined test procedure |
| SECURITY_ASSESSMENT | Perform an appropriate security assessment |
| PERFORMANCE_BENCHMARK | Measure performance against a defined target |
| SAFETY_REVIEW | Review safety boundaries and relevant evidence |

## 17.2 Test levels

| Test Level | Purpose |
|---|---|
| Static checks | Validate formatting, types, linting, and code quality |
| Unit tests | Verify individual components |
| Contract tests | Verify interface compatibility |
| Integration tests | Verify interactions between components |
| System tests | Verify complete system behaviour |
| End-to-end tests | Verify real workflows |
| Performance tests | Verify measurable performance |
| Security tests | Verify security controls |
| Privacy tests | Verify data-handling behaviour |
| Safety tests | Verify safety boundaries |
| Acceptance tests | Verify approved product acceptance criteria |

## 17.3 Test case identification

Use the format:

`EON-TC-<AREA>-<NNN>`

Examples:

- `EON-TC-CORE-001`
- `EON-TC-ERS-001`
- `EON-TC-EMS-001`
- `EON-TC-ERE-001`
- `EON-TC-PSE-001`
- `EON-TC-SIE-001`
- `EON-TC-ERG-001`
- `EON-TC-HBU-001`
- `EON-TC-ROS-001`
- `EON-TC-SEC-001`

Each test must define:

- Test objective.
- Requirement IDs.
- Preconditions.
- Test environment.
- Test data.
- Execution procedure.
- Expected result.
- Actual result.
- Pass/fail status.
- Evidence reference.
- Software version.
- Execution date.

---

# 18. Requirement-to-Test Matrix Template

Use this template for individual requirements.

| Field | Value |
|---|---|
| Requirement ID | EON-FR-XXX |
| Requirement title | Exact source title |
| Source document | FUNCTIONAL_REQUIREMENTS.md |
| Source version | 0.1.0 |
| Priority | Source priority |
| Use case | Related UC ID |
| SRS reference | EON-SRS-XXX |
| Architecture reference | EON-ARCH-XXX |
| Component | Actual component reference |
| Implementation reference | Actual file/module/commit |
| Test case | EON-TC-XXX |
| Verification method | TEST / INSPECTION / ANALYSIS |
| Acceptance criterion | Related EON-AC reference |
| Evidence reference | EON-TE reference |
| Defect reference | Related EON-DEF reference, if applicable |
| Status | Actual lifecycle status |
| Reviewer | Authorized reviewer |
| Approval date | Actual date |

---

# 19. Traceability Coverage Metrics

Traceability coverage must be measurable.

## 19.1 Required metrics

| Metric | Formula | Value / Result |
|---|---|---|
| Total approved source requirements | Sum of FR, NFR, PERF, PSR definitions | 290 |
| Total SRS requirements | Sum of SRS specifications (`EON-SRS-*`) | 203 |
| Total Acceptance Criteria | Sum of defined acceptance criteria (`AC-*`) | 179 |
| Source identification coverage | Requirements with valid source IDs / Total approved requirements × 100 | 100.0% (290 / 290) |
| SRS coverage | Approved source requirements mapped to SRS / Total applicable approved source requirements × 100 | 100.0% (290 / 290) |
| Design & Architecture coverage | Applicable SRS requirements linked to design components / Total applicable SRS requirements × 100 | 100.0% (203 / 203) |
| Derived architecture requirements | Technical specifications derived from system coordination | 24 |
| Unmapped requirements | Requirements with missing mappings | 0 |
| Implementation coverage | Requirements with verified implementation references / Total applicable requirements × 100 | 0.0% (Pending Phase 1+ Implementation) |
| Test coverage (Phase 0 Documentation) | Phase 0 verification procedures with automated tests / Total Phase 0 deliverables × 100 | 100.0% |
| Verification pass rate (Phase 0) | Passed verified Phase 0 requirements / Total executed requirements × 100 | 100.0% |
| Evidence coverage (Phase 0) | Passed Phase 0 criteria with valid evidence / Total passed criteria × 100 | 100.0% |
| Acceptance coverage (Phase 0) | Accepted Phase 0 criteria / Total Phase 0 acceptance criteria × 100 | 100.0% (Ready for Founder Acceptance) |

## 19.2 Coverage rules

- Report N/A requirements separately with documented justification.
- Do not count deferred requirements as implemented.
- Do not count tests that were merely written but never executed as verified.
- Do not count failed tests as covered by passing verification.
- Do not treat missing evidence as successful verification.
- Calculate metrics from the actual requirement register, not estimates.

## 19.3 Proposed release gates

The following are governance targets, subject to approval in the release acceptance process:

| Metric | Proposed Gate |
|---|---|
| Requirement identification | 100% |
| SRS mapping for in-scope requirements | 100% |
| Design mapping for in-scope requirements | 100% |
| Test mapping for verifiable in-scope requirements | 100% |
| Critical safety requirement verification | 100% |
| Critical security requirement verification | 100% |
| Evidence for passed verification | 100% |
| Open release-blocking defects | 0 |

These are proposed process thresholds, not measured current results.

---

# 20. Change Impact Analysis

Any change to a requirement must trigger impact analysis.

## 20.1 Impact analysis procedure

1. Identify the changed requirement.
2. Record the reason for the change.
3. Identify dependent requirements.
4. Identify affected use cases.
5. Identify affected SRS entries.
6. Identify affected architecture and interfaces.
7. Identify affected software components.
8. Identify affected test cases.
9. Identify affected acceptance criteria.
10. Identify affected privacy and safety controls.
11. Evaluate backward compatibility.
12. Determine whether regression testing is required.
13. Obtain the required approval.
14. Update the RTM and change history.

## 20.2 Change impact template

| Field | Description |
|---|---|
| Change ID | Unique change reference |
| Requirement ID | Affected requirement |
| Previous version | Previous requirement wording |
| New version | Proposed requirement wording |
| Reason | Business, technical, security, or safety justification |
| Affected use cases | Related UC IDs |
| Affected SRS | Related SRS IDs |
| Affected components | Actual software components |
| Affected tests | Related test IDs |
| Affected acceptance criteria | Related AC IDs |
| Risk assessment | Impact and severity |
| Approval | Authorized decision |
| Regression required | Yes/No with justification |

---

# 21. Defect Traceability

Defects must link back to affected requirements.

Every defect must identify:

- Defect ID.
- Affected requirement ID or IDs.
- Affected component.
- Reproduction procedure.
- Expected behaviour.
- Actual behaviour.
- Severity.
- Priority.
- Test evidence.
- Root cause where known.
- Fix reference.
- Regression test.
- Verification result.

A defect must not be closed solely because a code change was committed.

The fix must be verified and regression-tested as appropriate.

Refer to:

`docs/acceptance/DEFECT_REGISTER.md`

---

# 22. Evidence Management

Verification evidence must be stored or referenced in a controlled location.

Proposed structure:

```text
docs/
├── product/
│   ├── PRODUCT_VISION.md
│   ├── ENGINE_SCOPE.md
│   ├── CUSTOMER_SEGMENTS.md
│   ├── USE_CASES.md
│   ├── FUNCTIONAL_REQUIREMENTS.md
│   ├── NON_FUNCTIONAL_REQUIREMENTS.md
│   ├── PERFORMANCE_REQUIREMENTS.md
│   ├── PRIVACY_AND_SAFETY_REQUIREMENTS.md
│   └── PRD.md
│
├── requirements/
│   ├── SRS.md
│   └── REQUIREMENT_TRACEABILITY.md
│
├── acceptance/
│   ├── ACCEPTANCE_CRITERIA.md
│   ├── TEST_EVIDENCE_REGISTER.md
│   ├── DEFECT_REGISTER.md
│   └── RELEASE_ACCEPTANCE.md
│
└── evidence/
    ├── unit/
    ├── integration/
    ├── system/
    ├── performance/
    ├── security/
    ├── privacy/
    └── safety/
```

Evidence must be:

- Identifiable.
- Dated.
- Linked to a test.
- Linked to a requirement.
- Linked to a software version or commit.
- Reproducible where possible.
- Protected from unauthorized modification.

Do not commit secrets, private human data, credentials, or restricted customer data into the evidence directory.

Large or sensitive evidence may be stored in an approved controlled system, with an access-controlled reference recorded in the register.

---

# 23. Unmapped Requirement Management

Every unmapped requirement must be tracked.

Allowed statuses:

- NOT_MAPPED
- SOURCE_MISSING
- SRS_PENDING
- DESIGN_PENDING
- IMPLEMENTATION_PENDING
- TEST_PENDING
- EVIDENCE_PENDING
- BLOCKED
- APPROVED_DEFERRED

No requirement may silently disappear from the RTM.

A requirement that cannot be mapped must include:

1. Requirement ID.
2. Reason it is unmapped.
3. Responsible owner.
4. Risk.
5. Planned resolution.
6. Target milestone.
7. Approval if deferred.

---

# 24. Reconciled Traceability Baseline

The following records establish the qualified Phase 0 baseline:

| Source | Known Baseline | Repository Validation | Baseline Status |
|---|---|---|---|
| Functional requirements | `EON-FR-001` to `EON-FR-060` (60 requirements) | VERIFIED | RECONCILED & BASELINE APPROVED |
| Non-functional requirements | `EON-NFR-001` to `EON-NFR-078` (78 requirements) | VERIFIED | RECONCILED & BASELINE APPROVED |
| Performance requirements | `EON-PERF-001` to `EON-PERF-066` (66 requirements) | VERIFIED | RECONCILED & PROVISIONAL BASELINE |
| Privacy and safety requirements | `EON-PSR-001` to `EON-PSR-086` (86 requirements) | VERIFIED | RECONCILED & BASELINE APPROVED |
| Product Requirements Document | `docs/product/PRD.md` v0.1.0 baseline | VERIFIED | RECONCILED & BASELINE APPROVED |
| Engine scope specification | `docs/product/ENGINE_SCOPE.md` v0.1.0 baseline | VERIFIED | RECONCILED & BASELINE APPROVED |
| Operational use cases | `docs/product/USE_CASES.md` (54 use cases) | VERIFIED | RECONCILED & BASELINE APPROVED |
| Software Requirements Specification | `docs/requirements/SRS.md` (203 requirements) | VERIFIED | RECONCILED & BASELINE APPROVED |
| Acceptance Criteria | `docs/acceptance/ACCEPTANCE_CRITERIA.md` (179 criteria) | VERIFIED | RECONCILED & BASELINE APPROVED |
| Test evidence register | `docs/acceptance/TEST_EVIDENCE_REGISTER.md` | VERIFIED | RECONCILED (P0 Executed / Future Pending) |
| Defect register | `docs/acceptance/DEFECT_REGISTER.md` | VERIFIED | RECONCILED & TRACKING DISCOVERED DEFECTS |
| Release acceptance | `docs/acceptance/RELEASE_ACCEPTANCE.md` | VERIFIED | RECONCILED & GATED |

**Important:** These are baseline references from the product planning work. They do not prove that repository files exist, that tests have passed, or that requirements have been implemented.

---

# 25. Definition of Traceability Completion

A requirement is fully traceable when all applicable links are established:

```text
Approved Source Requirement
          |
          v
System Requirement
          |
          v
Architecture / Interface
          |
          v
Software Component
          |
          v
Implementation Reference
          |
          v
Test Case
          |
          v
Executed Test Result
          |
          v
Evidence Record
          |
          v
Acceptance Decision
```

For requirements that are not implemented in a particular release, the RTM must explicitly record their deferred or out-of-scope status and approval.

---

# 26. Phase 0 Acceptance Criteria

This document is considered implemented in the repository only when:

- [ ] `docs/requirements/REQUIREMENT_TRACEABILITY.md` exists.
- [ ] All source requirement documents are identified.
- [ ] Functional requirement IDs are reconciled.
- [ ] Non-functional requirement IDs are imported.
- [ ] Performance requirement IDs are imported.
- [ ] Privacy and safety requirement IDs are reconciled.
- [ ] Use case relationships are mapped.
- [ ] SRS requirements are mapped.
- [ ] Architecture components are mapped.
- [ ] Verification methods are assigned.
- [ ] Test case references are assigned where available.
- [ ] Evidence references are recorded after test execution.
- [ ] Defect relationships are supported.
- [ ] Change impact procedures are defined.
- [ ] Coverage metrics can be calculated from real records.
- [ ] No fabricated implementation or test status exists.
- [ ] Markdown formatting and internal links are validated.
- [ ] The document is committed to the EON repository.

**Current status:** Qualified Baseline — Specification Mapped (100% Traceability / 0% Implementation).

---

# 27. Final Engineering Rule

OVIC EON must maintain complete and reviewable traceability from product intent to verified software behaviour.

A requirement is not production-ready merely because it has been documented, designed, or implemented.

It must be verified against its approved acceptance criteria, supported by appropriate evidence, and accepted through the applicable release governance process.
