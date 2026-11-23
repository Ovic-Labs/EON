"""Contract tests validating deterministic serialization and encoding stability."""

from eon.schemas.common import ModalityType, Provenance
from eon.schemas.emotions import (
    DiscreteEmotionScore,
    EmotionEstimatePayload,
    PrimaryEmotionCategory,
)
from eon.schemas.events import EmotionEstimateEvent, EventType
from eon.schemas.identifiers import generate_event_id
from eon.schemas.observations import ObservationPayload, TextObservationData
from eon.schemas.serialization import (
    deserialize_event,
    deserialize_from_json,
    serialize_to_json,
)


def test_multilingual_unicode_serialization_fidelity() -> None:
    """AC-1.2-12: Contract verifying UTF-8 multilingual text observations round-trip losslessly."""
    multilingual_text = (
        "Hello robot! こんにちは! Grüß Gott! Bonjour! 🤖 "
        "Emotion perception test with accents: café, résumé, ñ, ü, ø."
    )
    obs = ObservationPayload(
        source_id="engine.asr",
        modality=ModalityType.TEXT,
        confidence=0.98,
        provenance=Provenance(source_id="engine.asr"),
        data=TextObservationData(text=multilingual_text, language="mul"),
    )

    json_str = serialize_to_json(obs)
    recovered = deserialize_from_json(json_str, ObservationPayload)
    assert recovered.data.text == multilingual_text  # type: ignore[union-attr]


def test_json_serialization_round_trip_equality() -> None:
    """AC-1.2-12: Contract verifying model equality after JSON round trip."""
    obs_id = generate_event_id()
    payload = EmotionEstimatePayload(
        source_observation_ids=[obs_id],
        valence=-0.45,
        arousal=0.80,
        primary_category=PrimaryEmotionCategory.FEAR,
        confidence=0.78,
        uncertainty=0.22,
        discrete_scores=[
            DiscreteEmotionScore(category=PrimaryEmotionCategory.FEAR, probability=0.78),
            DiscreteEmotionScore(category=PrimaryEmotionCategory.SURPRISE, probability=0.60),
        ],
    )
    event = EmotionEstimateEvent(
        event_type=EventType.EMOTION_ESTIMATE,
        source="eon.ers",
        payload=payload,
    )

    json_str = serialize_to_json(event)
    recovered = deserialize_event(json_str)

    assert recovered == event
    assert recovered.payload == event.payload
