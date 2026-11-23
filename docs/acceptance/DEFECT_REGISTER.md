
# OVIC EON — Defect Register

**Product:** OVIC EON  
**Organization:** OVIC Labs  
**Repository:** EON  
**Document ID:** OVIC-EON-DR-001  
**Version:** 0.1.0  
**Phase:** 0.15 — Establish Acceptance Criteria  
**Status:** Qualified Baseline — Documentation Verified (0 Open Defects)  
**Classification:** Software Quality and Engineering

---

# 1. Purpose

This document establishes the official defect tracking and management process for OVIC EON.

It provides a centralized record of:

- Software bugs.
- Functional failures.
- Engine failures.
- Integration defects.
- API defects.
- SDK defects.
- ROS 2 issues.
- AI/ML model defects.
- Performance problems.
- Security vulnerabilities.
- Privacy violations.
- Data integrity issues.
- Reliability problems.
- Documentation defects.
- Deployment failures.
- Production incidents.

Every identified defect must be documented, classified, investigated, assigned, resolved and verified.

No defect shall be marked as resolved merely because code has been changed. Verification evidence is required.

# 2. Defect Management Principles

1. Every defect must have a unique identifier.
2. Every defect must have a severity classification.
3. Every defect must have a priority.
4. Every defect must have reproducible information where applicable.
5. Every defect must identify the affected component.
6. Every defect must have an assigned owner or responsible role.
7. Every fix must be reviewed.
8. Every resolved defect must be retested.
9. Regression tests must be added where appropriate.
10. Critical safety and security defects must block release.
11. Defect history must be preserved.
12. No defect may be silently deleted or hidden.

# 3. Defect Identification System

Use the following identifier format:

`EON-DEF-YYYY-NNNN`

Examples:

- EON-DEF-2026-0001
- EON-DEF-2026-0002
- EON-DEF-2026-0003

Where:

| Field | Meaning |
|---|---|
| EON | Product identifier |
| DEF | Defect record |
| YYYY | Year identified |
| NNNN | Sequential defect number |

Identifiers must never be reused.

# 4. Defect Categories

| Category | Description |
|---|---|
| FUNCTIONAL | Feature does not work as specified |
| CORE | EON Core runtime defect |
| ERS | Emotion Recognition System defect |
| EMS | Emotional Memory System defect |
| ERE | Empathy Reasoning Engine defect |
| PSE | Personality Simulation Engine defect |
| SIE | Social Interaction Engine defect |
| ERG | Emotional Response Generation defect |
| HBU | Human Behaviour Understanding defect |
| AI_MODEL | Model loading, inference or output defect |
| DATA | Data contract, validation or integrity defect |
| API | REST, WebSocket or gRPC defect |
| SDK | Python or C++ SDK defect |
| ROBOT | Robot abstraction or hardware adapter defect |
| ROS | ROS 2 integration defect |
| SECURITY | Authentication, authorization or security defect |
| PRIVACY | Consent, retention, deletion or privacy defect |
| PERFORMANCE | Latency, CPU, memory or throughput defect |
| RELIABILITY | Crash, recovery or availability defect |
| DEPLOYMENT | Installation, packaging or deployment defect |
| DOCUMENTATION | Missing or incorrect documentation |
| BUILD | Compilation, dependency or CI failure |
| TESTING | Test infrastructure or test coverage defect |

# 5. Severity Classification

Severity represents the technical and business impact of a defect.

## 5.1 Critical — SEV-1

Examples:

- Robot safety boundary can be bypassed.
- Unauthorized physical command execution.
- Serious security compromise.
- Unauthorized access to sensitive personal memory.
- Major data loss or corruption.
- Emergency-stop authority can be bypassed.
- Critical system compromise.

**Required action:**
- Block affected release.
- Initiate immediate investigation.
- Apply containment where necessary.
- Notify responsible engineering and security reviewers.
- Verify remediation independently where appropriate.

## 5.2 High — SEV-2

Examples:

- EON Core cannot initialize.
- Multiple engines fail to communicate.
- Major memory retrieval failure.
- Authentication or authorization failure with significant impact.
- Serious persistent data inconsistency.
- Critical API workflow failure.
- Major ROS 2 integration failure.

**Required action:**
- Prioritize remediation.
- Block release when the defect affects required release scope.
- Require regression testing.

## 5.3 Medium — SEV-3

Examples:

- Individual engine feature malfunction.
- Non-critical API failure.
- Intermittent processing issue.
- Performance degradation outside critical paths.
- Incorrect but recoverable interaction behaviour.

**Required action:**
- Assign a fix.
- Document impact and workaround.
- Verify before the relevant release or formally defer.

## 5.4 Low — SEV-4

Examples:

- Minor UI issue.
- Documentation typo.
- Non-critical log formatting issue.
- Minor developer experience problem.

**Required action:**
- Record and schedule.
- Resolve through normal maintenance.

# 6. Priority Classification

Priority determines how quickly a defect should be addressed.

| Priority | Meaning |
|---|---|
| P0 | Immediate attention; release or safety blocker |
| P1 | Highest engineering priority |
| P2 | Normal planned remediation |
| P3 | Low-priority improvement |

Severity and priority are separate.

A defect may have high severity but a different remediation priority depending on containment, exposure and release scope. Safety-critical defects must never be deprioritized merely because they are difficult to reproduce.

# 7. Defect Lifecycle

Every defect must follow this lifecycle:

1. DETECTED
2. TRIAGED
3. CONFIRMED
4. ASSIGNED
5. IN_PROGRESS
6. FIX_READY
7. CODE_REVIEW
8. TESTING
9. VERIFIED
10. CLOSED

Additional states:

- REOPENED
- BLOCKED
- DEFERRED
- DUPLICATE
- INVALID
- ACCEPTED_RISK

## 7.1 Lifecycle Rules

- DETECTED: Defect has been reported.
- TRIAGED: Severity, priority and category are assigned.
- CONFIRMED: The defect has been reproduced or otherwise validated.
- ASSIGNED: Responsibility is assigned.
- IN_PROGRESS: Investigation or correction is underway.
- FIX_READY: Proposed correction is ready for review.
- CODE_REVIEW: Changes are under review.
- TESTING: Verification is underway.
- VERIFIED: Expected behaviour is demonstrated with evidence.
- CLOSED: Authorized reviewer confirms completion.
- REOPENED: Defect reappears or verification fails.
- BLOCKED: A dependency prevents progress.
- DEFERRED: Approved for a later release.
- DUPLICATE: Another defect record already tracks the same issue.
- INVALID: Investigation establishes that it is not a valid defect.
- ACCEPTED_RISK: A documented risk has been explicitly approved for a defined scope and period.

# 8. Mandatory Defect Record Template

Every defect must use the following template.

## Defect Information

| Field | Value |
|---|---|
| Defect ID | EON-DEF-YYYY-NNNN |
| Title | [Short description] |
| Category | [Category] |
| Severity | [SEV-1 / SEV-2 / SEV-3 / SEV-4] |
| Priority | [P0 / P1 / P2 / P3] |
| Status | [Lifecycle status] |
| Component | [Affected component] |
| Engine | [Affected engine, if applicable] |
| Environment | [Development / Testing / Simulation / Production] |
| Version | [Affected software version] |
| Commit | [Affected commit SHA] |
| Reported By | [Reporter or automated test] |
| Assigned To | [Responsible person or role] |
| Date Reported | [YYYY-MM-DD] |
| Target Resolution | [YYYY-MM-DD or TBD] |

## Description

[Explain the defect clearly.]

## Expected Behaviour

[Describe the correct expected result.]

## Actual Behaviour

[Describe what actually happens.]

## Reproduction Steps

1. [Step one]
2. [Step two]
3. [Step three]

## Impact

[Explain affected features, customers, data or operations.]

## Root Cause

[Document the confirmed cause after investigation.]

## Proposed Resolution

[Describe the corrective action.]

## Verification

- [ ] Fix implemented.
- [ ] Code review completed.
- [ ] Unit tests passed.
- [ ] Integration tests passed.
- [ ] Regression tests passed.
- [ ] Relevant security or privacy tests passed.
- [ ] Verification evidence attached.
- [ ] Reviewer approval recorded.

## Closure Information

| Field | Value |
|---|---|
| Resolution | [Description] |
| Fixed Version | [Version] |
| Fix Commit | [Commit SHA] |
| Test Evidence | [Path or URL] |
| Verified By | [Reviewer] |
| Verified Date | [YYYY-MM-DD] |
| Closure Approval | [Approver] |
| Closed Date | [YYYY-MM-DD] |

# 9. Engine-Specific Defect Tracking

## 9.1 EON Core

Track:
- Engine registration failures.
- Lifecycle transition errors.
- Event bus failures.
- Queue overflow.
- Invalid event handling.
- Context corruption.
- Configuration errors.
- Health monitoring failures.
- Recovery failures.

## 9.2 ERS

Track:
- Image preprocessing defects.
- Audio processing defects.
- Face detection failures.
- Feature extraction errors.
- Classification failures.
- Multimodal fusion errors.
- Timestamp synchronization issues.
- Confidence calibration defects.
- Unknown-state handling failures.
- Fairness evaluation issues.

## 9.3 EMS

Track:
- Memory creation failures.
- Retrieval failures.
- Incorrect associations.
- Unauthorized access.
- Retention failures.
- Deletion failures.
- Encryption failures.
- Storage corruption.
- Backup and recovery problems.

## 9.4 ERE

Track:
- Context construction failures.
- Reasoning inconsistencies.
- Rule execution failures.
- Invalid model output.
- Policy violations.
- Uncertainty handling failures.
- Unsafe response strategy selection.
- Missing explanation traces.

## 9.5 PSE

Track:
- Profile loading errors.
- Invalid personality configuration.
- Version compatibility failures.
- Inconsistent personality output.
- Unauthorized profile changes.
- Profile persistence failures.

## 9.6 SIE

Track:
- Session creation failures.
- Dialogue state corruption.
- Turn-taking errors.
- Interruption handling failures.
- Timeout failures.
- Multi-user context leakage.
- Session recovery failures.

## 9.7 ERG

Track:
- Response planning failures.
- Template generation defects.
- LLM adapter failures.
- TTS integration errors.
- Expression mapping failures.
- Gesture mapping failures.
- Unsupported robot capability requests.
- Invalid response output.

## 9.8 HBU

Track:
- Human detection failures.
- Tracking failures.
- Posture estimation defects.
- Gesture recognition defects.
- Activity classification errors.
- Temporal analysis failures.
- Conflicting observation handling failures.

# 10. Security and Privacy Defect Handling

Security and privacy defects require special handling.

Examples:

- Authentication bypass.
- Authorization bypass.
- Secret exposure.
- Sensitive memory disclosure.
- Cross-session data leakage.
- Unauthorized deletion.
- Consent enforcement failure.
- Unencrypted sensitive data.
- Unsafe external model data transfer.
- Audit log tampering.

Rules:

1. Restrict sensitive vulnerability details to authorized personnel.
2. Do not publish secrets, credentials or exploitable personal data in public issues.
3. Record remediation and verification evidence.
4. Preserve required security investigation records.
5. Follow responsible vulnerability disclosure procedures.
6. Do not close a security defect without validating the correction.

# 11. Defect Verification Rules

A defect can only be marked VERIFIED when:

1. The original issue has been reproduced or its validity established.
2. A corrective change is available.
3. The change has been reviewed.
4. The original failure condition has been retested.
5. Relevant regression tests pass.
6. No unacceptable new failures are introduced.
7. Evidence is recorded.
8. The verification environment is identified.

A defect can only be marked CLOSED after the required approval is recorded.

# 12. Regression Testing Requirements

For every corrected defect:

- Add a regression test where practical.
- Verify the original failure no longer occurs.
- Test adjacent functionality.
- Test affected engine interfaces.
- Check shared data contracts.
- Check relevant integration paths.
- Record the result.

Critical and high-severity defects require stronger regression evidence appropriate to their impact.

# 13. Defect Metrics

Track the following metrics:

| Metric | Purpose |
|---|---|
| Total defects | Overall recorded defects |
| Open defects | Unresolved issues |
| Critical defects | Safety and severe security blockers |
| High-severity defects | Major functional risks |
| Defect closure rate | Remediation progress |
| Mean time to resolve | Average remediation duration |
| Reopened defects | Fix quality indicator |
| Regression failures | Stability indicator |
| Defects by engine | Component quality |
| Defects by release | Release quality |
| Escaped defects | Issues found after release |

Metrics must be based on actual defect records, not estimates presented as measured values.

# 14. Release Defect Gates

A release must not proceed when:

- Any unresolved critical defect affects the release.
- A required safety test fails.
- A required security control is bypassable.
- Unauthorized access to protected data is possible.
- Required data deletion is broken.
- Core startup or installation fails.
- Required acceptance evidence is missing.
- A known high-severity defect affecting mandatory release scope has not been resolved or formally excluded through an authorized decision.

Medium and low defects may be deferred only with documented justification, ownership and release impact.

# 15. Defect Register

Use this table as the central index. The table records verified Phase 0 documentation and qualification defects identified and resolved during qualification audits.

| Defect ID | Title | Category | Severity | Priority | Component | Status | Assigned To |
|---|---|---|---|---|---|---|---|
| EON-DEF-0001 | README clone URL pointed to personal user path | Documentation | Low | P1 | Repository Root | CLOSED | Qualification Lead |
| EON-DEF-0002 | Missing CONTRIBUTING.md and SECURITY.md created broken links | Governance | Medium | P1 | Repository Root | CLOSED | Qualification Lead |
| EON-DEF-0003 | Performance target tables omitted 6 provisional metrics | Specification | Medium | P0 | PRD, SRS, AC | CLOSED | Systems Architect |
| EON-DEF-0004 | RTM range groupings misaligned with source sections | Traceability | Low | P1 | RTM | CLOSED | Traceability Lead |
| EON-DEF-0005 | Missing CI automated documentation validation workflow | Automation | Low | P1 | GitHub Actions | CLOSED | DevOps Engineer |

**Open Defect Summary:** 0 open blocker, critical, major, or minor defects for Phase 0 documentation baseline.

# 16. Defect Reporting Template and Resolved Defect Records

Use this template when reporting a new defect:

```text
Defect ID:
Title:
Category:
Severity:
Priority:
Component:
Engine:
Environment:
Affected Version:
Affected Commit:

Description:

Expected Behaviour:

Actual Behaviour:

Steps to Reproduce:

Impact:

Logs or Evidence:

Suggested Resolution:

Reported By:
Date:
```

### Resolved Defect Records

```text
Defect ID: EON-DEF-0001
Title: Incorrect clone URL in README.md
Category: Documentation
Severity: Low
Priority: P1
Component: README.md
Engine: N/A
Environment: GitHub Repository
Affected Version: 0.1.0
Affected Commit: 754388b

Description: README.md Section 12 directed users to clone from https://github.com/krishanth7/EON.git instead of official organization repository.
Expected Behaviour: Clone URL should reference https://github.com/Ovic-Labs/EON.git.
Actual Behaviour: Pointed to personal repository fork.
Steps to Reproduce: Inspect README.md line 483.
Impact: Potential developer friction and incorrect remote configuration.
Logs or Evidence: python scripts/validate_docs.py check_clone_url
Resolution: Corrected clone URL to https://github.com/Ovic-Labs/EON.git.
Regression Test: scripts/validate_docs.py check_clone_url
Status: CLOSED
Reported By: Qualification Engineer
Date: 2026-11-23
```

```text
Defect ID: EON-DEF-0002
Title: Missing CONTRIBUTING.md and SECURITY.md in repository root
Category: Governance / Documentation
Severity: Medium
Priority: P1
Component: Repository Root
Engine: N/A
Environment: GitHub Repository
Affected Version: 0.1.0
Affected Commit: 754388b

Description: README.md Section 15 and Section 16 referenced CONTRIBUTING.md and SECURITY.md, but the files did not exist in the root directory.
Expected Behaviour: Core repository governance documents must exist and outline contribution standards and security disclosure policies.
Actual Behaviour: Links produced 404 / file not found errors.
Steps to Reproduce: Run link verification on README.md.
Impact: Lack of clear contribution guidelines and private security disclosure process.
Logs or Evidence: Broken link audit reported 2 missing files.
Resolution: Authored comprehensive CONTRIBUTING.md and SECURITY.md policies tailored to OVIC EON's hybrid AI and robotics safety model.
Regression Test: scripts/validate_docs.py check_markdown_links
Status: CLOSED
Reported By: Qualification Engineer
Date: 2026-11-23
```

```text
Defect ID: EON-DEF-0003
Title: Inconsistent performance target metrics across PRD, SRS, and Acceptance Criteria
Category: Specification
Severity: Medium
Priority: P0
Component: PRD, SRS, Acceptance Criteria
Engine: Cross-engine, ERS, EMS, HBU, API, ROS 2
Environment: Documentation Suite
Affected Version: 0.1.0
Affected Commit: 754388b

Description: PERFORMANCE_REQUIREMENTS.md defined 21 provisional metrics, but PRD.md and SRS.md omitted 6 metrics (e.g. ERS/HBU p95 latency, EMS write latency, ROS 2 delivery, soak qualification), and ACCEPTANCE_CRITERIA.md listed only a partial subset of 6 metrics.
Expected Behaviour: All 4 documents must present a single reconciled performance baseline, explicitly designated as PROVISIONAL.
Actual Behaviour: Discrepancy in table rows and target completeness.
Steps to Reproduce: Compare Section 21 of PERFORMANCE_REQUIREMENTS.md with PRD Section 13.1, SRS Section 21, and AC Section 21.
Impact: Ambiguity for performance benchmark planning and acceptance gates.
Logs or Evidence: scratch/compare_perf.py side-by-side analysis.
Resolution: Reconciled all 4 documents to mirror the complete 21-metric target baseline from PERFORMANCE_REQUIREMENTS.md.
Regression Test: scripts/validate_docs.py check_performance_reconciliation
Status: CLOSED
Reported By: Systems Architect
Date: 2026-11-23
```

```text
Defect ID: EON-DEF-0004
Title: Requirement Traceability Matrix range groupings misaligned with source specifications
Category: Traceability
Severity: Low
Priority: P1
Component: REQUIREMENT_TRACEABILITY.md
Engine: Cross-engine
Environment: Documentation Suite
Affected Version: 0.1.0
Affected Commit: 754388b

Description: RTM Sections 9 and 13 contained provisional range increments (e.g., EON-FR-041-046 as SIE instead of ERG; EON-PSR-001-010 instead of 001-005) with uncompleted placeholders in Sections 11 and 15.
Expected Behaviour: RTM must accurately map the exact boundaries defined in authoritative requirement documents.
Actual Behaviour: Placeholder rows ("Pending source import", "To be assigned") remained in RTM.
Steps to Reproduce: Inspect REQUIREMENT_TRACEABILITY.md Sections 9, 11, 13, 15.
Impact: Incomplete traceability audit and unverifiable coverage metrics.
Logs or Evidence: RTM gap audit in scratch/audit_deep.py.
Resolution: Fully mapped all 60 FRs, 78 NFRs, 66 PERFs, 86 PSRs, and 203 SRS specifications into RTM.
Regression Test: scripts/validate_docs.py check_no_duplicate_requirement_definitions
Status: CLOSED
Reported By: Traceability Lead
Date: 2026-11-23
```

```text
Defect ID: EON-DEF-0005
Title: Absence of automated documentation linting and link verification in CI
Category: Automation / DevOps
Severity: Low
Priority: P1
Component: GitHub Actions Workflows
Engine: N/A
Environment: CI Pipeline
Affected Version: 0.1.0
Affected Commit: 754388b

Description: Repository lacked continuous integration workflows to enforce Markdown standards and prevent broken internal links on pull requests.
Expected Behaviour: CI workflow runs automated linting and validation on all commits.
Actual Behaviour: Directory .github/workflows was missing.
Steps to Reproduce: Check .github/workflows directory existence.
Impact: Risk of silent link breakage and specification drift.
Logs or Evidence: Missing CI configuration.
Resolution: Added .github/workflows/documentation-qualification.yml, .markdownlint-cli2.jsonc, and scripts/validate_docs.py.
Regression Test: python scripts/validate_docs.py && npx markdownlint-cli2 "**/*.md"
Status: CLOSED
Reported By: DevOps Engineer
Date: 2026-11-23
```

# 17. Repository and GitHub Integration

Recommended workflow:

1. Report defects through GitHub Issues.
2. Apply consistent labels.
3. Assign the responsible maintainer.
4. Link defects to related pull requests or commits.
5. Add regression tests.
6. Update this register or its automated source of truth.
7. Verify the correction.
8. Close the GitHub issue after approval.

Recommended GitHub labels:

- `bug`
- `critical`
- `high-priority`
- `medium-priority`
- `low-priority`
- `security`
- `privacy`
- `performance`
- `reliability`
- `regression`
- `needs-reproduction`
- `blocked`
- `verified`

Do not duplicate GitHub issue data manually in multiple places without a synchronization policy. If GitHub Issues becomes the authoritative defect database, this Markdown file should serve as the process and index document.

# 18. Phase 0.15 Completion Criteria

Phase 0.15 defect-management documentation is complete when:

1. Defect identification rules are defined.
2. Categories are defined.
3. Severity levels are defined.
4. Priorities are defined.
5. Lifecycle states are defined.
6. A mandatory defect template exists.
7. Seven-engine defect categories are documented.
8. Security and privacy handling is documented.
9. Verification rules are documented.
10. Regression requirements are documented.
11. Release defect gates are documented.
12. GitHub integration workflow is documented.
13. The defect register is created.
14. Repository documentation is validated.

---

**Document End**

OVIC-EON-DR-001  
Version 0.1.0  
Approved by Founder — Documentation Verified (0 Open Defects)
