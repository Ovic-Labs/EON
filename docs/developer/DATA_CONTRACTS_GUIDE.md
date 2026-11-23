# OVIC EON — Developer Guide to Data Contracts and Event Envelopes

**Document ID:** EON-DEV-SCHEMA-001  
**Product:** OVIC EON  
**Tagline:** Emotional Intelligence Infrastructure for Robotics  
**Organization:** OVIC Labs  
**Target Milestone:** Phase 1.2 — Data Schemas and Event Envelopes  
**Status:** `QUALIFIED AND VERIFIED`  
**Date:** 2026-11-23  

---

## 1. Quickstart

All OVIC EON data models and event envelopes are exposed through the top-level package `eon.schemas`.

```python
from eon.schemas import (
    # Common & Base
    EonBaseModel,
    ModalityType,
    Provenance,
    # Identifiers & Timestamps
    generate_correlation_id,
    generate_session_id,
    utc_now,
    # Observations
    ObservationEvent,
    ObservationPayload,
    VisualObservationData,
    # Emotions
    EmotionEstimateEvent,
    EmotionEstimatePayload,
    PrimaryEmotionCategory,
    # Context
    ContextUpdateEvent,
    InteractionContextPayload,
    InteractionStage,
    # Safety
    SafetyAdvisoryEvent,
    SafetyAdvisoryLevel,
    SafetyAdvisoryPayload,
    # Serialization
    deserialize_event,
    serialize_to_json,
)
```

---

## 2. Working with Observations

Observations record perceptual information extracted by cameras, microphones, or sensor adapters.

### Example: Emitting a Visual Observation Event
```python
# 1. Define perceptual observation data (strictly derived features, no raw pixels)
vis_data = VisualObservationData(
    face_detected=True,
    face_bounding_box=(0.15, 0.20, 0.45, 0.65),  # (x_min, y_min, x_max, y_max)
    head_pose_yaw=12.5,
    head_pose_pitch=-4.2,
    facial_action_units={"AU12": 0.85, "AU06": 0.70},  # Lip corner puller, cheek raiser
)

# 2. Package into an ObservationPayload
obs_payload = ObservationPayload(
    source_id="sensor.camera.rgb",
    modality=ModalityType.VISUAL,
    confidence=0.92,
    provenance=Provenance(
        source_id="sensor.camera.rgb",
        capture_device="realsense_d435",
        model_name="face_mesh_v2",
    ),
    data=vis_data,
)

# 3. Wrap in a universal EventEnvelope
obs_event = ObservationEvent(
    event_type="eon.observation",
    source="sensor.camera.rgb",
    payload=obs_payload,
)

print(f"Observation Event ID: {obs_event.event_id}")
print(f"Timestamp (UTC): {obs_event.timestamp.isoformat()}")
```

---

## 3. Working with Emotion Estimates

Emotion estimates communicate probabilistic affective assessments derived from upstream observations.

### Example: Emitting an Emotion Estimate Event
```python
# Create an emotion estimate with explicit confidence, uncertainty, and disclaimer
emotion_payload = EmotionEstimatePayload(
    source_observation_ids=[obs_event.event_id],  # Provenance link to source observation
    valence=0.75,  # Normalized in [-1.0, 1.0]
    arousal=0.45,  # Normalized in [-1.0, 1.0]
    dominance=0.10,  # Optional in [-1.0, 1.0]
    primary_category=PrimaryEmotionCategory.JOY,
    confidence=0.88,  # Normalized in [0.0, 1.0]
    uncertainty=0.12,  # Normalized in [0.0, 1.0]
    model_metadata={"engine": "eon.ers", "calibration": "balanced"},
)

# Envelope with causality tracking
emotion_event = EmotionEstimateEvent(
    event_type="eon.emotion_estimate",
    source="eon.ers",
    metadata={
        "correlation_id": obs_event.metadata.correlation_id,
        "causation_id": obs_event.event_id,
    },
    payload=emotion_payload,
)

print(f"Primary Emotion: {emotion_event.payload.primary_category.value}")
print(f"Ethical Disclaimer: {emotion_event.payload.disclaimer}")
```

---

## 4. Working with Interaction Context

Context captures the state of the interaction, conversational turn, and participants.

### Example: Updating Context
```python
ctx_payload = InteractionContextPayload(
    session_id="session_healthcare_ward_101",
    interaction_stage=InteractionStage.ACTIVE_DIALOGUE,
    participants=[
        {
            "participant_id": "user_pseudonym_alpha",
            "role": "primary_patient",
            "interaction_count": 4,
        }
    ],
    environment={
        "location_type": "hospital_ward",
        "noise_level": "moderate",
        "social_setting": "one_on_one",
    },
)

ctx_event = ContextUpdateEvent(
    event_type="eon.context_update",
    source="eon.core.context",
    metadata={"causation_id": emotion_event.event_id},
    payload=ctx_payload,
)
```

---

## 5. Working with Safety Advisories

EON communicates social and behavioral safety cues to the host robotics platform.

> [!CAUTION]
> **Safety Authority Boundary:**  
> EON is not the robot's certified safety controller. EON models strictly reject attempts to set `is_authoritative_stop=True`. Motion commands must never be generated from this package.

### Example: Emitting a Safety Advisory
```python
safety_payload = SafetyAdvisoryPayload(
    level=SafetyAdvisoryLevel.ADVISORY_PAUSE,
    advisory_code="ADV_PROXIMITY_OVERRUN",
    human_readable_message="Human interactor approached within 0.5m during speech.",
    reason="Sudden proximity change detected in behavioral stream.",
    recommended_action="Cease active conversational gestures; recommend static stance.",
    is_authoritative_stop=False,  # Enforced False
)

safety_event = SafetyAdvisoryEvent(
    event_type="eon.safety_advisory",
    source="eon.sie",
    metadata={"causation_id": ctx_event.event_id},
    payload=safety_payload,
)
```

---

## 6. Serialization and Deserialization

Never use `pickle`. Use the built-in, type-safe serialization utilities:

```python
# Serialize to canonical JSON string
json_str = serialize_to_json(safety_event, indent=2)

# Polymorphic deserialization: automatically parses concrete SafetyAdvisoryEvent
recovered_event = deserialize_event(json_str)

assert isinstance(recovered_event, SafetyAdvisoryEvent)
assert recovered_event.payload.advisory_code == "ADV_PROXIMITY_OVERRUN"
```

---

## 7. Developer Rules and Invariants

1. **Immutability:** Modifying any model attribute after construction raises `ValidationError`.
2. **Strict Fields:** Passing unexpected dictionary keys raises `ValidationError` (`extra='forbid'`).
3. **UTC Timestamps:** All datetime fields must be timezone-aware; naive datetimes are rejected.
4. **Ranges:** Numerical fields (valence, arousal, confidence, uncertainty) are strictly checked against mathematical bounds.
5. **Ethical Disclaimers:** Emotion payloads embed a mandatory ethical disclaimer; stripping it is prohibited by validation rules.
