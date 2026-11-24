# ADR-024: Optional Cloud Architecture and Edge Synchronization

**Document ID:** `EON-ADR-024`  
**Date:** 2026-11-24  
**Status:** `APPROVED`  
**Deciders:** Antigravity Engineering Architecture Team  
**Scope:** Distributed Systems, Cloud Architecture, Fleet Telemetry  

---

## 1. Context and Problem Statement

Enterprise robotics fleets require aggregate monitoring, firmware distribution, and cross-robot context synchronization. However, making cloud connectivity mandatory creates points of failure, breaks in network-denied environments, and introduces severe cloud streaming costs and privacy risks.

## 2. Decision

We decide to specify an **Optional Cloud Architecture**:
1. EON Core and all 7 intelligence engines operate 100% autonomously on the edge robot with zero cloud dependencies.
2. Cloud connectivity is strictly optional, utilized only for fleet diagnostics, model artifact distribution, and consented cross-robot context sync.
3. Raw camera feeds and raw microphone audio are **never transmitted to the cloud** by default.
4. Edge-to-cloud synchronization uses an asynchronous store-and-forward SQLite queue with CRDT / vector clock conflict resolution.
5. Strict multi-tenant isolation via mTLS device certificates, schema-per-tenant, and customer-managed KMS keys.

## 3. Alternatives Considered

- *Alternative A: Cloud-Centric AI Inference (Streaming Video to Cloud LLMs/VLM).* Rejected: Prohibitive bandwidth costs ($>\$500\text{/month}$), high latency, and complete failure upon WiFi loss.
- *Alternative B: No Cloud Architecture.* Rejected: Precludes enterprise fleet management and cross-robot memory.

## 4. Consequences and Implications

- **Positive:** Complete edge autonomy, minimal cloud egress costs (~$1.50/robot/month), and strict privacy compliance.
- **Negative:** Requires local model execution on edge hardware.
- **Security Implications:** mTLS authentication and per-tenant cryptographic isolation.
- **Privacy Implications:** Unbypassable edge privacy filter dropping raw media before cloud transmission.
- **Performance Implications:** Zero impact on real-time edge control loops during network dropouts.
- **Related ADRs:** ADR-010, ADR-018, ADR-025, ADR-026.
- **Supersession History:** None.
