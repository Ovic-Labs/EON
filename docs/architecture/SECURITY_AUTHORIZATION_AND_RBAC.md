# OVIC EON — Security Authorization and RBAC Specification

**Document ID:** `EON-SPEC-SEC-003`  
**Phase:** Phase 2 — System Architecture and Engineering Design (Sub-phase 2.16)  
**Status:** `DESIGNED — NOT IMPLEMENTED (Phase 2 Architecture Baseline)`  
**Target Audience:** Security Engineers, Systems Developers  
**Traceability:** `EON-ARCH-SEC-001`, ADR-025  

---

## 1. Capability-Based Authorization Model

EON enforces a capability-based permission matrix governing what actions local clients and components may perform:

```text
+-------------------------------------------------------------------------+
|                           Permission Capabilities                       |
+-------------------------------------------------------------------------+
| `CAP_INGEST_SENSOR`   : Publish to perception ingress topics            |
| `CAP_READ_OBSERVATION`: Subscribe to emotion & behavior inferences      |
| `CAP_READ_CONTEXT`    : Query shared context data                       |
| `CAP_WRITE_CONTEXT`   : Update shared context state                     |
| `CAP_PURGE_CONTEXT`   : Request cryptographic shredding of subject data |
| `CAP_PROPOSE_MOTION`  : Publish social motion proposals                 |
| `CAP_MANAGE_LIFECYCLE`: Issue transition commands to EON engines        |
+-------------------------------------------------------------------------+
```

---

## 2. Default Component Role Assignment

| Component / Client | Assigned Capabilities | Rationale |
|---|---|---|
| `eon_sensor_bridge` | `CAP_INGEST_SENSOR` | Needs only to push raw camera/audio frames |
| `eon_social_response_bridge` | `CAP_READ_OBSERVATION`, `CAP_PROPOSE_MOTION` | Reads emotional state, proposes social motions |
| `eon-cli` (Operator) | `CAP_MANAGE_LIFECYCLE`, `CAP_READ_OBSERVATION` | Diagnostics and manual engine restart |
| Privacy Service | `CAP_PURGE_CONTEXT`, `CAP_WRITE_CONTEXT` | Executes data subject deletion requests |
