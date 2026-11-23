"""Tests for zero-leakage privacy error sanitization."""

import pytest

from eon.core.delivery import DeliveryOutcome, DeliveryState
from eon.core.event_bus import EventBus
from eon.schemas.common import ModalityType, Provenance
from eon.schemas.events import EventEnvelope, EventType
from eon.schemas.observations import ObservationPayload, TextObservationData

SYNTHETIC_API_KEY = "SECRET_API_KEY_9876543210_DO_NOT_LEAK"
SYNTHETIC_PASSWORD = "SUPER_SECRET_PASSWORD_XYZ"


def _make_sample_event() -> EventEnvelope[ObservationPayload]:
    prov = Provenance(source_id="test.privacy", engine_version="0.1.0")
    payload = ObservationPayload(
        source_id="test.privacy",
        modality=ModalityType.TEXT,
        confidence=1.0,
        provenance=prov,
        data=TextObservationData(text="privacy audit"),
    )
    return EventEnvelope(
        event_type=EventType.OBSERVATION,
        source="test.privacy",
        payload=payload,
    )


@pytest.mark.asyncio
async def test_zero_leakage_of_secrets_in_delivery_outcome() -> None:
    """AC-1.3-03: Verify that sensitive secrets in exceptions never leak into delivery outcomes."""
    async with EventBus() as bus:

        async def leaky_handler(_e: EventEnvelope[ObservationPayload]) -> None:
            raise ValueError(f"Failed with key {SYNTHETIC_API_KEY} and pass {SYNTHETIC_PASSWORD}")

        await bus.subscribe_async(EventType.OBSERVATION, leaky_handler, name="leaky_sub")

        event = _make_sample_event()
        outcomes = await bus.publish_and_wait(event)

        assert len(outcomes) == 1
        outcome = outcomes[0]

        assert outcome.state == DeliveryState.FAILED
        assert outcome.error_message is not None

        # Verify safe category and diagnostic id
        assert outcome.diagnostic_id is not None
        assert outcome.diagnostic_id.startswith("ERR-")
        assert "HandlerException[ValueError]" in outcome.error_message
        assert outcome.diagnostic_id in outcome.error_message

        # STRICT PRIVACY INVARIANT: Secrets MUST NOT be present anywhere in the outcome object
        outcome_repr = repr(outcome)
        outcome_dict = str(outcome.__dict__)

        assert SYNTHETIC_API_KEY not in outcome.error_message
        assert SYNTHETIC_PASSWORD not in outcome.error_message
        assert SYNTHETIC_API_KEY not in outcome_repr
        assert SYNTHETIC_PASSWORD not in outcome_repr
        assert SYNTHETIC_API_KEY not in outcome_dict
        assert SYNTHETIC_PASSWORD not in outcome_dict


def test_delivery_outcome_create_sanitizes_legacy_error_message() -> None:
    """Verify DeliveryOutcome.create sanitizes legacy error_message input containing secrets."""
    outcome = DeliveryOutcome.create(
        event_id="ev_001",
        subscription_id="sub_001",
        state=DeliveryState.FAILED,
        error_message=f"Handler exception: RuntimeError: {SYNTHETIC_API_KEY}",
    )
    assert outcome.error_message is not None
    assert SYNTHETIC_API_KEY not in outcome.error_message
    assert "HandlerException" in outcome.error_message
    assert outcome.diagnostic_id is not None
    assert outcome.diagnostic_id.startswith("ERR-")
