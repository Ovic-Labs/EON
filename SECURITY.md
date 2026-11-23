# Security Policy — OVIC EON

**Product:** OVIC EON  
**Organization:** OVIC Labs  
**Tagline:** Emotional Intelligence Infrastructure for Robotics  
**Classification:** Public Security Policy  

OVIC Labs takes the security, reliability, and privacy of OVIC EON seriously. This policy describes our vulnerability reporting procedure, security architecture principles, and physical safety boundaries.

---

## 1. Supported Versions

Security updates and patches are provided for the following versions:

| Version | Milestone | Supported |
|---|---|---|
| 0.1.0 | Phase 0 — Foundation Baseline | Yes (Documentation & Architecture) |
| < 0.1.0 | Pre-baseline | No |

---

## 2. Fundamental Safety and Security Boundaries

When integrating or evaluating OVIC EON, note the following non-negotiable boundaries:

1. **Physical Motion Isolation:** Emotion recognition, empathy reasoning, personality, and behavioral interpretations must **never** directly authorize or trigger physical robot motion.
2. **Authoritative Safety Systems:** Motion authorization, emergency stop (E-stop), collision avoidance, and speed/separation monitoring must remain under the robot manufacturer's independent, certified safety systems.
3. **Data Minimization & Memory Governance:** Observable signals and emotional memory context must be strictly governed by retention, expiration, and authorized deletion workflows.
4. **Session Isolation:** Interaction context and emotional state must never leak across unlinked user sessions or unprivileged tenants.

---

## 3. Reporting a Vulnerability

If you discover a security vulnerability, privacy breach, or safety boundary failure in OVIC EON, please report it privately.

**Do NOT open a public GitHub issue for undisclosed vulnerabilities.**

### Reporting Procedure

1. **Email:** Send details to `security@oviclabs.com` (or use GitHub Private Vulnerability Reporting on the repository).
2. **Subject Line:** `[SECURITY] Vulnerability Report: OVIC EON - <Brief Description>`
3. **Details to Include:**
   - Description of the vulnerability or security weakness.
   - Affected engine or component (e.g., EON Core, ERS, EMS, API layer, ROS 2 integration).
   - Attack vector or failure scenario (e.g., prompt injection, unauthorized memory retrieval, memory leak, denial of service).
   - Step-by-step proof of concept (PoC) or reproduction steps.
   - Impact assessment (confidentiality, integrity, availability, or physical safety).
   - Any suggested mitigations or patches.

---

## 4. Response Timeline and Process

OVIC Labs commits to the following coordinated disclosure timeline:

- **Initial Acknowledgement:** Within 48 hours of receipt.
- **Triage and Assessment:** Within 5 business days, confirming validity and severity classification.
- **Remediation & Patching:** High and critical severity issues will be prioritized in active engineering sprints.
- **Public Disclosure:** Coordinated after a fix is available and integrators have been given reasonable advance notice.

---

## 5. Security Engineering Principles

OVIC EON engineering follows these principles:

- **Least Privilege:** Internal components and APIs run with minimum required permissions.
- **Contract Validation:** Inter-engine event buses validate schemas and reject malformed inputs.
- **Audit Logging:** Security-relevant lifecycle and administrative events are recorded in audit trails.
- **No Fictional Verification:** Security claims must be verified through threat modeling, static analysis, vulnerability scanning, and documented security reviews.
