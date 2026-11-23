"""Unit tests for identifier types, formats, and generators."""

import uuid

import pytest
from pydantic import BaseModel, ValidationError

from eon.schemas.identifiers import (
    CausationId,
    CorrelationId,
    EventId,
    SessionId,
    SourceId,
    generate_causation_id,
    generate_correlation_id,
    generate_event_id,
    generate_session_id,
    validate_session_id,
    validate_source_id,
    validate_uuid_string,
)


class DummyIdentifierModel(BaseModel):
    event_id: EventId
    correlation_id: CorrelationId | None = None
    causation_id: CausationId | None = None
    session_id: SessionId | None = None
    source_id: SourceId


def test_generators_produce_valid_uuids() -> None:
    """AC-1.2-02: Verify generators return valid UUID4 strings."""
    eid = generate_event_id()
    cid = generate_correlation_id()
    caus_id = generate_causation_id()
    sid = generate_session_id()

    for item in [eid, cid, caus_id, sid]:
        parsed = uuid.UUID(item, version=4)
        assert str(parsed) == item


def test_generator_uniqueness() -> None:
    """AC-1.2-02: Verify generated identifiers are unique."""
    generated = {generate_event_id() for _ in range(200)}
    assert len(generated) == 200


def test_valid_identifier_model() -> None:
    """Verify identifier validation within model fields."""
    eid = generate_event_id()
    cid = generate_correlation_id()
    m = DummyIdentifierModel(
        event_id=eid,
        correlation_id=cid,
        session_id="session_hospital_ward_42",
        source_id="eon.ers.visual",
    )
    assert m.event_id == eid
    assert m.correlation_id == cid
    assert m.session_id == "session_hospital_ward_42"
    assert m.source_id == "eon.ers.visual"


def test_invalid_uuid_rejected() -> None:
    """Verify non-UUID strings are rejected for EventId."""
    with pytest.raises(ValidationError):
        DummyIdentifierModel(
            event_id="invalid-uuid-string",
            source_id="eon.core",
        )


def test_invalid_source_id_rejected() -> None:
    """Verify uppercase or illegal punctuation in source_id is rejected."""
    with pytest.raises(ValidationError):
        DummyIdentifierModel(
            event_id=generate_event_id(),
            source_id="EON.Core!",  # Uppercase and punctuation
        )


def test_validate_uuid_string_helper() -> None:
    """Verify standalone UUID validator function."""
    valid_uuid = "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d"
    assert validate_uuid_string(valid_uuid) == valid_uuid
    assert validate_uuid_string(valid_uuid.upper()) == valid_uuid

    with pytest.raises(ValueError):
        validate_uuid_string("not-a-uuid")


def test_validate_source_and_session_helpers() -> None:
    """Verify source and session validator helper functions."""
    assert validate_source_id("sensor.camera.rgb") == "sensor.camera.rgb"
    with pytest.raises(ValueError):
        validate_source_id("sensor..camera")

    assert validate_session_id("session-1234.v1") == "session-1234.v1"
    with pytest.raises(ValueError):
        validate_session_id("")
