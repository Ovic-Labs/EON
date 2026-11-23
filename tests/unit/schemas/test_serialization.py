"""Unit tests for serialization, deserialization, and payload protection."""

import json

import pytest

from eon.schemas.common import ModalityType, Provenance
from eon.schemas.events import (
    EventType,
    ObservationEvent,
    SafetyAdvisoryEvent,
)
from eon.schemas.observations import (
    ObservationPayload,
    VisualObservationData,
)
from eon.schemas.safety import SafetyAdvisoryLevel, SafetyAdvisoryPayload
from eon.schemas.serialization import (
    MAX_PAYLOAD_SIZE_BYTES,
    deserialize_event,
    deserialize_from_dict,
    deserialize_from_json,
    serialize_to_dict,
    serialize_to_json,
)


@pytest.fixture
def sample_safety_event() -> SafetyAdvisoryEvent:
    payload = SafetyAdvisoryPayload(
        level=SafetyAdvisoryLevel.ADVISORY_CAUTION,
        advisory_code="ADV_PROXIMITY_CAUTION",
        human_readable_message="Participant in proximity.",
        reason="Observed movement.",
        recommended_action="Maintain conversational stance.",
    )
    return SafetyAdvisoryEvent(
        event_type=EventType.SAFETY_ADVISORY,
        source="eon.sie",
        payload=payload,
    )


def test_serialize_and_deserialize_round_trip(
    sample_safety_event: SafetyAdvisoryEvent,
) -> None:
    """AC-1.2-12: Verify round-trip JSON serialization and deserialization."""
    json_str = serialize_to_json(sample_safety_event)
    assert isinstance(json_str, str)
    assert "ADV_PROXIMITY_CAUTION" in json_str

    deserialized = deserialize_from_json(json_str, SafetyAdvisoryEvent)
    assert deserialized.event_id == sample_safety_event.event_id
    assert deserialized.payload.advisory_code == "ADV_PROXIMITY_CAUTION"
    assert deserialized.timestamp == sample_safety_event.timestamp


def test_dict_serialization_and_deserialization(
    sample_safety_event: SafetyAdvisoryEvent,
) -> None:
    """AC-1.2-12: Verify round-trip dictionary serialization and deserialization."""
    data_dict = serialize_to_dict(sample_safety_event)
    assert isinstance(data_dict, dict)
    assert data_dict["source"] == "eon.sie"

    deserialized = deserialize_from_dict(data_dict, SafetyAdvisoryEvent)
    assert deserialized.event_id == sample_safety_event.event_id


def test_deserialize_event_polymorphic(
    sample_safety_event: SafetyAdvisoryEvent,
) -> None:
    """AC-1.2-12: Verify polymorphic event deserializer parses concrete event class."""
    json_str = serialize_to_json(sample_safety_event)
    event = deserialize_event(json_str)

    assert isinstance(event, SafetyAdvisoryEvent)
    assert event.event_type == EventType.SAFETY_ADVISORY
    assert event.payload.advisory_code == "ADV_PROXIMITY_CAUTION"


def test_deserialize_observation_event_polymorphic() -> None:
    """Verify polymorphic deserialization of ObservationEvent."""
    obs_payload = ObservationPayload(
        source_id="sensor.camera.rgb",
        modality=ModalityType.VISUAL,
        confidence=0.9,
        provenance=Provenance(source_id="sensor.camera.rgb"),
        data=VisualObservationData(face_detected=True),
    )
    event = ObservationEvent(
        event_type=EventType.OBSERVATION,
        source="sensor.camera.rgb",
        payload=obs_payload,
    )

    json_str = serialize_to_json(event)
    deserialized = deserialize_event(json_str)
    assert isinstance(deserialized, ObservationEvent)
    assert deserialized.payload.modality == ModalityType.VISUAL


def test_deserialize_malformed_json_raises() -> None:
    """Verify malformed JSON payload raises clean ValueError."""
    with pytest.raises(ValueError) as exc:
        deserialize_from_json("{broken_json: true", SafetyAdvisoryPayload)
    assert "Malformed JSON" in str(exc.value)

    with pytest.raises(ValueError) as exc:
        deserialize_event("not even json")
    assert "Malformed JSON" in str(exc.value)


def test_deserialize_non_dict_event_raises() -> None:
    """Verify non-object JSON array or scalar raises ValueError."""
    with pytest.raises(ValueError) as exc:
        deserialize_event("[1, 2, 3]")
    assert "must be a JSON object" in str(exc.value)


def test_deserialize_unknown_event_type_raises() -> None:
    """Verify unknown event_type raises explicit error."""
    payload = {"event_type": "unknown.custom_hazard", "payload": {}}
    with pytest.raises(ValueError) as exc:
        deserialize_event(json.dumps(payload))
    assert "Unknown or unsupported event_type" in str(exc.value)

    # Missing event_type
    with pytest.raises(ValueError) as exc_missing:
        deserialize_event(json.dumps({"source": "eon.core"}))
    assert "Missing required 'event_type'" in str(exc_missing.value)


def test_oversized_payload_rejected() -> None:
    """AC-1.2-12: Verify oversized payloads exceeding 10MB are rejected."""
    huge_json = " " * (MAX_PAYLOAD_SIZE_BYTES + 10)
    with pytest.raises(ValueError) as exc:
        deserialize_from_json(huge_json, SafetyAdvisoryPayload)
    assert "exceeds maximum allowed boundary" in str(exc.value)

    with pytest.raises(ValueError) as exc2:
        deserialize_event(huge_json)
    assert "exceeds maximum allowed boundary" in str(exc2.value)


def test_type_errors_on_invalid_inputs() -> None:
    """Verify TypeError raised when wrong types are supplied."""
    with pytest.raises(TypeError):
        deserialize_from_json(12345, SafetyAdvisoryPayload)  # type: ignore[arg-type]

    with pytest.raises(TypeError):
        deserialize_from_dict(["not", "a", "dict"], SafetyAdvisoryPayload)  # type: ignore[arg-type]

    with pytest.raises(TypeError):
        deserialize_event(12345)  # type: ignore[arg-type]


def test_deserialize_from_dict_validation_failure() -> None:
    """Verify ValueError on schema validation failure during dict deserialization."""
    with pytest.raises(ValueError) as exc:
        deserialize_from_dict({"level": "invalid_level"}, SafetyAdvisoryPayload)
    assert "Schema validation failed" in str(exc.value)


def test_deserialize_all_event_types_polymorphic() -> None:
    """Verify polymorphic deserialization handles all event types."""
    from eon.schemas.base import EonBaseModel
    from eon.schemas.context import InteractionContextPayload
    from eon.schemas.emotions import (
        EmotionEstimatePayload,
        PrimaryEmotionCategory,
    )
    from eon.schemas.events import (
        ComponentHealthEvent,
        ContextUpdateEvent,
        EmotionEstimateEvent,
        EventEnvelope,
    )
    from eon.schemas.health import ComponentHealthPayload, ComponentStatus, HealthState

    # EmotionEstimateEvent
    ers_ev = EmotionEstimateEvent(
        event_type=EventType.EMOTION_ESTIMATE,
        source="eon.ers",
        payload=EmotionEstimatePayload(
            source_observation_ids=["00000000-0000-0000-0000-000000000001"],
            valence=0.5,
            arousal=0.5,
            primary_category=PrimaryEmotionCategory.JOY,
            confidence=0.9,
            uncertainty=0.1,
        ),
    )
    assert isinstance(deserialize_event(serialize_to_json(ers_ev)), EmotionEstimateEvent)

    # ContextUpdateEvent
    ctx_ev = ContextUpdateEvent(
        event_type=EventType.CONTEXT_UPDATE,
        source="eon.context",
        payload=InteractionContextPayload(session_id="session-1"),
    )
    assert isinstance(deserialize_event(serialize_to_json(ctx_ev)), ContextUpdateEvent)

    # ComponentHealthEvent
    health_ev = ComponentHealthEvent(
        event_type=EventType.COMPONENT_HEALTH,
        source="eon.core",
        payload=ComponentHealthPayload(
            component_id="eon.core",
            health_state=HealthState.HEALTHY,
            status=ComponentStatus.RUNNING,
        ),
    )
    assert isinstance(deserialize_event(serialize_to_json(health_ev)), ComponentHealthEvent)

    # Custom Event
    custom_ev = EventEnvelope[EonBaseModel](
        event_type=EventType.CUSTOM,
        source="eon.custom",
        payload=EonBaseModel(),
    )
    assert deserialize_event(serialize_to_json(custom_ev)).event_type == EventType.CUSTOM
