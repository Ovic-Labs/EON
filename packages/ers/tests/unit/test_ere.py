import sqlite3
import time
from pathlib import Path

import pytest
from eon_ers.types import Modality, ModelState, ObservationStatus
from pydantic import ValidationError

from ovic_eon.ems import EmotionalMemory
from ovic_eon.ere import (
    EmpathyEngine,
    EmpathyRequest,
    InteractionGoal,
    MemoryStatus,
    ReportedNeed,
    ResponseStrategy,
)
from ovic_eon.ers import EmotionObservation


def _qualified_observation() -> EmotionObservation:
    return EmotionObservation(
        observation_id="obs-1",
        timestamp=time.time(),
        modality=Modality.FACIAL,
        emotion_probabilities={"sadness": 0.9, "neutral": 0.1},
        dominant_estimate="sadness",
        confidence=0.9,
        uncertainty=0.1,
        quality_score=0.9,
        model_id="fixture",
        model_version="1.0.0",
        processing_latency_ms=2.0,
        model_state=ModelState.MODEL_LOADED_VALIDATED,
        is_validated=True,
        is_calibrated=True,
    )


def test_reported_need_takes_priority_and_plan_is_serializable() -> None:
    engine = EmpathyEngine()
    result = engine.reason(
        EmpathyRequest(
            user_id="operator",
            goal=InteractionGoal.SOLVE,
            reported_need=ReportedNeed.FRUSTRATED,
            use_affect_cue=True,
        ),
        observation=_qualified_observation(),
    )
    assert result.strategy == ResponseStrategy.OFFER_NEXT_STEP
    assert result.acknowledge_reported_need
    assert result.tone == "supportive"
    assert result.observation_id is None
    assert not result.offer_check_in
    assert result.model_dump(mode="json")["schema_version"] == "1.0"


def test_give_space_and_disabled_memory_do_not_read_the_database(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    memory = EmotionalMemory(tmp_path / "ems.sqlite3", user_id="operator")

    def forbidden(*args: object, **kwargs: object) -> None:
        pytest.fail("Memory was read with enrichment disabled")

    monkeypatch.setattr(memory, "get_preference", forbidden)
    monkeypatch.setattr(memory, "recall", forbidden)
    engine = EmpathyEngine()
    result = engine.reason(
        EmpathyRequest(
            user_id="operator",
            goal=InteractionGoal.GIVE_SPACE,
            use_memory=True,
            use_affect_cue=True,
            reported_need=ReportedNeed.OVERWHELMED,
        ),
        memory=memory,
        observation=_qualified_observation(),
    )
    assert result.strategy == ResponseStrategy.GIVE_SPACE
    assert result.memory_status == MemoryStatus.DISABLED
    assert not result.acknowledge_reported_need
    assert not result.offer_check_in

    default = engine.reason(EmpathyRequest(user_id="operator"), memory=memory)
    assert default.strategy == ResponseStrategy.ASK_WHAT_WOULD_HELP
    assert default.memory_status == MemoryStatus.DISABLED


def test_confirmed_preference_and_interaction_refs_respect_current_request(tmp_path: Path) -> None:
    memory = EmotionalMemory(
        tmp_path / "ems.sqlite3", user_id="operator", encryption_key=bytes(range(32))
    )
    preference = memory.confirm_preference("reply_style", "detailed", confirmed=True)
    item = memory.remember_interaction("Operator resumed calibration checklist")
    memory.remember_interaction("Operator replaced a battery")
    engine = EmpathyEngine()
    request = EmpathyRequest(
        user_id="operator",
        goal=InteractionGoal.EXPLAIN,
        use_memory=True,
        memory_query="calibration",
    )
    result = engine.reason(request, memory=memory)
    assert result.reply_style == "detailed"
    assert result.preference_id == preference.id
    assert result.interaction_ids == (item.id,)
    assert memory.get_memory(result.interaction_ids[0]) == item
    other = EmotionalMemory(
        tmp_path / "ems.sqlite3", user_id="different", encryption_key=bytes(range(32))
    )
    assert other.get_memory(item.id) is None
    assert result.memory_status == MemoryStatus.AVAILABLE
    assert "Operator resumed" not in result.model_dump_json()
    assert len(memory.export_memories()) == 3

    overridden = engine.reason(request.model_copy(update={"reply_style": "concise"}), memory=memory)
    assert overridden.reply_style == "concise"
    assert overridden.preference_id is None
    with pytest.raises(ValueError, match="does not match"):
        engine.reason(EmpathyRequest(user_id="different", use_memory=True), memory=memory)


def test_memory_failure_discards_enrichment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    memory = EmotionalMemory(tmp_path / "ems.sqlite3", user_id="operator")
    memory.confirm_preference("reply_style", "detailed", confirmed=True)

    def unavailable(*args: object, **kwargs: object) -> None:
        raise sqlite3.OperationalError("database unavailable")

    monkeypatch.setattr(memory, "recall", unavailable)
    decision = EmpathyEngine().reason(
        EmpathyRequest(
            user_id="operator", goal=InteractionGoal.LISTEN, use_memory=True, memory_query="help"
        ),
        memory=memory,
    )
    assert decision.strategy == ResponseStrategy.LISTEN
    assert decision.memory_status == MemoryStatus.UNAVAILABLE
    assert decision.preference_id is None
    assert decision.reply_style == "concise"


@pytest.mark.parametrize(
    "change",
    [
        {"is_validated": False},
        {"is_calibrated": False},
        {"status": ObservationStatus.INSUFFICIENT_EVIDENCE},
        {"model_state": ModelState.MODEL_LOADED_UNVERIFIED},
        {"confidence": 0.79},
        {"uncertainty": 0.21},
        {"quality_score": 0.69},
        {"timestamp": 0},
        {"timestamp": float("nan")},
        {"timestamp": float("inf")},
        {"dominant_estimate": "unknown"},
    ],
)
def test_affect_cue_rejects_unqualified_or_stale_observations(change: dict[str, object]) -> None:
    result = EmpathyEngine().reason(
        EmpathyRequest(user_id="operator", goal=InteractionGoal.EXPLAIN, use_affect_cue=True),
        observation=_qualified_observation().model_copy(update=change),
    )
    assert result.strategy == ResponseStrategy.EXPLAIN
    assert result.observation_id is None
    assert not result.offer_check_in
    assert not result.acknowledge_reported_need


def test_qualified_cue_only_suggests_check_in_and_requires_opt_in() -> None:
    engine = EmpathyEngine()
    observation = _qualified_observation()
    request = EmpathyRequest(user_id="operator", goal=InteractionGoal.EXPLAIN)
    assert not engine.reason(request, observation=observation).offer_check_in

    result = engine.reason(
        request.model_copy(update={"use_affect_cue": True}), observation=observation
    )
    assert result.offer_check_in
    assert result.observation_id == "obs-1"
    assert result.strategy == ResponseStrategy.EXPLAIN
    assert not result.acknowledge_reported_need
    assert "sadness" not in result.model_dump_json()
    with pytest.raises(ValidationError):
        EmpathyRequest.model_validate({"user_id": "operator", "use_affect_cue": "true"})
