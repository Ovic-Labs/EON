"""Conservative, offline interpretation of explicit interaction requests."""

from __future__ import annotations

import re
import unicodedata
from enum import StrEnum
from typing import Literal

from eon_ere import EmpathyRequest, InteractionGoal, ReportedNeed
from pydantic import BaseModel, ConfigDict

__all__ = ["BehaviorProposal", "HumanBehaviorEngine", "ProposalStatus"]


class ProposalStatus(StrEnum):
    RECOGNIZED = "recognized"
    AMBIGUOUS = "ambiguous"
    UNSUPPORTED = "unsupported"


class BehaviorProposal(BaseModel):
    """Ephemeral context for the host to confirm before invoking ERE."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["1.0"] = "1.0"
    status: ProposalStatus
    goal: InteractionGoal
    reported_need: ReportedNeed | None = None

    def to_empathy_request(self, *, user_id: str, confirmed: bool) -> EmpathyRequest:
        """Convert reviewed context into an ERE request, with enrichment off by default."""
        if confirmed is not True:
            raise ValueError("The host must confirm the interpretation before use.")
        return EmpathyRequest(user_id=user_id, goal=self.goal, reported_need=self.reported_need)


_GOAL_RULES = (
    (
        InteractionGoal.GIVE_SPACE,
        re.compile(
            r"(?:give me (?:some )?space|leave me alone|stop talking|pause|"
            r"stop|i need (?:some )?space|don't talk)(?: please)?$"
        ),
    ),
    (
        InteractionGoal.LISTEN,
        re.compile(
            r"(?:(?:just )?listen(?: to me)?|i (?:just )?need (?:you|someone) to listen)"
            r"(?: please)?$"
        ),
    ),
    (InteractionGoal.EXPLAIN, re.compile(r"(?:explain\b|(?:can|could|would) you explain\b)")),
    (
        InteractionGoal.SOLVE,
        re.compile(
            r"(?:(?:(?:can|could|would) you )?(?:help me|fix|solve|troubleshoot)\b|"
            r"i need help\b)"
        ),
    ),
)
_NEED = re.compile(r"i (?:am|feel) (frustrated|overwhelmed|upset)\b")
_NEGATED_NEED = re.compile(r"i (?:am|feel) not (frustrated|overwhelmed|upset)\b")


class HumanBehaviorEngine:
    """Recognize a bounded set of English requests and explicit self-reports."""

    def interpret(self, utterance: str) -> BehaviorProposal:
        if not isinstance(utterance, str):
            raise TypeError("utterance must be a string")
        if not 1 <= len(utterance) <= 4096 or not utterance.strip() or "\x00" in utterance:
            raise ValueError("utterance must contain 1–4096 characters and no NUL.")

        text = unicodedata.normalize("NFKC", utterance).casefold()
        text = text.replace("’", "'").replace("i'm ", "i am ")
        # Quoted dialogue and conditional clauses are outside this policy's
        # grammar. Avoid interpreting dialogue embedded in quoted scenarios.
        if '"' in text or "“" in text or "”" in text or text.lstrip().startswith("'"):
            return BehaviorProposal(
                status=ProposalStatus.UNSUPPORTED, goal=InteractionGoal.UNSPECIFIED
            )

        if re.match(r"\s*(?:if|suppose|imagine|hypothetically)\b", text):
            return BehaviorProposal(
                status=ProposalStatus.UNSUPPORTED, goal=InteractionGoal.UNSPECIFIED
            )

        segments = re.split(
            r"[.!?;\n]+|\bbut\b|\band (?:please )?(?=explain|listen|help|pause)", text
        )
        goals: set[InteractionGoal] = set()
        needs: set[ReportedNeed] = set()
        negated: set[ReportedNeed] = set()
        for segment in segments:
            phrase = " ".join(segment.strip(" ,").split()).removeprefix("please ")
            for goal, rule in _GOAL_RULES:
                if rule.match(phrase):
                    goals.add(goal)
            if match := _NEED.match(phrase):
                needs.add(ReportedNeed(match[1]))
            if match := _NEGATED_NEED.match(phrase):
                negated.add(ReportedNeed(match[1]))

        if InteractionGoal.GIVE_SPACE in goals:
            return BehaviorProposal(
                status=ProposalStatus.RECOGNIZED, goal=InteractionGoal.GIVE_SPACE
            )
        if len(goals) > 1 or len(needs) > 1 or needs & negated:
            return BehaviorProposal(
                status=ProposalStatus.AMBIGUOUS, goal=InteractionGoal.UNSPECIFIED
            )
        return BehaviorProposal(
            status=ProposalStatus.RECOGNIZED if goals or needs else ProposalStatus.UNSUPPORTED,
            goal=next(iter(goals), InteractionGoal.UNSPECIFIED),
            reported_need=next(iter(needs), None),
        )
