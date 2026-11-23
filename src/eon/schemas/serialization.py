"""Safe serialization and deserialization utilities for OVIC EON schemas."""

import json
from typing import Any, Final, TypeVar

from pydantic import ValidationError

from eon.schemas.base import EonBaseModel
from eon.schemas.events import (
    ComponentHealthEvent,
    ContextUpdateEvent,
    EmotionEstimateEvent,
    EventEnvelope,
    EventType,
    ObservationEvent,
    SafetyAdvisoryEvent,
)

T = TypeVar("T", bound=EonBaseModel)

# Default upper bound on raw JSON string length to guard against memory exhaustion (10 MB)
MAX_PAYLOAD_SIZE_BYTES: Final[int] = 10 * 1024 * 1024


def serialize_to_json(model: EonBaseModel, indent: int | None = None) -> str:
    """Serialize any EON schema model to a canonical JSON string.

    Never utilizes pickle or unsafe object serializers.
    """
    return model.model_dump_json(indent=indent)


def serialize_to_dict(model: EonBaseModel) -> dict[str, Any]:
    """Serialize any EON schema model to a standard Python dictionary."""
    return model.model_dump(mode="python")


def deserialize_from_json(json_str: str, model_cls: type[T]) -> T:
    """Safely deserialize a JSON string into an explicit EON schema model.

    Validates schema rules, enforces extra='forbid', and rejects oversized or malformed payloads.
    """
    if not isinstance(json_str, str):
        raise TypeError(f"Expected str input for json_str, received {type(json_str).__name__}")

    if len(json_str.encode("utf-8")) > MAX_PAYLOAD_SIZE_BYTES:
        raise ValueError(
            f"Payload size exceeds maximum allowed boundary of {MAX_PAYLOAD_SIZE_BYTES} bytes."
        )

    try:
        raw_dict = json.loads(json_str)
    except (json.JSONDecodeError, ValueError) as e:
        raise ValueError(f"Malformed JSON payload: {e}") from e

    return deserialize_from_dict(raw_dict, model_cls)


def deserialize_from_dict(data: dict[str, Any], model_cls: type[T]) -> T:
    """Safely deserialize a Python dictionary into an explicit EON schema model."""
    if not isinstance(data, dict):
        raise TypeError(f"Expected dict input for data, received {type(data).__name__}")

    try:
        return model_cls.model_validate(data)
    except ValidationError as e:
        raise ValueError(f"Schema validation failed for {model_cls.__name__}: {e}") from e


def deserialize_event(json_str: str) -> EventEnvelope[Any]:
    """Polymorphically deserialize a JSON event string into its concrete event envelope.

    Inspects `event_type` safely without arbitrary class loading, then delegates
    to the corresponding strongly typed event class.
    """
    if not isinstance(json_str, str):
        raise TypeError(f"Expected str input for json_str, received {type(json_str).__name__}")

    if len(json_str.encode("utf-8")) > MAX_PAYLOAD_SIZE_BYTES:
        raise ValueError(
            f"Payload size exceeds maximum allowed boundary of {MAX_PAYLOAD_SIZE_BYTES} bytes."
        )

    try:
        raw_dict = json.loads(json_str)
    except json.JSONDecodeError as e:
        raise ValueError(f"Malformed JSON payload: {e}") from e

    if not isinstance(raw_dict, dict):
        raise ValueError("Event payload must be a JSON object.")

    event_type_str = raw_dict.get("event_type")
    if not event_type_str:
        raise ValueError("Missing required 'event_type' field in event envelope.")

    try:
        event_type = EventType(event_type_str)
    except ValueError as e:
        raise ValueError(
            f"Unknown or unsupported event_type '{event_type_str}'. "
            f"Supported types: {[t.value for t in EventType]}"
        ) from e

    match event_type:
        case EventType.OBSERVATION:
            return deserialize_from_dict(raw_dict, ObservationEvent)
        case EventType.EMOTION_ESTIMATE:
            return deserialize_from_dict(raw_dict, EmotionEstimateEvent)
        case EventType.CONTEXT_UPDATE:
            return deserialize_from_dict(raw_dict, ContextUpdateEvent)
        case EventType.SAFETY_ADVISORY:
            return deserialize_from_dict(raw_dict, SafetyAdvisoryEvent)
        case EventType.COMPONENT_HEALTH:
            return deserialize_from_dict(raw_dict, ComponentHealthEvent)
        case EventType.CUSTOM:
            # Custom events require explicit envelope validation
            return deserialize_from_dict(raw_dict, EventEnvelope[EonBaseModel])
