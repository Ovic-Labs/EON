
# OVIC EON — Defect Register

**Product:** OVIC EON  
**Organization:** OVIC Labs  
**Repository:** EON  
**Document ID:** OVIC-EON-DR-001  
**Version:** 0.1.0  
**Phase:** 0.15 — Establish Acceptance Criteria  
**Status:** Approved by Founder — Pending Repository Validation  
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

Use this table as the central index.

| Defect ID | Title | Category | Severity | Priority | Component | Status | Assigned To |
|---|---|---|---|---|---|---|---|
| — | No verified defects registered yet | — | — | — | — | NOT STARTED | — |

**Important:** The initial empty register does not mean the product has zero defects. Defects must be discovered through implementation, inspection and testing.

# 16. Defect Reporting Template

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
Approved by Founder — Pending Repository Validation
