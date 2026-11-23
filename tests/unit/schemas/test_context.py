"""Unit tests for interaction and session context schemas."""

import datetime

import pytest
from pydantic import ValidationError

from eon.schemas.context import (
    EnvironmentContext,
    InteractionContextPayload,
    InteractionStage,
    ParticipantContext,
)
from eon.schemas.identifiers import generate_session_id
from eon.schemas.timestamps import utc_now


def test_valid_interaction_context() -> None:
    """AC-1.2-08: Verify valid interaction context snapshot construction."""
    session_id = generate_session_id()
    participant = ParticipantContext(
        participant_id="user_pseudonym_alpha",
        role="primary_collaborator",
        interaction_count=3,
    )
    env = EnvironmentContext(
        location_type="design_studio",
        noise_level="moderate",
        social_setting="one_on_one",
    )
    context = InteractionContextPayload(
        session_id=session_id,
        participants=[participant],
        environment=env,
        interaction_stage=InteractionStage.TASK_COLLABORATION,
    )
    assert context.session_id == session_id
    assert len(context.participants) == 1
    assert context.participants[0].participant_id == "user_pseudonym_alpha"
    assert context.interaction_stage == InteractionStage.TASK_COLLABORATION


def test_context_expiration_validation() -> None:
    """AC-1.2-08: Verify expires_at must be strictly after updated_at."""
    session_id = generate_session_id()
    now = utc_now()
    past = now - datetime.timedelta(seconds=10)

    with pytest.raises(ValidationError):
        InteractionContextPayload(
            session_id=session_id,
            updated_at=now,
            expires_at=past,
        )


def test_participant_context_defaults() -> None:
    """Verify default values on participant context."""
    p = ParticipantContext(participant_id="p1")
    assert p.role == "interactor"
    assert p.interaction_count == 1
