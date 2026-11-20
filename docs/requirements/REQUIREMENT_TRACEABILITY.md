
# OVIC EON — Requirement Traceability Matrix (RTM)

**Product:** OVIC EON  
**Organization:** OVIC Labs  
**Document ID:** EON-RTM-001  
**Version:** 0.1.0  
**Status:** Approved Baseline — Pending Repository Validation  
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

The following table establishes the initial requirement-group mapping. Exact individual requirement titles and component assignments must be reconciled against the authoritative functional requirements document and repository.

| Requirement Range | Functional Area | Primary Components | Verification |
|---|---|---|---|
| EON-FR-001–010 | Initialization, lifecycle, and platform foundation | EON Core | Unit, integration, system |
| EON-FR-011–016 | Core coordination and communication | EON Core, Event Bus | Unit, contract, integration |
| EON-FR-017–022 | Emotion Recognition System | ERS | Unit, integration, evaluation |
| EON-FR-023–028 | Emotional Memory System | EMS | Unit, integration, privacy |
| EON-FR-029–034 | Empathy Reasoning Engine | ERE | Unit, scenario, policy |
| EON-FR-035–040 | Personality Simulation Engine | PSE | Unit, configuration |
| EON-FR-041–046 | Social Interaction Engine | SIE | Unit, integration, scenario |
| EON-FR-047–052 | Emotional Response Generation | ERG | Unit, integration, policy |
| EON-FR-053–056 | Human Behaviour Understanding | HBU | Unit, integration, evaluation |
| EON-FR-057–059 | Data contracts, APIs, and integration | API and contract layer | Contract, integration |
| EON-FR-060 | Safety and authorization boundary | EON Core and safety integration boundary | Safety, negative, integration |

**Reconciliation requirement:** This range grouping is an initial navigation aid, not a substitute for the actual requirement register. Before approving the detailed RTM, verify that every ID exists, its title matches the source, and its allocated group is correct. If the authoritative document assigns different boundaries, update this table.

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

The detailed NFR identifiers and titles must be imported from the approved `NON_FUNCTIONAL_REQUIREMENTS.md`.

| NFR Category | Expected System Area | Verification |
|---|---|---|
| Reliability | EON Core and all engines | Fault injection, recovery tests |
| Maintainability | Core and engine architecture | Code review, architecture review |
| Portability | Runtime and deployment layer | Environment compatibility tests |
| Modularity | Engine interfaces | Architecture and contract tests |
| Observability | Logging, metrics, diagnostics | Integration and operational tests |
| Security | APIs, configuration, data and deployment | Security tests and assessment |
| Compatibility | SDKs, contracts and ROS 2 | Compatibility tests |
| Scalability | Runtime and communication infrastructure | Load and stress tests |
| Availability | Runtime and deployment | Soak and fault-recovery tests |
| Documentation | SDKs and developer platform | Documentation and example validation |

Detailed mapping:

| Requirement ID | Requirement Title | System Specification | Component | Test ID | Status |
|---|---|---|---|---|---|
| Pending source import | Reliability requirements | Pending SRS mapping | EON Core | Pending | NOT MAPPED |
| Pending source import | Modularity requirements | Pending SRS mapping | Core and engines | Pending | NOT MAPPED |
| Pending source import | Security requirements | Pending SRS mapping | Security layer | Pending | NOT MAPPED |
| Pending source import | Portability requirements | Pending SRS mapping | Runtime | Pending | NOT MAPPED |
| Pending source import | Observability requirements | Pending SRS mapping | Monitoring | Pending | NOT MAPPED |

Do not assign fabricated NFR IDs. Populate this table from the actual source document.

---

# 12. Traceability Matrix — Performance Requirements

Performance requirements must be traceable to measurable workloads, reference hardware, test procedures, and results.

| Performance Area | Target Source | System Area | Verification |
|---|---|---|---|
| Core event routing latency | PERFORMANCE_REQUIREMENTS.md | EON Core | Benchmark |
| Event throughput | PERFORMANCE_REQUIREMENTS.md | Event Bus | Load test |
| Engine processing latency | PERFORMANCE_REQUIREMENTS.md | Individual engines | Benchmark |
| Startup readiness | PERFORMANCE_REQUIREMENTS.md | Runtime lifecycle | Startup test |
| Memory consumption | PERFORMANCE_REQUIREMENTS.md | Runtime and engines | Resource monitoring |
| CPU utilization | PERFORMANCE_REQUIREMENTS.md | Runtime and engines | Profiling |
| Recovery time | PERFORMANCE_REQUIREMENTS.md | Failure management | Fault injection |
| API response latency | PERFORMANCE_REQUIREMENTS.md | API layer | Load test |
| ROS 2 communication latency | PERFORMANCE_REQUIREMENTS.md | ROS 2 integration | Integration benchmark |

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

The following table provides category-level mapping.

| Requirement Category | Requirement Source | Primary Component | Verification |
|---|---|---|---|
| Data inventory and minimization | EON-PSR-001–010 | Data governance layer | Inspection, privacy tests |
| Consent and transparency | EON-PSR-011–020 | Policy and interaction layer | Scenario, negative tests |
| Retention and deletion | EON-PSR-021–030 | EMS and storage layer | Integration, deletion tests |
| Sensor and external transmission controls | EON-PSR-031–040 | Sensor and model adapters | Security and privacy tests |
| Access control and security | EON-PSR-041–050 | Authentication and authorization | Security tests |
| Audit and incident handling | EON-PSR-051–056 | Audit and monitoring | Inspection, integration |
| Responsible AI and uncertainty | EON-PSR-057–066 | ERS, HBU, ERE | Evaluation, scenario tests |
| Human oversight and interaction safeguards | EON-PSR-067–072 | ERE, SIE, ERG | Policy and scenario tests |
| Physical safety boundaries | EON-PSR-073–080 | EON Core and robotics boundary | Safety and negative tests |
| Fault handling and integration safeguards | EON-PSR-081–086 | EON Core and integration layer | Fault injection, integration |

**Reconciliation requirement:** Verify every range and title against the authoritative privacy and safety requirements document. This category-level grouping must not be treated as verified individual requirement mapping.

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

Use cases must be linked to functional requirements and test cases.

| Use Case ID | Use Case | Main Engines | Requirement Group |
|---|---|---|---|
| UC-HUM-001 | Context-Aware Human Greeting | ERS, HBU, SIE, PSE, ERG | Interaction and response |
| UC-HUM-002 | Human Emotion-Cue Interpretation | ERS, HBU | Emotion and behaviour |
| UC-HUM-003 | Interaction Memory Continuity | EMS, SIE, ERE | Memory and context |
| UC-HUM-004 | Adaptive Communication Style | PSE, ERE, SIE, ERG | Personality and response |
| UC-HUM-005 | Context-Aware Conversation Continuity | EMS, ERE, SIE, ERG, PSE | Conversation and memory |
| UC-HUM-006 | Respectful Interaction When a Person Appears Distressed | ERS, HBU, ERE, SIE, ERG | Interaction safeguards |
| UC-HUM-007 | Configurable Robot Personality | PSE, SIE, ERG | Configuration |
| UC-HUM-008 | Human Interaction Preference Management | EMS, PSE, SIE | Preferences and privacy |
| UC-HUM-009 | Human Interaction Interruption Management | SIE, ERE, ERG | Social interaction |
| UC-HUM-010 | Multiple Human Interaction Management | HBU, ERS, EMS, SIE, ERE, ERG | Group interaction |
| UC-DEV-001 | Initialize EON Core | EON Core | Lifecycle |
| UC-DEV-002 | Register an Intelligence Engine | EON Core | Engine management |
| UC-DEV-004 | Integrate EON with ROS 2 | Integration layer | Interoperability |
| UC-DEV-005 | Use the Python SDK | Python SDK | Developer interface |
| UC-DEV-009 | Handle Engine Failure | EON Core | Reliability |

The remaining service, social, industrial, developer, and research use cases must also be mapped before the full RTM is approved.

---

# 15. Software Requirements Specification Traceability

The SRS translates product requirements into implementable software specifications.

Each SRS requirement must identify its source requirement.

| SRS Requirement | Source Requirement | Design Reference | Component | Test Reference |
|---|---|---|---|---|
| To be assigned | EON-FR source ID | Architecture reference | Component | EON-TC ID |
| To be assigned | EON-NFR source ID | Architecture reference | Component | EON-TC ID |
| To be assigned | EON-PERF source ID | Performance design | Component | EON-TC ID |
| To be assigned | EON-PSR source ID | Security/safety design | Component | EON-TC ID |

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

| Metric | Formula |
|---|---|
| Source identification coverage | Requirements with valid source IDs / Total approved requirements × 100 |
| SRS coverage | Approved source requirements mapped to SRS / Total applicable approved source requirements × 100 |
| Design coverage | Applicable SRS requirements linked to design / Total applicable SRS requirements × 100 |
| Implementation coverage | Requirements with verified implementation references / Total applicable requirements × 100 |
| Test coverage | Verifiable requirements with test cases / Total verifiable requirements × 100 |
| Verification pass rate | Passed verified requirements / Total executed requirements × 100 |
| Evidence coverage | Passed requirements with valid evidence / Total passed requirements × 100 |
| Acceptance coverage | Accepted requirements / Total requirements planned for the release × 100 |

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

# 24. Initial Traceability Baseline

The following records establish the current planned baseline.

| Source | Known Baseline | Repository Validation |
|---|---|---|
| Functional requirements | EON-FR-001 to EON-FR-060 | Pending |
| Privacy and safety requirements | EON-PSR-001 to EON-PSR-086 | Pending |
| Non-functional requirements | Approved document requested; exact IDs to import | Pending |
| Performance requirements | Approved document requested; exact IDs to import | Pending |
| PRD | Version 0.1.0 baseline | Pending |
| Engine scope | Version 0.1.0 baseline | Pending |
| Use cases | Version 0.1.0 baseline | Pending |
| SRS | Must be completed and reconciled | Pending |
| Test evidence | Must be linked to actual executed tests | Pending |

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

**Current status:** Approved Baseline — Pending Repository Validation.

---

# 27. Final Engineering Rule

OVIC EON must maintain complete and reviewable traceability from product intent to verified software behaviour.

A requirement is not production-ready merely because it has been documented, designed, or implemented.

It must be verified against its approved acceptance criteria, supported by appropriate evidence, and accepted through the applicable release governance process.
