"""Unit tests for the universal event envelope."""

import pytest
from pydantic import ValidationError

from eon.schemas.common import DataClassification
from eon.schemas.events import (
    ComponentHealthEvent,
    EventEnvelope,
    EventMetadata,
    EventType,
    SafetyAdvisoryEvent,
)
from eon.schemas.health import (
    ComponentHealthPayload,
    ComponentStatus,
    HealthState,
)
from eon.schemas.identifiers import (
    generate_causation_id,
    generate_correlation_id,
    generate_session_id,
)
from eon.schemas.safety import SafetyAdvisoryLevel, SafetyAdvisoryPayload


def test_event_envelope_default_fields() -> None:
    """AC-1.2-04: Verify automatic event_id generation and UTC timestamp."""
    payload = SafetyAdvisoryPayload(
        level=SafetyAdvisoryLevel.INFO,
        advisory_code="ADV_BOOT",
        human_readable_message="Subsystem initialized.",
        reason="Startup.",
        recommended_action="None.",
    )
    event = SafetyAdvisoryEvent(
        event_type=EventType.SAFETY_ADVISORY,
        source="eon.core",
        payload=payload,
    )
    assert event.event_id is not None
    assert len(event.event_id) == 36
    assert event.timestamp.tzinfo is not None
    assert event.schema_version == "1.0.0"
    assert event.payload.advisory_code == "ADV_BOOT"


def test_event_envelope_causality_and_correlation_tracking() -> None:
    """AC-1.2-04, AC-1.2-05: Verify correlation and causation identifiers."""
    corr_id = generate_correlation_id()
    caus_id = generate_causation_id()
    sess_id = generate_session_id()

    metadata = EventMetadata(
        correlation_id=corr_id,
        causation_id=caus_id,
        session_id=sess_id,
        classification=DataClassification.SENSITIVE_BEHAVIOURAL,
    )

    payload = ComponentHealthPayload(
        component_id="eon.ers",
        health_state=HealthState.HEALTHY,
        status=ComponentStatus.RUNNING,
    )

    event = ComponentHealthEvent(
        event_type=EventType.COMPONENT_HEALTH,
        source="eon.ers",
        metadata=metadata,
        payload=payload,
    )
    assert event.metadata.correlation_id == corr_id
    assert event.metadata.causation_id == caus_id
    assert event.metadata.session_id == sess_id
    assert event.metadata.classification == DataClassification.SENSITIVE_BEHAVIOURAL


def test_event_envelope_missing_required_fields_rejected() -> None:
    """Verify envelope fails validation when required fields are missing."""
    payload = ComponentHealthPayload(
        component_id="eon.ers",
        health_state=HealthState.HEALTHY,
        status=ComponentStatus.RUNNING,
    )
    # Missing source
    with pytest.raises(ValidationError):
        EventEnvelope(
            event_type=EventType.COMPONENT_HEALTH,
            payload=payload,
        )  # type: ignore[call-arg]


def test_event_envelope_unsupported_schema_version_rejected() -> None:
    """AC-1.2-11: Verify envelope rejects unsupported schema versions."""
    payload = ComponentHealthPayload(
        component_id="eon.ers",
        health_state=HealthState.HEALTHY,
        status=ComponentStatus.RUNNING,
    )
    with pytest.raises(ValidationError) as exc:
        EventEnvelope(
            event_type=EventType.COMPONENT_HEALTH,
            source="eon.ers",
            schema_version="9.9.9",
            payload=payload,
        )
    assert "Unsupported schema version" in str(exc.value)
