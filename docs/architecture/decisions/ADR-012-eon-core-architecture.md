# ADR-012: EON Core Architecture and Central Coordination Substrate

**Document ID:** `EON-ADR-012`  
**Status:** Approved  
**Date:** 2026-11-23  
**Deciders:** Principal Software Architect, Founder, Engineering Leads  
**Related Requirements:** `EON-FR-001`, `EON-SRS-001` through `EON-SRS-015`, `EON-ARCH-CORE-004`

---

## 1. Context
OVIC EON consists of seven independent intelligence engines (ERS, EMS, ERE, PSE, SIE, ERG, HBU) and multiple supporting platform services (HAL, Perception, Context, Model Adapters, SDK). Without a dedicated, neutral core runtime substrate, the responsibilities of engine registration, configuration distribution, event routing, lifecycle transitions, health monitoring, and graceful termination would be either fragmented across individual engines or forced into an unmaintainable monolithic architecture.

## 2. Problem
How should the central orchestration and coordination substrate of OVIC EON be architected to govern the seven engines and platform infrastructure while strictly preserving engine independence, fault isolation, and the non-authoritative actuation boundary?

## 3. Decision
Adopt **EON Core (Layer 5)** as a domain-neutral coordination substrate:
1. **Core Application Manager & Registries:** EON Core coordinates system initialization across a deterministic 12-step sequence and manages components via `ComponentRegistry` and `EngineRegistry`.
2. **Topological Dependency Resolution:** Engine startup and shutdown ordering are calculated dynamically via `DependencyResolver` using Kahn's topological sort, guaranteeing DAG execution without hardcoded startup chains.
3. **Decoupled Event Mediation:** All engine interactions are mediated through the L5 Core Event Bus. EON Core does not contain cognitive emotion reasoning logic.
4. **Failure Blast Radius Containment:** A crash or exception in an individual engine or model adapter degrades system health to `DEGRADED` but does not crash the EON process or halt safety advisory routing.
5. **Non-Authoritative Actuation Invariant:** EON Core enforces `is_authoritative_stop=False` on all outgoing actuation events.

## 4. Alternatives Considered
1. **Peer-to-Peer Distributed Coordination:** Engines coordinate amongst themselves via broadcast messages without a central Core. Rejected because decentralized consensus adds excessive latency and makes deterministic lifecycle startup/shutdown verification impossible on edge systems.
2. **Monolithic Engine Controller:** Merging Core with one of the engines (e.g. SIE or ERS). Rejected because it violates the Single Responsibility Principle and couples domain conversation logic with platform lifecycle management.

## 5. Consequences
- **Positive:** Centralized configuration, health, and lifecycle governance; guaranteed failure isolation; clean separation between platform mechanics and domain emotional intelligence.
- **Negative:** Requires strict interface contracts between Core and engines.

## 6. Risks and Mitigations
- **Risk:** Core itself becoming a single point of failure.
- **Mitigation:** Core logic is kept domain-neutral, lightweight, and heavily unit-tested with zero external network or model dependencies.
