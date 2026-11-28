import time
from pathlib import Path

import pytest
from eon_ers.types import Modality, ObservationStatus
from pydantic import ValidationError

from ovic_eon.ems import EmotionalMemory
from ovic_eon.ere import EmpathyEngine, EmpathyRequest, InteractionGoal, ReportedNeed
from ovic_eon.erg import EmotionalResponseGenerator, RenderedResponse, ResponseContent
from ovic_eon.ers import EmotionObservation
from ovic_eon.hbu import HumanBehaviorEngine, ProposalStatus
from ovic_eon.pse import PersonalityEngine
from ovic_eon.sie import SocialInteractionEngine, TurnAction, TurnDecision


def _start(session: SocialInteractionEngine, goal: InteractionGoal) -> TurnDecision:
    response = EmpathyEngine().reason(EmpathyRequest(user_id="a", goal=goal))
    return session.submit(response, PersonalityEngine().style(response))


@pytest.mark.parametrize(
    ("message", "goal", "need"),
    [
        (
            "I’m frustrated. Help me with calibration.",
            InteractionGoal.SOLVE,
            ReportedNeed.FRUSTRATED,
        ),
        ("Please explain this.", InteractionGoal.EXPLAIN, None),
        ("I just need someone to listen.", InteractionGoal.LISTEN, None),
        ("Please stop.", InteractionGoal.GIVE_SPACE, None),
        ("Explain the manual. Give me space.", InteractionGoal.GIVE_SPACE, None),
    ],
)
def test_hbu_recognizes_explicit_requests(
    message: str, goal: InteractionGoal, need: ReportedNeed | None
) -> None:
    proposal = HumanBehaviorEngine().interpret(message)
    assert proposal.status == ProposalStatus.RECOGNIZED
    assert (proposal.goal, proposal.reported_need) == (goal, need)
    with pytest.raises(ValueError, match="confirm"):
        proposal.to_empathy_request(user_id="a", confirmed=False)
    request = proposal.to_empathy_request(user_id="a", confirmed=True)
    assert request.goal == goal
    assert not request.use_memory and not request.use_affect_cue
    assert message not in proposal.model_dump_json()


@pytest.mark.parametrize(
    "message",
    [
        "If this fails; explain it.",
        "I am not frustrated.",
        "My colleague is overwhelmed.",
        "Don't explain this.",
        'My colleague said "help me".',
        "Please don't stop talking.",
    ],
)
def test_hbu_does_not_infer_unstated_intent_or_feelings(message: str) -> None:
    proposal = HumanBehaviorEngine().interpret(message)
    assert proposal.status == ProposalStatus.UNSUPPORTED
    assert proposal.goal == InteractionGoal.UNSPECIFIED and proposal.reported_need is None


def test_hbu_abstains_on_conflicting_context() -> None:
    engine = HumanBehaviorEngine()
    assert engine.interpret("Just listen. Explain this.").status == ProposalStatus.AMBIGUOUS
    assert engine.interpret("I am upset but I am not upset.").status == ProposalStatus.AMBIGUOUS


def test_erg_rejects_stale_forged_paused_and_cross_session_turns() -> None:
    renderer = EmotionalResponseGenerator()
    session = SocialInteractionEngine(session_id="a")
    other = SocialInteractionEngine(session_id="b")
    turn = _start(session, InteractionGoal.EXPLAIN)
    assert turn.delivery is not None
    tampered = turn.model_copy(
        update={"delivery": turn.delivery.model_copy(update={"sentence_limit": 10})}
    )
    assert renderer.render(session, tampered) is None
    assert renderer.render(other, turn) is None

    paused = _start(session, InteractionGoal.GIVE_SPACE)
    assert paused.action == TurnAction.PAUSE and paused.cancelled_turn_id == turn.turn_id
    assert renderer.render(session, paused) is None
    assert renderer.render(session, turn) is None


def test_erg_checks_deadline_before_the_scheduler_runs(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("eon_sie.time.monotonic", lambda: 10)
    session = SocialInteractionEngine(session_id="deadline", turn_timeout_seconds=1)
    turn = _start(session, InteractionGoal.LISTEN)
    monkeypatch.setattr("eon_sie.time.monotonic", lambda: 11)
    assert EmotionalResponseGenerator().render(session, turn) is None
    assert session.expire_overdue() == turn.turn_id


def test_erg_respects_sentence_budget_and_one_step_strategy() -> None:
    with pytest.raises(ValidationError):
        ResponseContent(clauses=("First. Second.",))
    with pytest.raises(ValidationError):
        ResponseContent(clauses=("first\nsecond",))

    session = SocialInteractionEngine(session_id="budget")
    turn = _start(session, InteractionGoal.SOLVE)
    rendered = EmotionalResponseGenerator().render(
        session, turn, content=ResponseContent(clauses=("Open the settings", "Change the mode"))
    )
    assert rendered is not None
    assert rendered.text == "Open the settings."
    assert RenderedResponse.model_validate_json(rendered.model_dump_json()) == rendered


def test_all_seven_modules_can_share_a_turn(tmp_path: Path) -> None:
    proposal = HumanBehaviorEngine().interpret("I feel overwhelmed. Explain the restart process.")
    request = proposal.to_empathy_request(user_id="a", confirmed=True).model_copy(
        update={"use_memory": True, "use_affect_cue": True}
    )
    memory = EmotionalMemory(tmp_path / "ems.sqlite3", user_id="a")
    memory.confirm_preference("reply_style", "detailed", confirmed=True)
    observation = EmotionObservation(
        observation_id="sample",
        timestamp=time.time(),
        modality=Modality.FACIAL,
        emotion_probabilities={"unknown": 1.0},
        dominant_estimate="unknown",
        confidence=0,
        uncertainty=1,
        quality_score=0.5,
        model_id="fixture",
        model_version="0.1",
        processing_latency_ms=1,
        status=ObservationStatus.MODEL_UNVALIDATED,
    )
    response = EmpathyEngine().reason(request, memory=memory, observation=observation)
    assert response.observation_id is None and not response.offer_check_in
    delivery = PersonalityEngine().style(response, profile_id="friendly")
    session = SocialInteractionEngine(session_id="joint")
    turn = session.submit(response, delivery)
    rendered = EmotionalResponseGenerator().render(
        session,
        turn,
        content=ResponseContent(clauses=("Open the settings", "Select the restart command")),
    )
    assert rendered is not None and turn.turn_id
    assert rendered.sentences == (
        "Thank you for telling me how this feels.",
        "Open the settings.",
        "Select the restart command.",
    )
    assert session.complete(turn.turn_id)
    assert EmotionalResponseGenerator().render(session, turn) is None


def test_erg_truncates_to_the_authorized_sentence_budget() -> None:
    session = SocialInteractionEngine(session_id="concise")
    turn = _start(session, InteractionGoal.EXPLAIN)
    content = ResponseContent(clauses=("Open settings", "Choose calibration", "Save the result"))
    renderer = EmotionalResponseGenerator()
    rendered = renderer.render(session, turn, content=content)
    assert rendered is not None
    assert rendered.sentences == ("Open settings.", "Choose calibration.")
    tampered = content.model_copy(update={"clauses": ("First. Second.",)})
    with pytest.raises(ValidationError):
        renderer.render(session, turn, content=tampered)
