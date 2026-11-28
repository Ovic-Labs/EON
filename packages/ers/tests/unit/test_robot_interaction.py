import pytest
from pydantic import ValidationError

from ovic_eon.check import check
from ovic_eon.erg import ResponseContent
from ovic_eon.hbu import HumanBehaviorEngine
from ovic_eon.interaction import RobotInteraction
from ovic_eon.sie import TurnAction


async def test_installed_check_exercises_live_transcript():
    result = await check()
    assert len(result) == 7
    assert result["SIE"] == "completed"
    assert result["ERS"] == "model_unvalidated"


def test_clarification_and_interruption():
    robot = RobotInteraction(user_id="a", session_id="s")
    interpret = HumanBehaviorEngine().interpret
    with pytest.raises(ValueError, match="Clarify"):
        robot.respond(interpret("Listen. Explain this."), confirmed=True)
    proposal = interpret("Explain this.")
    invalid = ResponseContent.model_construct(clauses=("One. Two.",))
    with pytest.raises(ValidationError):
        robot.respond(proposal, confirmed=True, content=invalid)
    result = robot.respond(proposal, confirmed=True)
    assert result.reply
    paused = robot.respond(interpret("Explain this and stop talking."), confirmed=True)
    assert paused.turn.action == TurnAction.PAUSE
    assert paused.turn.cancelled_turn_id == result.reply.turn_id
    assert not robot.session.authorizes(result.turn)
    assert paused.reply is None
