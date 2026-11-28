from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest
from pydantic import ValidationError

from ovic_eon.ems import EmotionalMemory
from ovic_eon.ere import EmpathyEngine, EmpathyRequest, InteractionGoal, ResponsePlan
from ovic_eon.pse import DeliveryPlan, PersonalityEngine
from ovic_eon.sie import SessionState, SocialInteractionEngine, TurnAction, TurnDecision


def _plans(goal: InteractionGoal = InteractionGoal.SOLVE) -> tuple[ResponsePlan, DeliveryPlan]:
    response = EmpathyEngine().reason(EmpathyRequest(user_id="operator", goal=goal))
    return response, PersonalityEngine().style(response)


def test_busy_turn_and_stale_completion() -> None:
    sie = SocialInteractionEngine(session_id="one")
    plans = _plans()
    first = sie.submit(*plans)
    assert first.action == TurnAction.RESPOND and first.turn_id
    assert TurnDecision.model_validate_json(first.model_dump_json()) == first
    assert sie.submit(*plans).action == TurnAction.BUSY
    assert sie.interrupt(turn_id="stale") is None
    assert sie.complete(first.turn_id)
    second = sie.submit(*plans)
    assert second.turn_id and second.turn_id != first.turn_id
    assert not sie.complete(first.turn_id)
    assert sie.snapshot().active_turn_id == second.turn_id
    assert sie.interrupt() == second.turn_id
    assert sie.snapshot().state == SessionState.READY


def test_give_space_interrupts_and_resume_requires_explicit_call() -> None:
    sie = SocialInteractionEngine(session_id="pause-test")
    first = sie.submit(*_plans())
    paused = sie.submit(*_plans(InteractionGoal.GIVE_SPACE))
    assert paused.action == TurnAction.PAUSE
    assert paused.cancelled_turn_id == first.turn_id
    assert paused.delivery is None
    assert sie.snapshot().state == SessionState.PAUSED
    assert sie.submit(*_plans()).action == TurnAction.PAUSE
    assert sie.resume()
    assert not sie.resume()
    second = sie.submit(*_plans())
    assert second.turn_id and second.turn_id != first.turn_id


def test_close_is_terminal_and_session_state_is_isolated() -> None:
    a = SocialInteractionEngine(session_id="a")
    b = SocialInteractionEngine(session_id="b")
    a_turn = a.submit(*_plans())
    b_turn = b.submit(*_plans())
    assert a.close() == a_turn.turn_id
    assert not a.resume()
    assert a.pause() is None
    assert a.interrupt() is None
    assert a.submit(*_plans()).action == TurnAction.CLOSED
    assert a.snapshot().state == SessionState.CLOSED
    assert b.snapshot().active_turn_id == b_turn.turn_id


def test_expiring_a_turn_returns_only_its_id(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("eon_sie.time.monotonic", lambda: 10.0)
    sie = SocialInteractionEngine(session_id="lease", turn_timeout_seconds=2)
    decision = sie.submit(*_plans())
    assert sie.expire_overdue() is None
    monkeypatch.setattr("eon_sie.time.monotonic", lambda: 12.0)
    assert sie.expire_overdue() == decision.turn_id
    assert sie.expire_overdue() is None
    assert sie.snapshot().state == SessionState.READY


def test_mismatched_plans_and_invalid_delivery_do_not_open_turn() -> None:
    sie = SocialInteractionEngine(session_id="pair")
    response, _ = _plans()
    _, wrong = _plans(InteractionGoal.EXPLAIN)
    with pytest.raises(ValueError, match="does not match"):
        sie.submit(response, wrong)
    assert sie.snapshot().state == SessionState.READY
    with pytest.raises(ValidationError):
        TurnDecision(session_id="pair", action=TurnAction.RESPOND)


def test_concurrent_requests_accept_at_most_one_turn() -> None:
    sie = SocialInteractionEngine(session_id="concurrent")
    plans = _plans()

    def submit(_: int) -> TurnAction:
        return sie.submit(*plans).action

    with ThreadPoolExecutor(max_workers=8) as executor:
        actions = list(executor.map(submit, range(40)))
    assert actions.count(TurnAction.RESPOND) == 1
    assert actions.count(TurnAction.BUSY) == 39


def test_ems_ere_pse_and_sie_chain(tmp_path: Path) -> None:
    memory = EmotionalMemory(tmp_path / "ems.sqlite3", user_id="operator")
    memory.confirm_preference("reply_style", "detailed", confirmed=True)
    response = EmpathyEngine().reason(
        EmpathyRequest(user_id="operator", goal=InteractionGoal.EXPLAIN, use_memory=True),
        memory=memory,
    )
    delivery = PersonalityEngine().style(response, profile_id="formal")
    turn = SocialInteractionEngine(session_id="pipeline").submit(response, delivery)

    assert turn.action == TurnAction.RESPOND
    assert turn.delivery is not None
    assert turn.delivery.reply_style == "detailed"
    assert turn.delivery.formality == "formal"


def test_immediate_pause_and_empty_completion() -> None:
    sie = SocialInteractionEngine(session_id="direct-pause")
    running = sie.submit(*_plans())
    assert running.turn_id
    with pytest.raises(ValueError, match="turn ID"):
        sie.complete("")
    assert sie.pause() == running.turn_id
    assert sie.pause() is None
    assert not sie.complete(running.turn_id)
    assert sie.snapshot().state == SessionState.PAUSED
