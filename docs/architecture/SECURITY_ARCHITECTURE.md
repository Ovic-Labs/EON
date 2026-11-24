# OVIC EON — Security Architecture Specification

**Document ID:** `EON-ARCH-SEC-001`  
**Phase:** Phase 2 — System Architecture and Engineering Design (Sub-phase 2.16)  
**Status:** `DESIGNED — NOT IMPLEMENTED (Phase 2 Architecture Baseline)`  
**Target Audience:** Cybersecurity Architects, Systems Software Engineers, Robotics Certifiers  
**Traceability:** PRD Section 4.5, SRS-SEC-001 through SRS-SEC-010, ADR-025, ADR-014  

---

## 1. Executive Summary and Zero-Trust Philosophy

The **OVIC EON Security Architecture** defines the defense-in-depth framework protecting EON’s emotional intelligence infrastructure against unauthorized intrusion, adversarial manipulation, data theft, and safety circumvention.

Robots operate in physically accessible environments where physical port access, local network adjacency, and untrusted software coexist. EON adheres to strict Zero-Trust architectural principles:
1. **Never Trust Local Adjacency:** Processes communicating over IPC, shared memory, or network sockets must be explicitly authenticated and authorized.
2. **Strict Trust Boundaries:** Complete process and privilege isolation between EON Core, model inference runtimes, robot hardware controllers, ROS 2 middleware, and optional cloud services.
3. **Defense-in-Depth Cryptography:** Hardware-backed root-of-trust (TPM 2.0 / Secure Element), envelope encryption with per-subject keys, and signed binaries.
4. **Non-Authoritative Physical Safety:** The security boundary guarantees that even in the catastrophic event of a compromised intelligence engine, the attacker cannot command physical robot motion because EON has zero direct actuator authority.

> [!IMPORTANT]
> **Implementation and Certification Status:** This specification establishes the security architecture and threat models for EON. In accordance with Phase 2 governance rules, all security features are classified as **DESIGNED — NOT IMPLEMENTED**. No third-party penetration testing or regulatory certifications (e.g., ISO 27001, IEC 62443) are claimed.

---

## 2. Trust Boundaries and Security Domains

```text
+-------------------------------------------------------------------------+
|                  DOMAIN 1: Robot Hardware & Safety HAL                  |
|   - Certified Safety Controller     - Hardware Emergency Stop Relay     |
|   - Low-level motor drivers         - Physical sensor electronics       |
+-------------------------------------------------------------------------+
       |                                                    ^
       | (Ingress Sensor Frames)                            | (Non-Authoritative
       v                                                    |  Proposals Checked)
+========================= TRUST BOUNDARY A ==============================+
+-------------------------------------------------------------------------+
|                   DOMAIN 2: EON Core Protected Daemon                   |
|   - Core Event Bus                  - Operational Lifecycle FSM         |
|   - Shared Context Engine           - Subject Encryption Key Store      |
|   - Local SQLite Context Store      - Systemd Service (user: eon)       |
+-------------------------------------------------------------------------+
       ^                                                    ^
       |                                                    |
+======|================== TRUST BOUNDARY B ================|=============+
       v                                                    v
+----------------------------------+  +-----------------------------------+
| DOMAIN 3: Intelligence Engines   |  | DOMAIN 4: Client & Middleware     |
| (ERS, EMS, ERE, PSE, SIE, ERG,   |  | - libeonsdk (C++ / Python)        |
|  HBU Model Runtimes / ONNX)      |  | - eon_ros2_bridge Nodes           |
+----------------------------------+  +-----------------------------------+
       ^
+======|================== TRUST BOUNDARY C ==============================+
       v
+-------------------------------------------------------------------------+
|                DOMAIN 5: Optional Cloud Platform (External)             |
|   - Fleet Telemetry                 - OTA Artifact Distribution         |
+-------------------------------------------------------------------------+
```

---

## 3. Trust Boundary Descriptions

1. **Trust Boundary A (Robot Safety Boundary):** Separates uncertified AI intelligence from the certified robot safety controller. Communication is unidirectional for actuation: EON publishes proposals with `is_authoritative = false`; the safety controller filters and commands actuators.
2. **Trust Boundary B (EON Core IPC Boundary):** Separates the core daemon from client SDKs, ROS 2 nodes, and inference worker engines. Enforced via Unix Domain Socket file permissions (`0660`), `SO_PEERCRED` UID validation, and capability tokens.
3. **Trust Boundary C (Cloud Boundary):** Separates the local robot edge system from the public internet / cloud. Enforced via mTLS with device certificates, strict TLS 1.3 encryption, and firewall rules.

---

## 4. Traceability Matrix

| Requirement ID | Architectural Requirement | Specification Document |
|---|---|---|
| `PRD-REQ-009` | Comprehensive robotic threat model and access control | `SECURITY_THREAT_MODEL.md` |
| `SRS-SEC-001` | Strong identity, authentication, and RBAC | `SECURITY_IDENTITY_AND_AUTHENTICATION.md` |
| `ADR-025` | Architecture Decision Record: Zero-Trust Security & STRIDE | `ADR-025-zero-trust-security-and-stride-threat-model.md` |
