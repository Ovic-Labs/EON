# OVIC EON — Engine Lifecycle Architecture Specification

**Document ID:** `EON-ARCH-LIFE-001`  
**Phase:** Phase 2 — System Architecture and Engineering Design  
**Sub-phase:** 2.4 — Design Engine Lifecycle  
**Status:** Approved Engineering Architecture Specification  
**Version:** 1.0.0  
**Classification:** Technical Architecture Specification  
**Document Owner:** Principal Software Architect  
**Related Documents:**
- `docs/architecture/ENGINE_LIFECYCLE_CONTRACT.md` (`EON-SPEC-LIFE-001`)
- `docs/architecture/ENGINE_STATE_TRANSITIONS.md` (`EON-ARCH-LIFE-002`)
- `docs/architecture/ENGINE_RECOVERY_AND_FAILURE_POLICIES.md` (`EON-POL-LIFE-001`)
- `docs/architecture/ENGINE_RESOURCE_DECLARATIONS.md` (`EON-SPEC-LIFE-002`)
- `docs/architecture/decisions/ADR-013-engine-lifecycle-contract.md` (`EON-ADR-013`)

---

## 1. Executive Summary

This specification defines the unified lifecycle coordination architecture governing all seven intelligence engines of OVIC EON (ERS, EMS, ERE, PSE, SIE, ERG, HBU).

A core design principle of OVIC EON is that engines must adhere to a standardized, deterministic lifecycle contract. This ensures that the central EON Core runtime can discover, validate, initialize, start, monitor, throttle, recover, and terminate engines predictably without requiring engine-specific hacks or custom lifecycle protocols.

---

## 2. Standard 11-State Engine Lifecycle

Every intelligence engine traverses an 11-state lifecycle state machine:

```text
[ DISCOVERED ]
      │  register()
      ▼
[ REGISTERED ]
      │  validate()
      ▼
[ VALIDATING ] ──(Invalid)──► [ FAILED ]
      │  (Valid)
      ▼
[ INITIALIZING ] ──(Init Error)──► [ FAILED ]
      │  initialize() OK
      ▼
[ INITIALIZED ]
      │  start()
      ▼
[ STARTING ] ──(Start Error)──► [ FAILED ]
      │  Workers active
      ▼
  [ RUNNING ] ◄────────────────────────┐
   │    │  ▲                           │
   │    │  │ recover()                 │ resume()
   │    │  ▼                           │
   │    │ [ DEGRADED ]                 │
   │    │                              │
   │    └──────► [ PAUSED ] ───────────┘
   │
   │ stop() / shutdown()
   ▼
[ STOPPING ]
      │  Queues drained
      ▼
 [ STOPPED ]
```

### State Classifications
- **Pre-Execution States:** `DISCOVERED`, `REGISTERED`, `VALIDATING`, `INITIALIZING`, `INITIALIZED`.
- **Operational States:** `STARTING`, `RUNNING`, `DEGRADED`, `PAUSED`.
- **Terminal & Fault States:** `STOPPING`, `STOPPED`, `FAILED`.

---

## 3. Dependency-Aware Startup and Shutdown Sequencing

Startup ordering is calculated dynamically by the Core `DependencyResolver` using topological sorting over declared engine dependencies:

```text
Startup Tier 1 (Sensory Ingest & Spatial):
  - HBU (Human Behaviour Understanding)
  - ERS (Emotion Recognition System)

Startup Tier 2 (State Dynamics & Interaction Coordination):
  - EMS (Emotion Modelling System / Memory)
  - SIE (Social Interaction Engine)

Startup Tier 3 (Cognitive Deliberation & Personality):
  - ERE (Empathy Reasoning Engine)
  - PSE (Personality and Social Engine)

Startup Tier 4 (Expressive Actuation):
  - ERG (Emotion Response Generation Engine)
```

**Shutdown Ordering:** Executed in the exact reverse topological order (Tier 4 -> Tier 3 -> Tier 2 -> Tier 1), ensuring that downstream consumers terminate before upstream producers cease event emissions.
