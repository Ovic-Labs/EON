# ADR-001: Ten-Tier Layered Architecture Model

**Document ID:** `EON-ADR-001`  
**Status:** Approved  
**Date:** 2026-11-23  
**Deciders:** Principal Software Architect, Founder, Engineering Leads  
**Related Requirements:** `EON-FR-001`, `EON-NFR-001` through `EON-NFR-010`, `EON-SRS-001`

---

## 1. Context
OVIC EON is an emotional and social intelligence infrastructure designed to operate on autonomous robots across diverse hardware platforms (humanoids, quadrupedal, mobile service bases). The system encompasses physical sensor capture, real-time computer vision, acoustic signal processing, memory management, cognitive appraisal, conversational AI, and robotic middleware integration. Without a strict layered architectural structure, cross-cutting dependencies lead to tightly coupled, unmaintainable code that cannot be tested without physical hardware.

## 2. Problem
How should OVIC EON organize its functional subsystems to guarantee modularity, enable headless unit testing without physical sensors, prevent cyclic dependencies, and isolate physical hardware drivers from cognitive reasoning algorithms?

## 3. Decision
Adopt a **Ten-Tier Layered Architecture** grouped into four macro-planes:
1. **Perception & Physical Substrate Plane:**
   - L1: Hardware & Device Layer (Physical sensors and compute silicon)
   - L2: Device Abstraction Layer (HAL and normalized in-memory ring buffers)
   - L3: Perception Layer (Face Mesh, Silero VAD, SER, Pose tracking)
2. **Cognitive & Deliberation Plane:**
   - L4: Intelligence Engine Layer (The Seven Engines: ERS, EMS, ERE, PSE, SIE, ERG, HBU)
   - L6: Context & Memory Layer (SessionContext, WorkingMemory, Storage SPI)
   - L7: Model & Algorithm Adapter Layer (ONNX Runtime, llama.cpp, Piper TTS, Rule Engines)
3. **Orchestration & Coordination Plane:**
   - L5: EON Core Runtime Layer (EventBus, Engine Lifecycle, Health, Priority Queues)
4. **Integration, Application & Infrastructure Plane:**
   - L8: SDK & Integration Layer (Python/C++ SDK, ROS 2 Node Bridge)
   - L9: API & Application Layer (FastAPI REST, WebSockets, OpenAPI)
   - L10: Deployment & Infrastructure Layer (systemd, Docker, Cgroups, Secrets)

All dependencies flow strictly downwards, or horizontally mediated by the L5 Core Event Bus.

## 4. Alternatives Considered
1. **Monolithic 3-Tier Architecture (Perception, Brain, Actuation):** Too coarse; conflated device drivers with neural vision models, and combined event routing with cognitive algorithms, making independent engine replacement impossible.
2. **Microservices Architecture with HTTP/gRPC IPC:** Excessive latency (>5–15 ms per RPC call) and memory overhead (>1.5 GB overhead) unfeasible on edge ARM64 processors with tight latency budgets (<25 ms).

## 5. Consequences
- **Positive:** Clear separation of concerns; mockable L2 HAL enables 100% automated test coverage in virtual CI environments; cognitive engines in L4 are decoupled from inference frameworks in L7; core routing in L5 remains domain-neutral.
- **Negative:** Increased architectural surface area requiring explicit interface contracts across every adjacent layer.

## 6. Risks and Mitigations
- **Risk:** Developers may attempt to bypass adjacent layers for quick convenience.
- **Mitigation:** Enforce strict Directed Acyclic Graph (DAG) checks in CI using `import-linter`.
