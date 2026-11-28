"""Session-scoped composition for local robot applications."""

from dataclasses import dataclass

from ovic_eon.ems import EmotionalMemory
from ovic_eon.ere import EmpathyEngine, ResponsePlan
from ovic_eon.erg import EmotionalResponseGenerator, RenderedResponse, ResponseContent
from ovic_eon.ers import EmotionObservation
from ovic_eon.hbu import BehaviorProposal
from ovic_eon.pse import PersonalityEngine
from ovic_eon.sie import SocialInteractionEngine, TurnDecision


@dataclass(frozen=True)
class InteractionResult:
    plan: ResponsePlan
    turn: TurnDecision
    reply: RenderedResponse | None


class RobotInteraction:
    """One host-authorized user and session, with host-controlled output."""

    def __init__(self, *, user_id: str, session_id: str, memory: EmotionalMemory | None = None):
        if memory is not None and memory.user_id != user_id:
            raise ValueError("Memory belongs to another user.")
        self._user_id = user_id
        self._memory = memory
        self.session = SocialInteractionEngine(session_id=session_id)
        self._reasoner = EmpathyEngine()
        self._personality = PersonalityEngine()
        self._renderer = EmotionalResponseGenerator()

    def respond(
        self,
        proposal: BehaviorProposal,
        *,
        confirmed: bool,
        content: ResponseContent | None = None,
        profile_id: str = "professional",
        use_memory: bool = False,
        observation: EmotionObservation | None = None,
    ) -> InteractionResult:
        """Pass only a session-bound observation the user has authorized for this turn."""
        request = proposal.to_empathy_request(user_id=self._user_id, confirmed=confirmed)
        request = type(request).model_validate(
            {
                **request.model_dump(),
                "use_memory": use_memory,
                "use_affect_cue": observation is not None,
            }
        )
        plan = self._reasoner.reason(request, memory=self._memory, observation=observation)
        delivery = self._personality.style(plan, profile_id=profile_id)
        turn = self.session.submit(plan, delivery)
        try:
            reply = self._renderer.render(self.session, turn, content=content)
        except Exception:
            if turn.turn_id:
                self.session.interrupt(turn_id=turn.turn_id)
            raise
        return InteractionResult(plan, turn, reply)
