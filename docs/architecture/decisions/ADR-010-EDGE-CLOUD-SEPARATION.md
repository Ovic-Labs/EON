# ADR-010: Edge-First Execution and Cloud Separation Boundary

**Document ID:** `EON-ADR-010`  
**Status:** Approved  
**Date:** 2026-11-23  
**Deciders:** Principal Software Architect, Founder, Engineering Leads  
**Related Requirements:** `EON-NFR-060`, `EON-PSR-030`, `EON-SRS-130`

---

## 1. Context
Many modern AI architectures depend entirely on external cloud APIs (e.g. OpenAI GPT-4, Google Gemini, ElevenLabs) for conversational reasoning and speech synthesis. In robotics, cloud dependence introduces three fatal flaws:
1. High and unpredictable network latency (300–2500 ms) destroying conversational rhythm.
2. Catastrophic complete failure when robots lose Wi-Fi/5G connectivity (elevators, basements, warehouses, outdoors).
3. Data privacy violations from streaming audio and camera streams to third-party cloud servers.

## 2. Problem
Should OVIC EON permit or require cloud connectivity for core emotional intelligence, and how should edge and cloud boundaries be defined?

## 3. Decision
Enforce strict **Edge-First Execution with Optional Cloud Separation**:
1. **Air-Gapped Autonomous Operation:** The core EON runtime (L1 through L7) operates completely self-contained on the robot's local compute hardware with zero external internet dependencies.
2. **Zero Cloud Dependencies for Core Intelligence:** Perception, affective state dynamics, empathy reasoning, turn-taking, dialogue generation, and speech synthesis run locally on edge CPUs/NPUs.
3. **Strictly Optional Cloud Extension:** Cloud connectivity is restricted to Layer 9/10 for fleet management, aggregated telemetry, and optional long-term software updates. If network interfaces are disabled, EON continues operating indefinitely with zero degradation of emotional responsiveness.

## 4. Alternatives Considered
1. **Hybrid Cloud Architecture (Perception on Edge, Dialogue in Cloud):** Rejected because internet drops cause the robot to freeze mid-conversation, creating an awkward and unsettling user experience.
2. **Cloud-Only Architecture:** Completely rejected due to unacceptable latency, bandwidth costs, and privacy non-compliance.

## 5. Consequences
- **Positive:** Deterministic sub-second conversational latency; 100% operational availability regardless of internet status; zero recurring cloud API token costs.
- **Negative:** Local SLM parameter size is constrained to $\le 1.5\text{B}$ parameters to fit within edge RAM budgets.

## 6. Risks and Mitigations
- **Risk:** Local 1.5B SLMs may have lower general reasoning capability compared to 70B+ cloud models.
- **Mitigation:** Restrict the SLM strictly to surface natural language generation while cognitive appraisal and supportive strategy selection are performed by deterministic rule engines (ERE).
