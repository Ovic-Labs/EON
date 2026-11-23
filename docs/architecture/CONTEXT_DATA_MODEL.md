# OVIC EON — Context Data Model Specification

**Document ID:** `EON-SPEC-CTX-001`  
**Phase:** Phase 2 — System Architecture and Engineering Design  
**Sub-phase:** 2.6 — Design Shared Context Management  
**Status:** Approved Engineering Architecture Specification  
**Version:** 1.0.0  
**Classification:** Technical Architecture Specification  
**Document Owner:** Principal Software Architect  
**Related Documents:**
- `docs/architecture/SHARED_CONTEXT_ARCHITECTURE.md` (`EON-ARCH-CTX-001`)
- `docs/architecture/CONTEXT_ACCESS_CONTROL.md` (`EON-POL-CTX-001`)

---

## 1. Executive Summary

This specification defines the typed data models, schema fields, and classification taxonomy for all categories of context in OVIC EON.

---

## 2. Eight Context Categories

```text
+=======================================================================================+
| Category               | Lifetime / Storage           | Permitted Contents            |
+=======================================================================================+
| 1. Session Context     | Session duration (RAM)       | Session ID, stage, start time |
| 2. Interaction Context | Active engagement (RAM)      | Turn counts, participant IDs  |
| 3. Short-Term Context  | Rolling window (20 turns RAM)| Recent utterances & intents   |
| 4. Long-Term Context   | Consent-gated (Encrypted DB) | Explicit verified preferences |
| 5. Environmental Ctx   | Ephemeral (RAM)              | Ambient lux, noise level dB   |
| 6. Task Context        | Task duration (RAM)          | Task frame, slot bindings     |
| 7. User Preferences    | Consent-gated (Encrypted DB) | Preferred name, volume, lang  |
| 8. Transient Obs Ctx   | < 5.0 seconds (RAM)          | Instantaneous face/voice VAD  |
+=======================================================================================+
```

---

## 3. Universal Context Schema Model

```python
class ContextRecord(EonBaseModel):
    """Universal typed container for scoped context records."""

    context_id: EventId = Field(default_factory=generate_event_id)
    context_type: str = Field(description="Category identifier, e.g. 'user_preference'.")
    schema_version: str = Field(default="1.0.0")
    scope: str = Field(description="Scope boundary, e.g. 'session_123' or 'user_456'.")
    source: str = Field(description="Originating engine or sensor node.")
    created_at: UtcTimestamp = Field(default_factory=utc_now)
    updated_at: UtcTimestamp = Field(default_factory=utc_now)
    expires_at: UtcTimestamp | None = Field(default=None, description="TTL expiration timestamp.")
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    provenance: Provenance = Field(description="Model, algorithm, and sensor origin.")
    access_classification: DataClassification = Field(default=DataClassification.INTERNAL)
    retention_policy_ref: str = Field(default="session_ephemeral")
    data_payload: dict[str, Any] = Field(description="Typed domain payload dictionary.")
```

> **Epistemological Constraint:** `confidence` represents model uncertainty, never ground truth. A confidence score of 0.95 on an emotion estimate does not mean the user's biological feeling is verified fact.
