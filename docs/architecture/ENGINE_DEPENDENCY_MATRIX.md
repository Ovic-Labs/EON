# OVIC EON — Seven Engine Dependency Matrix and Interaction Topology

**Document ID:** `EON-ARCH-DEP-002`  
**Phase:** Phase 2 — System Architecture and Engineering Design  
**Sub-phase:** 2.2 — Seven-Engine Boundary Design  
**Status:** Approved Engineering Architecture Specification  
**Version:** 1.0.0  
**Classification:** Technical Architecture Specification  
**Document Owner:** Principal Software Architect  
**Related Documents:**
- `docs/architecture/SEVEN_ENGINE_ARCHITECTURE.md` (`EON-ARCH-ENG-001`)
- `docs/architecture/ENGINE_BOUNDARY_SPECIFICATIONS.md` (`EON-SPEC-ENG-001`)
- `docs/architecture/ENGINE_INPUT_OUTPUT_CONTRACTS.md` (`EON-SPEC-ENG-IO-001`)
- `docs/architecture/ARCHITECTURE_CONSTRAINTS.md` (`EON-ARCH-CONST-001`)

---

## 1. Executive Summary

This specification establishes the authoritative cross-engine dependency topology, communication protocols, and isolation boundaries for the **Seven Intelligence Engines** of OVIC EON.

To guarantee that each engine can be developed, tested, and upgraded independently, **direct, in-process engine-to-engine coupling is strictly forbidden**. All inter-engine communication is event-driven and routed through the **L5 Core Event Bus** using typed `EventEnvelope[T]` instances.

---

## 2. Cross-Engine Interaction Matrix

The matrix below delineates the functional relationships between each pair of engines:
- **`EVENT-DEP` (Event-Based Dependency):** The consumer engine subscribes to an event topic published by the producer engine via L5 Core Event Bus.
- **`OPT-DEP` (Optional Dependency):** The consumer uses the published event when available, but functions deterministically if the producer is absent or degraded.
- **`PROHIBITED` (Forbidden Dependency):** Direct in-memory invocation, synchronous blocking call, or circular coupling is strictly forbidden.
- **`NONE`:** No direct or event-based interaction.

```text
+=======================================================================================+
| PRODUCER \ CONSUMER | ERS        | EMS        | ERE        | PSE  | SIE        | ERG      | HBU  |
+=======================================================================================+
| ERS (Emotions)      | —          | EVENT-DEP  | EVENT-DEP  | NONE | EVENT-DEP  | NONE     | NONE |
| EMS (Memory)        | NONE       | —          | OPT-DEP    | NONE | OPT-DEP    | OPT-DEP  | NONE |
| ERE (Empathy)       | NONE       | NONE       | —          | NONE | EVENT-DEP  | EVENT-DEP| NONE |
| PSE (Personality)   | NONE       | NONE       | NONE       | —    | OPT-DEP    | EVENT-DEP| NONE |
| SIE (Interaction)   | NONE       | EVENT-DEP  | EVENT-DEP  | NONE | —          | EVENT-DEP| NONE |
| ERG (Response Gen)  | NONE       | NONE       | NONE       | NONE | EVENT-DEP  | —        | NONE |
| HBU (Behavior)      | NONE       | EVENT-DEP  | EVENT-DEP  | NONE | EVENT-DEP  | NONE     | —    |
+=======================================================================================+
```

---

## 3. Direct, Event-Based, and Prohibited Dependencies

### 3.1 Direct Dependencies (Direct In-Memory Calls)
- **Status:** **STRICTLY ZERO DIRECT DEPENDENCIES.**
- **Rule:** No engine module under `src/eon/engines/<engine_a>` may import from or instantiate any class in `src/eon/engines/<engine_b>`.
- **Enforcement:** Enforced via AST static analysis in CI:
  ```python
  # FORBIDDEN:
  from eon.engines.ers import ErsEngine  # Raised as CI Architecture Violation
  ```

### 3.2 Event-Based Dependencies (Brokered via L5 Event Bus)

| Producer | Published Event Topic | Consuming Engines | Purpose & Impact |
|---|---|---|---|
| **ERS** | `emotion.estimate.realtime` | **EMS**, **ERE**, **SIE** | Updates affective state; informs appraisal; provides turn prosody |
| **HBU** | `observation.behaviour.fused` | **EMS**, **ERE**, **SIE** | Provides spatial proxemics and human gesture deictics |
| **EMS** | `ems.state.update` / Context | **ERE**, **SIE**, **ERG** | Supplies longitudinal interaction history and participant mood |
| **ERE** | `intent.empathy_reasoned` | **SIE**, **ERG** | Supplies supportive communicative strategy and dialogue goals |
| **PSE** | `persona.style.vector` | **ERG**, **SIE** | Supplies numerical style clamps (formality, verbosity, pitch) |
| **SIE** | `interaction.turn.action` | **ERG**, **EMS** | Grants conversational floor; triggers instant speech audio halt |
| **ERG** | `actuation.speech.status` | **SIE** | Reports speech start, playback progress, and speech completion |

### 3.3 Optional Dependencies and Graceful Degradation

Every event-based dependency is designed with explicit fallback behavior:

1. **If ERS is disabled or fails:**
   - ERE and SIE receive `QualityStatus.MISSING` emotion events; fall back to text sentiment and neutral baseline $(0.0, 0.0, 0.0)$.
2. **If HBU is disabled or fails:**
   - SIE operates without spatial proxemics; assumes human is at default social interaction distance ($1.5\text{ m}$).
3. **If EMS is disabled or running in ephemeral mode:**
   - ERE and ERG operate without long-term history; treat every encounter as an anonymous, context-valid session.
4. **If ERE is disabled or times out:**
   - ERG falls back to standard polite conversational templates (`"I understand, please tell me more"`).
5. **If PSE is disabled:**
   - ERG applies hardcoded default style parameters (formality = 0.70, verbosity = 0.50).

### 3.4 Prohibited Dependencies and Architectural Red Lines

1. **No Circular Event Cascades:** An engine must not publish an event that triggers an immediate, un-gated re-publication to itself.
2. **No Actuation Bypass:** ERG and HBU cannot send raw hardware command packets to motor controllers. All outputs must pass through L8 SDK / ROS 2 bridge and carry `is_authoritative_stop=False`.
3. **No Direct Hardware Access:** No engine may open Linux `/dev/video*`, `/dev/snd/*`, or serial ports directly. Hardware access is strictly owned by L1/L2.
4. **No External Cloud API Calls:** No engine may establish outbound HTTP/gRPC connections to third-party cloud AI APIs in standard local operation.

---

## 4. Shared Platform Service Dependencies

All seven engines depend on neutral infrastructure services provided by Layers 5, 6, and 7:

```text
+=======================================================================================+
| Shared Service Substrate         | Providing Layer | Consumed By All Seven Engines    |
+=======================================================================================+
| Core Event Bus (`EventBus`)      | Layer 5         | Publishing & subscribing envelopes|
| Schema Validator & Envelopes     | Layer 5 / Pydantic| Serialization & contract check |
| Component Health Supervisor      | Layer 5         | Reporting health states & errors |
| Session Context Accessor         | Layer 6         | Querying active interaction turn |
| Model Adapter Registry           | Layer 7         | Offloading tensor / model inference|
| Deterministic Rule Engine        | Layer 7         | Executing fallback templates     |
+=======================================================================================+
```

---

## 5. Dependency Topology Verification (DAG)

The engine interaction graph forms a Directed Acyclic Graph across execution stages:

```text
[ L3 Perception ] (Face Mesh, Silero VAD, SER, Pose)
       │
       ▼
  [ ERS, HBU ] (Feature Extraction & Observation Envelopes)
       │
       ▼
  [ EMS, SIE ] (State Dynamics, Memory & Turn-Taking)
       │
       ▼
  [ ERE, PSE ] (Cognitive Appraisal & Personality Clamping)
       │
       ▼
     [ ERG ] (Surface NLG & Neural Speech Synthesis)
       │
       ▼
[ L8 SDK / Robot Safety Controller ] (Advisory Speech & Motion Execution)
```

**Formal Verification Rule:** There are zero cyclic edges in the inter-engine event subscription topology. All state transitions flow monotonically from perception to response planning.
