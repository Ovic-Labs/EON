from pathlib import Path

import pytest
from pydantic import ValidationError

from ovic_eon.ems import EmotionalMemory
from ovic_eon.ere import EmpathyEngine, EmpathyRequest, InteractionGoal, ReportedNeed
from ovic_eon.pse import DeliveryPlan, PersonalityEngine, PersonalityProfile


def test_default_style_preserves_strategy_and_requested_length() -> None:
    response = EmpathyEngine().reason(
        EmpathyRequest(user_id="operator", goal=InteractionGoal.EXPLAIN, reply_style="detailed")
    )
    styled = PersonalityEngine().style(response)

    assert styled.strategy == response.strategy
    assert styled.reply_style == "detailed"
    assert styled.sentence_limit == 6
    assert styled.tone == response.tone
    assert styled.warmth == "reserved"
    assert DeliveryPlan.model_validate_json(styled.model_dump_json()) == styled


def test_custom_profile_revisions_and_per_turn_selection() -> None:
    profile = PersonalityProfile(
        profile_id="console", revision=2, pace="measured", concise_sentence_limit=1
    )
    engine = PersonalityEngine(profiles=(profile,), default_profile="console")
    response = EmpathyEngine().reason(
        EmpathyRequest(
            user_id="operator", goal=InteractionGoal.SOLVE, reported_need=ReportedNeed.FRUSTRATED
        )
    )

    delivery = engine.style(response)
    assert delivery.profile_id == "console"
    assert delivery.profile_revision == 2
    assert delivery.acknowledge_reported_need
    assert delivery.pace == "measured"
    assert delivery.sentence_limit == 1
    assert engine.style(response, profile_id="friendly").warmth == "warm"
    assert engine.style(response).profile_id == "console"
    assert {profile.profile_id for profile in engine.list_profiles()} == {
        "professional",
        "formal",
        "friendly",
        "console",
    }


def test_pause_overrides_delivery_without_losing_the_strategy() -> None:
    pause = EmpathyEngine().reason(
        EmpathyRequest(user_id="operator", goal=InteractionGoal.GIVE_SPACE)
    )
    stale_flags = pause.model_copy(
        update={"offer_check_in": True, "acknowledge_reported_need": True}
    )
    styled = PersonalityEngine().style(stale_flags, profile_id="friendly")

    assert styled.strategy == pause.strategy
    assert styled.mode == "pause"
    assert styled.sentence_limit == 0
    assert not styled.offer_check_in
    assert not styled.acknowledge_reported_need
    with pytest.raises(ValidationError, match="pause cannot"):
        DeliveryPlan.model_validate({**styled.model_dump(), "offer_check_in": True})


def test_profile_validation_rejects_unknown_duplicate_and_unbounded_settings() -> None:
    with pytest.raises(ValueError, match="Unknown"):
        PersonalityEngine(default_profile="unknown")
    with pytest.raises(ValueError, match="Duplicate"):
        PersonalityEngine(profiles=(PersonalityProfile(profile_id="friendly"),))
    with pytest.raises(ValidationError):
        PersonalityProfile(profile_id="free text\n")
    with pytest.raises(ValidationError):
        PersonalityProfile(profile_id="valid", concise_sentence_limit=3, detailed_sentence_limit=2)
    with pytest.raises(ValidationError):
        PersonalityProfile.model_validate({"profile_id": "valid", "concise_sentence_limit": "2"})


def test_ems_confirmed_preference_flows_through_ere_to_pse(tmp_path: Path) -> None:
    memory = EmotionalMemory(tmp_path / "ems.sqlite3", user_id="operator")
    memory.confirm_preference("reply_style", "detailed", confirmed=True)
    response = EmpathyEngine().reason(
        EmpathyRequest(user_id="operator", goal=InteractionGoal.EXPLAIN, use_memory=True),
        memory=memory,
    )
    delivery = PersonalityEngine().style(response, profile_id="formal")
    assert delivery.strategy == response.strategy
    assert delivery.reply_style == "detailed"
    assert delivery.sentence_limit == 6
    assert delivery.formality == "formal"
