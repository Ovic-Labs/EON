# OVIC EON — Engine Lifecycle Architecture Specification

**Document ID:** `EON-ARCH-LIFE-001`  
**Phase:** Phase 2 — System Architecture and Engineering Design  
**Sub-phase:** 2.4 — Design Engine Lifecycle  
**Status:** Approved Engineering Architecture Specification  
**Version:** 2.0.0 (Authoritative Reconciled Baseline)  
**Classification:** Technical Architecture Specification  
**Document Owner:** Principal Software Architect  
**Related Documents:**  
- `docs/architecture/ENGINE_LIFECYCLE_CONTRACT.md` (`EON-SPEC-LIFE-001`)  
- `docs/architecture/ENGINE_STATE_TRANSITIONS.md` (`EON-ARCH-LIFE-002`)  
- `docs/architecture/ENGINE_RECOVERY_AND_FAILURE_POLICIES.md` (`EON-POL-LIFE-001`)  
- `docs/architecture/ENGINE_RESOURCE_DECLARATIONS.md` (`EON-SPEC-LIFE-002`)  
- `docs/architecture/decisions/ADR-013-engine-lifecycle-contract.md` (`EON-ADR-013`)  

---

## 1. Executive Summary & Authoritative Model Declaration

This specification establishes the authoritative lifecycle architecture governing all seven intelligence engines of OVIC EON (ERS, EMS, ERE, PSE, SIE, ERG, HBU).

> [!IMPORTANT]
> **AUTHORITATIVE LIFECYCLE RECONCILIATION:**  
> The EON runtime establishes a strict distinction between:  
> 1. **The Internal 11-State Engine Lifecycle FSM:** The authoritative, granular state machine executed by the EON Core kernel supervisor to manage discovery, validation, resource allocation, concurrency, failure isolation, and graceful teardown.  
> 2. **The External 7-State Operational Health Projection:** A simplified, coarse-grained state view exposed to remote API clients, teleoperation dashboards, and the Python SDK (`EngineState`), shielding external callers from transient startup sub-phases.  
> Earlier text describing the operational model as "six states but listing seven" was an editorial typographical error; the operational health projection model defines exactly **seven** states (`UNINITIALIZED`, `INITIALIZING`, `ACTIVE`, `PAUSED`, `DEGRADED`, `STOPPED`, `FAULTED`).

---

## 2. Standard 11-State Engine Lifecycle Model

Every intelligence engine adheres to the following 11-state finite state machine (with `FAILED` as the terminal fault state):

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

---

## 3. Formal State Definitions

| State ID | Name | Classification | Formal Definition & Invariant |
| :---: | :--- | :--- | :--- |
| **S1** | `DISCOVERED` | Pre-Execution | Engine class or entrypoint identified on disk; metadata unverified; no resources allocated. |
| **S2** | `REGISTERED` | Pre-Execution | Engine metadata accepted by Core Engine Registry; engine ID recognized; capability tags verified. |
| **S3** | `VALIDATING` | Pre-Execution | Actively verifying runtime configuration, schema compliance, hardware dependencies, and topic contracts. |
| **S4** | `INITIALIZING`| Pre-Execution | Allocating queues, subscribing to EventBroker, creating worker threads, and loading neural adapters. |
| **S5** | `INITIALIZED` | Pre-Execution | All resources allocated and verified; event listeners registered; ready to begin event consumption. |
| **S6** | `STARTING` | Operational | Workers actively starting up and verifying healthy loop execution within configured timeout. |
| **S7** | `RUNNING` | Operational | Actively processing events and observations within nominal error and latency budgets. |
| **S8** | `DEGRADED` | Operational | Operating with reduced capability (e.g. fallback CPU model active, dropped frame rate, high latency). |
| **S9** | `PAUSED` | Operational | Worker loops suspended; in-flight queues preserved without discarding items; robot idle or docked. |
| **S10**| `STOPPING` | Teardown | Graceful termination sequence: subscriptions unsubscribed, worker queues draining up to deadline. |
| **S11**| `STOPPED` | Terminal | Cleanly shut down; all threads terminated, memory buffers released; safe to reload or discard. |
| **SF** | `FAILED` | Terminal Fault | Unrecoverable fault, failed validation, initialization timeout, or exhausted recovery attempts. |

---

## 4. Operational Health Projection (7-State External View)

External APIs (`GET /api/v1/engines`), telemetry exporters, and the Python SDK (`eon.models.lifecycle.EngineState`) expose the **7-State Operational Health Projection**:

| Operational Health State | Mapped Internal Lifecycle States | Description for External Callers |
| :--- | :--- | :--- |
| `UNINITIALIZED` | `DISCOVERED`, `REGISTERED` | Engine registered with kernel but not yet initialized. |
| `INITIALIZING` | `VALIDATING`, `INITIALIZING`, `INITIALIZED`, `STARTING` | Engine undergoing configuration validation and resource setup. |
| `ACTIVE` | `RUNNING` | Engine fully operational and healthy. |
| `PAUSED` | `PAUSED` | Engine temporarily suspended by operator or robot docking policy. |
| `DEGRADED` | `DEGRADED` | Engine functioning under fallback mode or elevated error rate. |
| `STOPPED` | `STOPPING`, `STOPPED` | Engine gracefully shut down or undergoing teardown. |
| `FAULTED` | `FAILED` | Engine faulted and requiring operator or supervisory reset. |

---

## 5. Failure States & Three-Tier Recovery Policies

When an engine enters `DEGRADED` or experiences runtime anomalies:

1. **Tier 1 (In-Process Worker Restart):**
   - The engine attempts to restart hung worker threads and flush congested in-flight queues.
   - Guard: Allowed once within a 60-second sliding window.
2. **Tier 2 (Model Fallback Downgrade):**
   - If inference fails or hardware accelerators fault, the engine switches to the quantized CPU fallback adapter (`EON-SPEC-MOD-003`).
   - Guard: Latency target increases; engine state remains `DEGRADED` with notification emitted to Core.
3. **Tier 3 (Supervisory Escalation & Circuit Breaking):**
   - If 3 consecutive recovery attempts fail within 120 seconds, the engine transitions to `FAILED`.
   - Core isolates the engine's event subscriptions to prevent cascading bus failure.

---

## 6. Dependency-Aware Startup and Shutdown Sequencing

Startup ordering is calculated dynamically via topological sorting over declared engine dependencies (`EON-ARCH-DEP-002`):

```text
Startup Tier 1 (Sensory Ingest & Spatial Foundation):
  - HBU (Human Behaviour Understanding)
  - ERS (Emotion Recognition System)

Startup Tier 2 (State Dynamics & Interaction Coordination):
  - EMS (Emotional Memory System)
  - SIE (Social Interaction Engine)

Startup Tier 3 (Cognitive Deliberation & Personality):
  - ERE (Empathy Reasoning Engine)
  - PSE (Personality Simulation Engine)

Startup Tier 4 (Expressive Actuation Planning):
  - ERG (Emotional Response Generation Engine)
```

**Shutdown Ordering:** Executed in the exact reverse topological sequence (Tier 4 -> Tier 3 -> Tier 2 -> Tier 1), ensuring downstream consumer engines terminate cleanly before upstream event producers shut down.
