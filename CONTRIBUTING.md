# Contributing to OVIC EON

**Emotional Intelligence Infrastructure for Robotics**  
**Organization:** OVIC Labs  
**Project:** OVIC EON  

Thank you for your interest in contributing to OVIC EON.

OVIC EON is a modular emotional and social intelligence infrastructure platform designed for humanoid, service, industrial, and social robotics. The platform follows a hybrid intelligence architecture combining deterministic software policies with supported machine learning capabilities, CPU-first execution, and strict safety and privacy boundaries.

---

## 1. Project Status and Governance

OVIC EON is being developed through controlled, evidence-based engineering milestones:

- **Current Milestone:** Phase 0 (Foundation & Requirements Qualification).
- **Phase 0 Rule:** Implementation code for Phase 1 must not be introduced until Phase 0 documentation and engineering baselines have received final founder acceptance.
- **Traceability Rule:** Every code change, interface modification, or specification update must trace directly to approved requirements in [`docs/requirements/REQUIREMENT_TRACEABILITY.md`](docs/requirements/REQUIREMENT_TRACEABILITY.md).

---

## 2. Core Engineering Principles

All contributions must adhere to the following core tenets:

1. **Safety-First Engineering:** Emotion recognition, empathy reasoning, personality simulation, or behavioural outputs must **never** directly authorize physical robot motion. Safety-critical decisions and emergency stops remain under the robot manufacturer's independent control.
2. **Deterministic Governance:** Policy enforcement, memory retention/deletion, and authorization boundaries must remain deterministic and auditable.
3. **Privacy by Design:** Personal data collection must be minimized, session isolation preserved, and deletion/correction workflows strictly supported.
4. **Uncertainty Awareness:** Perception and behavioral classifications are probabilistic observations, not internal psychological facts or diagnoses. Confidence and uncertainty metadata must be preserved.
5. **CPU-First Compatibility:** Baseline capabilities must function on CPU architectures. GPU or NPU acceleration is strictly optional.
6. **No Fabricated Evidence:** Performance claims, test results, or requirement verifications must be supported by reproducible evidence. Never mark an unverified requirement as complete.

---

## 3. Contribution Workflow

We follow a structured Git workflow for all contributions:

### 3.1 Branching Strategy

- `main`: Protected trunk containing approved milestone baselines. Direct pushes to `main` are restricted.
- Feature/Documentation branches: Use descriptive branch names:
  - `docs/<topic>` for documentation updates (e.g., `docs/perf-reconciliation`)
  - `feat/<engine-or-component>` for new features in supported milestones
  - `fix/<defect-id>` for defect resolutions (e.g., `fix/def-0012-event-timeout`)
  - `test/<category>` for test framework additions

### 3.2 Commit Message Standards

We follow Conventional Commits formatting:

```text
<type>(<scope>): <short description in imperative present tense>

[optional body explaining motivation and context]

[optional footer linking to requirement ID, defect ID, or PR]
```

Valid types: `docs`, `feat`, `fix`, `test`, `refactor`, `perf`, `chore`, `ci`.  
Example:
```text
docs(perf): reconcile provisional targets with performance specification

Aligns PRD, SRS, and acceptance criteria with PERFORMANCE_REQUIREMENTS.md.
Traceability: EON-PERF-001 through EON-PERF-066.
```

### 3.3 Pull Request Process

1. Fork the repository and create your branch from `main`.
2. Ensure all Markdown documents pass local validation:
   ```bash
   python scripts/validate_docs.py
   ```
3. Verify that all internal links resolve to existing files and valid anchors.
4. Verify that tables, headings, and code blocks follow repository conventions.
5. Update related documentation and traceability matrices where applicable.
6. Submit a Pull Request targeting `main`. Fill out the PR template completely.
7. Address reviewer feedback promptly. All CI checks must pass before merge.

---

## 4. Documentation Standards

When editing or adding documentation in `docs/`:

- Use GitHub Flavored Markdown (GFM).
- Keep numerical performance targets explicitly marked `PROVISIONAL` until empirical benchmark data is captured.
- Maintain consistent terminology across the seven intelligence engines:
  - **ERS:** Emotion Recognition System
  - **EMS:** Emotional Memory System
  - **ERE:** Empathy Reasoning Engine
  - **PSE:** Personality Simulation Engine
  - **SIE:** Social Interaction Engine
  - **ERG:** Emotional Response Generation
  - **HBU:** Human Behaviour Understanding
- Preserve `NOT_STARTED` and `TBD` in acceptance and evidence registers until tests are formally executed.

---

## 5. Defect Reporting

Found an issue or defect in specifications or implementations?

1. Search [`docs/acceptance/DEFECT_REGISTER.md`](docs/acceptance/DEFECT_REGISTER.md) and existing GitHub Issues to avoid duplicates.
2. Open a GitHub Issue using the Defect Report template. Include:
   - Defect title and affected component/engine.
   - Requirement IDs affected.
   - Severity and priority assessment.
   - Step-by-step reproduction or inconsistency evidence.
   - Expected versus actual behavior.

---

## 6. Security and Vulnerabilities

Please **do not** report sensitive security vulnerabilities through public GitHub Issues. Review our disclosure process in [SECURITY.md](SECURITY.md).

---

## 7. Contact and Support

For questions regarding engineering governance or the product roadmap, refer to the official contact channels published by OVIC Labs.
