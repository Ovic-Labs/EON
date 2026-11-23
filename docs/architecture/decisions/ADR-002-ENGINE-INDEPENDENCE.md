# ADR-002: Seven Engine Independence and Decoupling

**Document ID:** `EON-ADR-002`  
**Status:** Approved  
**Date:** 2026-11-23  
**Deciders:** Principal Software Architect, Founder, Engineering Leads  
**Related Requirements:** `EON-FR-002` through `EON-FR-020`, `EON-SRS-020` through `EON-SRS-060`

---

## 1. Context
OVIC EON divides emotional intelligence into seven core functional engines: ERS (Recognition), EMS (Memory), ERE (Empathy), PSE (Personality), SIE (Social Interaction), ERG (Response Generation), and HBU (Behavior Understanding). In complex multi-component systems, components often develop direct method call dependencies on one another, creating cascading failure risks and preventing modular deployment.

## 2. Problem
Should the seven intelligence engines be permitted to invoke each other directly via Python class methods, or must they remain completely decoupled, and how should cross-engine interaction be governed?

## 3. Decision
Enforce **Strict Engine Independence**:
1. **Zero Direct Method Invocation:** No engine in L4 may hold an object reference to, or call methods on, any other engine.
2. **Standalone Testability:** Every engine must be capable of instantiation and complete unit testing in complete isolation using mock event buses.
3. **Pluggable & Optional Engines:** Engines can be individually enabled or disabled via configuration (`eon_config.yaml`). If an optional engine is disabled (e.g. EMS episodic memory), peer engines continue operating with defined fallback behaviors.

## 4. Alternatives Considered
1. **Direct In-Memory Object References via Engine Registry:** Engines retrieve peer instances via `registry.get_engine("EMS")`. Rejected because it creates tight runtime coupling, circular call graphs, and allows one engine's uncaught exception to crash calling engines.
2. **Shared Blackboard Shared-Memory Model:** All engines read/write to a shared state object. Rejected because shared mutable state causes race conditions, lock contention, and breaks deterministic causality tracking.

## 5. Consequences
- **Positive:** Complete failure isolation; independent development by separate engineering teams; deterministic property-based testing; zero circular dependency bugs.
- **Negative:** Requires serializing and routing all cross-engine state updates through event envelopes, introducing sub-millisecond dispatch overhead.

## 6. Risks and Mitigations
- **Risk:** Event dispatch overhead might exceed latency budgets.
- **Mitigation:** The Phase 1.3 Core Event Bus delivers median routing latency of $0.038\text{ ms}$, representing $<0.5\%$ of the conversational latency budget.
