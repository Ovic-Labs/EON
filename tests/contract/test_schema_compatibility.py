"""Contract tests validating JSON schema compatibility and strict schema constraints."""

from eon.schemas.base import EonBaseModel
from eon.schemas.context import InteractionContextPayload
from eon.schemas.emotions import EmotionEstimatePayload
from eon.schemas.events import EventEnvelope, ObservationEvent
from eon.schemas.health import ComponentHealthPayload
from eon.schemas.observations import ObservationPayload
from eon.schemas.safety import SafetyAdvisoryPayload


def test_json_schema_generation_and_strict_extra_forbid() -> None:
    """AC-1.2-01, AC-1.2-11: Contract checking JSON schemas enforce additionalProperties=False."""
    target_models: list[type[EonBaseModel]] = [
        ObservationPayload,
        EmotionEstimatePayload,
        InteractionContextPayload,
        SafetyAdvisoryPayload,
        ComponentHealthPayload,
        EventEnvelope,  # type: ignore[type-abstract]
        ObservationEvent,
    ]

    for model_cls in target_models:
        schema = model_cls.model_json_schema()
        assert isinstance(schema, dict)
        assert "properties" in schema
        # In Pydantic v2, extra='forbid' sets additionalProperties=False in JSON Schema
        assert schema.get("additionalProperties") is False, (
            f"Model {model_cls.__name__} must enforce additionalProperties=False."
        )


def test_schema_required_fields_contract() -> None:
    """Verify that non-default fields are strictly listed in schema 'required'."""
    schema = EmotionEstimatePayload.model_json_schema()
    required = schema.get("required", [])
    expected_required = [
        "source_observation_ids",
        "valence",
        "arousal",
        "primary_category",
        "confidence",
        "uncertainty",
    ]
    for req in expected_required:
        assert req in required, f"Field '{req}' must be marked as required in JSON schema."
