# OVIC EON — Event Taxonomy Specification

**Document ID:** `EON-SPEC-COMM-001`  
**Phase:** Phase 2 — System Architecture and Engineering Design  
**Sub-phase:** 2.5 — Design Event-Driven Communication  
**Status:** Approved Engineering Architecture Specification  
**Version:** 1.0.0  
**Classification:** Technical Architecture Specification  
**Document Owner:** Principal Software Architect  
**Related Documents:**
- `docs/architecture/EVENT_DRIVEN_COMMUNICATION.md` (`EON-ARCH-COMM-001`)
- `docs/architecture/EVENT_ENVELOPE_SPECIFICATION.md` (`EON-SPEC-ENV-001`)

---

## 1. Executive Summary

This specification establishes the official event taxonomy and dot-notation topic hierarchy for OVIC EON.

---

## 2. Event Category Hierarchy

```text
+=======================================================================================+
| Category               | Canonical Topic Prefix       | Payload Schema                |
+=======================================================================================+
| System Lifecycle       | `system.lifecycle.*`         | CoreLifecyclePayload          |
| Engine Lifecycle       | `engine.lifecycle.*`         | ComponentHealthPayload        |
| Perception Observations| `observation.<modality>.*`   | ObservationPayload            |
| Emotion Estimates      | `emotion.estimate.*`         | EmotionEstimatePayload        |
| Context Updates        | `context.session.*`          | InteractionContextPayload     |
| Social Reasoning       | `intent.empathy_reasoned`    | ResponseIntentPayload         |
| Turn-Taking Actions    | `interaction.turn.*`         | TurnActionPayload             |
| Response Proposals     | `actuation.proposal.*`       | ResponseProposalPayload       |
| Speech Streaming Audio | `actuation.speech.*`         | AudioPlaybackChunkPayload     |
| Component Health       | `health.<component_id>`      | ComponentHealthPayload        |
| Safety Advisories      | `safety.advisory.*`          | SafetyAdvisoryPayload         |
| Security & Audit       | `security.audit.*`           | SecurityAuditPayload          |
+=======================================================================================+
```

---

## 3. Strict Semantic Demarcation: Observations vs. Verified Facts

A non-negotiable principle of OVIC EON is that **emotion-related outputs are uncertain probabilistic observations, not verified ground truth**:
- Topics under `observation.*` and `emotion.estimate.*` express probabilistic machine learning estimates with required `confidence` and `quality` indicators.
- Inferences made by ERS must never be classified as clinical, psychiatric, or legally definitive facts.
