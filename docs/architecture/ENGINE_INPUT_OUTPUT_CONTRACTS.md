# OVIC EON — Seven Engine Input and Output Contracts

**Document ID:** `EON-SPEC-ENG-IO-001`  
**Phase:** Phase 2 — System Architecture and Engineering Design  
**Sub-phase:** 2.2 — Seven-Engine Boundary Design  
**Status:** Approved Engineering Architecture Specification  
**Version:** 1.0.0  
**Classification:** Technical Architecture Specification  
**Document Owner:** Principal Software Architect  
**Related Documents:**
- `docs/architecture/SEVEN_ENGINE_ARCHITECTURE.md` (`EON-ARCH-ENG-001`)
- `docs/architecture/ENGINE_BOUNDARY_SPECIFICATIONS.md` (`EON-SPEC-ENG-001`)
- `docs/architecture/ENGINE_DEPENDENCY_MATRIX.md` (`EON-ARCH-DEP-002`)
- `docs/architecture/EVENT_ENVELOPE_SPECIFICATION.md` (`EON-SPEC-ENV-001`)
- `docs/architecture/DATA_SCHEMA_ARCHITECTURE.md` (`EON-ARCH-SCHEMA-001`)

---

## 1. Executive Summary

This specification establishes the exhaustive data contracts, event schemas, payload definitions, and field constraints governing all input and output data exchanged across OVIC EON's seven core intelligence engines.

All data payloads in OVIC EON are defined using **Pydantic v2** models, serialized to UTF-8 JSON, and wrapped in strongly typed `EventEnvelope[PayloadT]` containers. This document maps existing qualified Phase 1.2 schemas and formally defines proposed new contracts required for Phase 2 implementation.

---

## 2. Schema Inventory and Qualification Status

```text
+=======================================================================================+
| Contract Name                 | Schema Package / Location        | Phase Status       |
+=======================================================================================+
| `ObservationPayload`          | `eon.schemas.observations`       | Qualified (Ph 1.2) |
| `EmotionEstimatePayload`      | `eon.schemas.emotions`           | Qualified (Ph 1.2) |
| `InteractionContextPayload`   | `eon.schemas.context`            | Qualified (Ph 1.2) |
| `SafetyAdvisoryPayload`       | `eon.schemas.safety`             | Qualified (Ph 1.2) |
| `ComponentHealthPayload`      | `eon.schemas.health`             | Qualified (Ph 1.2) |
| `ResponseIntentPayload`       | `eon.schemas.intents` (Proposed) | Proposed (Ph 2.2)  |
| `PersonaStylePayload`         | `eon.schemas.persona` (Proposed) | Proposed (Ph 2.2)  |
| `TurnActionPayload`           | `eon.schemas.interaction` (Prop) | Proposed (Ph 2.2)  |
| `ResponseProposalPayload`     | `eon.schemas.responses` (Prop)   | Proposed (Ph 2.2)  |
| `AudioPlaybackChunkPayload`   | `eon.schemas.actuation` (Prop)   | Proposed (Ph 2.2)  |
| `KinesicIntentPayload`        | `eon.schemas.actuation` (Prop)   | Proposed (Ph 2.2)  |
| `MemoryRecordPayload`         | `eon.schemas.memory` (Proposed)  | Proposed (Ph 2.2)  |
+=======================================================================================+
```

---

## 3. Existing Qualified Phase 1.2 Schemas (Reused Verbatim)

### 3.1 `ObservationPayload` (`eon.schemas.observations`)
Used as primary input to **ERS**, **EMS**, and **HBU**.
- `observation_id: EventId` (UUID4)
- `source_id: SourceId` (Originating sensor node)
- `observed_at: UtcTimestamp` (Timezone-aware UTC)
- `received_at: UtcTimestamp` (Ingestion timestamp)
- `modality: ModalityType` (`VISUAL`, `AUDIO`, `TEXT`, `BEHAVIOURAL`, `MULTIMODAL`)
- `confidence: ConfidenceScore` ($[0.0, 1.0]$)
- `quality: QualityStatus` (`GOOD`, `DEGRADED`, `UNRELIABLE`, `MISSING`)
- `data: ObservationDataUnion` (`VisualObservationData`, `AudioObservationData`, etc.)
- `provenance: Provenance` (Algorithm, pipeline, version metadata)

### 3.2 `EmotionEstimatePayload` (`eon.schemas.emotions`)
Published by **ERS**; consumed by **EMS**, **ERE**, and **SIE**.
- `estimate_id: EventId` (UUID4)
- `source_id: SourceId` (e.g. `"eon.engine.ers"`)
- `estimated_at: UtcTimestamp`
- `valence: ValenceScore` ($[-1.0, +1.0]$)
- `arousal: ArousalScore` ($[-1.0, +1.0]$)
- `dominance: DominanceScore` ($[-1.0, +1.0]$)
- `discrete_emotions: list[DiscreteEmotionScore]` (Category and score in $[0.0, 1.0]$)
- `primary_category: PrimaryEmotionCategory`
- `confidence: ConfidenceScore`
- `conflict_flag: bool` (Asserted when modalities diverge)
- `modality_quality_scores: dict[str, float]`

### 3.3 `InteractionContextPayload` (`eon.schemas.context`)
Shared across **SIE**, **EMS**, **PSE**, and **ERE**.
- `session_id: SessionId`
- `stage: InteractionStage` (12 stages)
- `participants: list[ParticipantContext]`
- `environment: EnvironmentContext`
- `active_turn_count: int`
- `updated_at: UtcTimestamp`

---

## 4. Proposed New Schema Specifications (Phase 2.2 Scope)

The following schemas are formally specified for implementation during Phase 2.

### 4.1 `ResponseIntentPayload` (`eon.schemas.intents`)
Published by **ERE**; consumed by **SIE** and **ERG**.

```python
class IntentCategory(str, Enum):
    SUPPORTIVE_ASSISTANCE = "supportive_assistance"
    ACTIVE_LISTENING = "active_listening"
    CLARIFICATION_REQUEST = "clarification_request"
    EMOTIONAL_REASSURANCE = "emotional_reassurance"
    TASK_GUIDANCE = "task_guidance"
    POLITE_ACKNOWLEDGMENT = "polite_acknowledgment"
    BOUNDARY_ENFORCEMENT = "boundary_enforcement"


class ResponseIntentPayload(EonBaseModel):
    """Communicative intent formulated by Empathy Reasoning Engine."""

    intent_id: EventId = Field(default_factory=generate_event_id)
    causation_id: EventId = Field(description="Observation ID that triggered this intent.")
    source_engine: str = Field(default="ERE", pattern=r"^[A-Z0-9_-]+$")
    created_at: UtcTimestamp = Field(default_factory=utc_now)
    category: IntentCategory = Field(description="High-level communicative intent category.")
    semantic_goal: str = Field(description="Descriptive goal for natural language generation.")
    empathy_strategy: str = Field(description="Declared empathy policy, e.g. reflective_listening.")
    priority: EventPriority = Field(default=EventPriority.NORMAL)
    context_tags: list[str] = Field(default_factory=list)
    is_authoritative_stop: bool = Field(
        default=False,
        description="Must always be False; EON outputs are strictly advisory.",
    )

    @field_validator("is_authoritative_stop")
    @classmethod
    def validate_non_authoritative(cls, v: bool) -> bool:
        if v is not False:
            raise ValueError("EON intents must never assert authoritative stop authority.")
        return v
```

### 4.2 `PersonaStylePayload` (`eon.schemas.persona`)
Published by **PSE**; consumed by **ERG**.

```python
class PersonaStylePayload(EonBaseModel):
    """Clamped behavioral and vocal style vector published by PSE."""

    style_id: EventId = Field(default_factory=generate_event_id)
    source_engine: str = Field(default="PSE")
    persona_id: str = Field(description="Active base persona profile identifier.")
    formality: float = Field(
        ge=0.0, le=1.0, description="0.0 = casual/colloquial, 1.0 = formal/academic."
    )
    verbosity: float = Field(ge=0.0, le=1.0, description="0.0 = terse/concise, 1.0 = elaborative.")
    pace_multiplier: float = Field(ge=0.8, le=1.3, description="Speech rate scaling factor.")
    pitch_offset_semitones: float = Field(ge=-4.0, le=4.0, description="Prosodic pitch shift.")
    warmth_bias: float = Field(ge=0.0, le=1.0, description="Empathetic warmth modulation.")
    safety_clamps_enforced: bool = Field(default=True)
    created_at: UtcTimestamp = Field(default_factory=utc_now)
```

### 4.3 `TurnActionPayload` (`eon.schemas.interaction`)
Published by **SIE**; consumed by **ERG** and **EMS**.

```python
class TurnCommand(str, Enum):
    TAKE_FLOOR = "take_floor"
    YIELD_FLOOR = "yield_floor"
    INSTANT_AUDIO_HALT = "instant_audio_halt"
    BACKCHANNEL = "backchannel"
    WAIT = "wait"


class TurnActionPayload(EonBaseModel):
    """Conversational floor and turn arbitration directive from SIE."""

    turn_id: EventId = Field(default_factory=generate_event_id)
    source_engine: str = Field(default="SIE")
    command: TurnCommand = Field(description="Turn-taking directive.")
    current_stage: InteractionStage = Field(description="Active 12-stage interaction state.")
    trp_score: float = Field(ge=0.0, le=1.0, description="Transition Relevance Place confidence.")
    barge_in_detected: bool = Field(default=False)
    created_at: UtcTimestamp = Field(default_factory=utc_now)
```

### 4.4 `ResponseProposalPayload` (`eon.schemas.responses`)
Published by **ERG**; consumed by L8 SDK and host robot controllers.

```python
class ResponseProposalPayload(EonBaseModel):
    """Multimodal dialogue and expressive proposal formulated by ERG."""

    proposal_id: EventId = Field(default_factory=generate_event_id)
    intent_id: EventId = Field(description="Originating ERE intent ID.")
    text_content: str = Field(description="Synthesized surface text utterance.")
    audio_stream_topic: str | None = Field(
        default=None, description="Topic streaming 16kHz PCM audio."
    )
    estimated_duration_seconds: float = Field(gt=0.0)
    visemes: list[dict[str, Any]] = Field(
        default_factory=list, description="Timestamped phoneme visemes."
    )
    advisory_gestures: list[dict[str, Any]] = Field(
        default_factory=list, description="Advisory head/arm targets."
    )
    is_authoritative_stop: bool = Field(default=False)
    created_at: UtcTimestamp = Field(default_factory=utc_now)

    @field_validator("is_authoritative_stop")
    @classmethod
    def validate_non_authoritative(cls, v: bool) -> bool:
        if v is not False:
            raise ValueError("Response proposals must never assert authoritative stop authority.")
        return v
```

### 4.5 `MemoryRecordPayload` (`eon.schemas.memory`)
Managed by **EMS** in L6 Context & Memory.

```python
class MemoryTier(str, Enum):
    WORKING = "working"
    EPISODIC = "episodic"
    SEMANTIC = "semantic"


class MemoryRecordPayload(EonBaseModel):
    """Governed interaction memory record."""

    memory_id: EventId = Field(default_factory=generate_event_id)
    user_id: str = Field(description="Pseudonymous user identifier.")
    session_id: SessionId
    tier: MemoryTier
    created_at: UtcTimestamp = Field(default_factory=utc_now)
    expires_at: UtcTimestamp | None = Field(
        default=None, description="TTL expiration for episodic memory."
    )
    consent_scope: str = Field(description="User-approved data retention scope.")
    content_summary: str = Field(description="Structured, scrubbed factual summary.")
    is_user_editable: bool = Field(default=True)
```

---

## 5. Schema Validation and Serialization Rules

1. **Strict Pydantic v2 Parsing:** All models derive from `eon.schemas.base.EonBaseModel`, configured with `extra="forbid"` to prevent unrecognized fields.
2. **Deterministic ISO 8601 Timestamps:** All timestamps must use UTC timezone notation (`2026-11-23T18:00:00.000000Z`).
3. **Envelope Compatibility:** Every payload model must be capable of serialization inside `EventEnvelope[PayloadT]`.
4. **Backward Compatibility:** All proposed additions maintain SemVer 2.0.0 rules defined in `SCHEMA_VERSIONING_POLICY.md`.
