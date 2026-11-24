# OVIC EON — Architecture Acceptance Matrix

**Document ID:** `EON-REG-ACCP-001`  
**Phase:** Phase 2 — System Architecture and Engineering Design (Sub-phase 2.20)  
**Status:** `DESIGNED — NOT IMPLEMENTED (Phase 2 Architecture Baseline)`  
**Target Audience:** QA Directors, Systems Certifiers, Chief Architects  
**Traceability:** PRD Section 4.5, SRS Acceptance Criteria, ADR-001 through ADR-028  

---

## 1. Acceptance Criteria Verification Matrix

This matrix maps all core system architecture acceptance criteria against written specifications and verification criteria:

| Acceptance ID | Architectural Requirement | Governing Specification | Verification Method | Acceptance Status |
|---|---|---|---|---|
| `ACC-ARCH-01` | CPU-First Execution with documented CPU fallback | `EDGE_RESOURCE_MANAGEMENT.md` | Verification of INT8 model configs and CPU execution provider | **ACCEPTED (DESIGN)** |
| `ACC-ARCH-02` | Zero Mandatory External AI APIs | `EDGE_OFFLINE_OPERATION.md` | Network inspection verifying zero outbound external inference | **ACCEPTED (DESIGN)** |
| `ACC-ARCH-03` | Seven-Engine Boundary Preservation | `SEVEN_ENGINE_INTERACTION.mmd` | Architectural review verifying zero circular engine dependencies | **ACCEPTED (DESIGN)** |
| `ACC-ARCH-04` | Non-Authoritative Physical Safety Boundary | `ROBOT_SAFETY_BOUNDARIES.md` | Code review verifying `is_authoritative = false` in all proposals | **ACCEPTED (DESIGN)** |
| `ACC-ARCH-05` | Zero Raw Media Disk Retention | `PRIVACY_MEDIA_PROCESSING.md` | Verification of `/dev/shm` volatile memory architecture | **ACCEPTED (DESIGN)** |
| `ACC-ARCH-06` | Truth-in-Specification Cryptographic Shredding | `PRIVACY_RETENTION_AND_DELETION.md` | Verification of per-subject DEK overwrite & WAL truncation | **ACCEPTED (DESIGN)** |
| `ACC-ARCH-07` | Native C++ SDK with Pimpl ABI Stability | `CPP_SDK_ABI_COMPATIBILITY.md` | Symbol visibility and header inspection | **ACCEPTED (DESIGN)** |
| `ACC-ARCH-08` | Decoupled ROS 2 Integration via Managed Lifecycle | `ROS2_LIFECYCLE_INTEGRATION.md` | Verification of standalone core build without ROS 2 | **ACCEPTED (DESIGN)** |
| `ACC-ARCH-09` | Hardware-Independent Robot Abstraction Layer | `ROBOT_CAPABILITY_MODEL.md` | Verification of dynamic capability negotiation schema | **ACCEPTED (DESIGN)** |
| `ACC-ARCH-10` | Zero-Trust Security with STRIDE Threat Model | `SECURITY_THREAT_MODEL.md` | Verification of mitigations for all 6 STRIDE categories | **ACCEPTED (DESIGN)** |
