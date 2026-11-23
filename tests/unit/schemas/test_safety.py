"""Unit tests for safety advisory contracts and non-authorization boundaries."""

import pytest
from pydantic import ValidationError

from eon.schemas.common import QualityStatus
from eon.schemas.safety import (
    SafetyAdvisoryLevel,
    SafetyAdvisoryPayload,
    ValidationResultPayload,
)


def test_valid_safety_advisory() -> None:
    """AC-1.2-09: Verify valid safety advisory payload construction."""
    adv = SafetyAdvisoryPayload(
        level=SafetyAdvisoryLevel.ADVISORY_PAUSE,
        advisory_code="ADV_PROXIMITY_OVERRUN",
        human_readable_message="Human interactor stepped within 0.5 meters of arm workspace.",
        reason="Rapid distance reduction detected in behavioral observation feed.",
        recommended_action="Suspend social speech overtures and recommend static gaze.",
    )
    assert adv.level == SafetyAdvisoryLevel.ADVISORY_PAUSE
    assert adv.is_authoritative_stop is False
    assert "Host robot safety PLC" in adv.authority_boundary_disclaimer


def test_authoritative_stop_strictly_forbidden() -> None:
    """AC-1.2-09: Verify setting is_authoritative_stop to True is strictly rejected.

    EON is not a certified robot safety controller. It must never claim or transmit
    authoritative emergency stop command structures.
    """
    with pytest.raises(ValidationError) as exc:
        SafetyAdvisoryPayload(
            level=SafetyAdvisoryLevel.ADVISORY_DISENGAGE,
            advisory_code="ADV_EMERGENCY",
            human_readable_message="Simulated stop attempt.",
            reason="Testing authority boundaries.",
            recommended_action="Halt.",
            is_authoritative_stop=True,  # Prohibited!
        )
    assert "is_authoritative_stop must always be False" in str(exc.value)


def test_disclaimer_cannot_be_stripped() -> None:
    """Verify authority boundary disclaimer cannot be emptied or stripped."""
    with pytest.raises(ValidationError):
        SafetyAdvisoryPayload(
            level=SafetyAdvisoryLevel.INFO,
            advisory_code="ADV_INFO",
            human_readable_message="Information only.",
            reason="Informational.",
            recommended_action="None.",
            authority_boundary_disclaimer="",  # Cannot be stripped
        )


def test_validation_result_payload() -> None:
    """Verify ValidationResultPayload construction."""
    res_valid = ValidationResultPayload(
        target_id="event-1234",
        is_valid=True,
    )
    assert res_valid.is_valid is True
    assert res_valid.data_freshness_status == QualityStatus.GOOD

    res_invalid = ValidationResultPayload(
        target_id="event-5678",
        is_valid=False,
        rejection_reasons=["Schema version mismatch", "Stale observation"],
        data_freshness_status=QualityStatus.STALE,
    )
    assert res_invalid.is_valid is False
    assert len(res_invalid.rejection_reasons) == 2
