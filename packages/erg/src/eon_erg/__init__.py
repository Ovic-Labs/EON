"""Offline, bounded response rendering for the OVIC EON SDK."""

from __future__ import annotations

import re
import unicodedata
from typing import Literal

from eon_ere import ResponseStrategy
from eon_sie import SocialInteractionEngine, TurnAction, TurnDecision
from pydantic import BaseModel, ConfigDict, Field, field_validator

__all__ = ["EmotionalResponseGenerator", "RenderedResponse", "ResponseContent"]


class ResponseContent(BaseModel):
    """Plain, host-approved answer clauses. ERG adds sentence punctuation."""

    model_config = ConfigDict(extra="forbid", frozen=True, revalidate_instances="always")

    clauses: tuple[str, ...] = Field(default=(), max_length=12)

    @field_validator("clauses")
    @classmethod
    def _validate_clauses(cls, clauses: tuple[str, ...]) -> tuple[str, ...]:
        clean = []
        for clause in clauses:
            if any(unicodedata.category(char).startswith("C") for char in clause):
                raise ValueError("Answer clauses cannot contain control or format characters.")
            value = clause.strip()
            if not 1 <= len(value) <= 240 or re.search(r"[!?。！？]|(?<!\d)\.|\.(?!\d)", value):
                raise ValueError("Use a plain 1–240 character clause without sentence punctuation.")
            clean.append(value)
        return tuple(clean)


class RenderedResponse(BaseModel):
    """Text and metadata for a single accepted turn."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["1.0"] = "1.0"
    session_id: str
    turn_id: str
    strategy: ResponseStrategy
    profile_id: str
    pace: Literal["measured", "standard"]
    sentences: tuple[str, ...] = Field(min_length=1, max_length=12)

    @property
    def text(self) -> str:
        return " ".join(self.sentences)


_LISTEN = {
    "professional": "I'm listening.",
    "conversational": "I'm here to listen.",
    "formal": "Please continue when you are ready.",
}
_ACKNOWLEDGE = {
    "reserved": "I hear what you said.",
    "steady": "I hear that this is difficult.",
    "warm": "Thank you for telling me how this feels.",
}


class EmotionalResponseGenerator:
    """Render deterministic text for an active SIE decision."""

    def render(
        self,
        session: SocialInteractionEngine,
        turn: TurnDecision,
        *,
        content: ResponseContent | None = None,
    ) -> RenderedResponse | None:
        """Return no text if the turn is paused, stale, expired, or from another session."""
        delivery = turn.delivery
        turn_id = turn.turn_id
        if (
            turn.action != TurnAction.RESPOND
            or delivery is None
            or turn_id is None
            or not session.authorizes(turn)
        ):
            return None

        clauses = ResponseContent.model_validate(content).clauses if content is not None else ()
        if delivery.strategy in (ResponseStrategy.EXPLAIN, ResponseStrategy.OFFER_NEXT_STEP):
            if delivery.strategy == ResponseStrategy.OFFER_NEXT_STEP:
                clauses = clauses[:1]
            core = [f"{clause}." for clause in clauses]
            if not core:
                core = ["What should we work through first?"]
        elif delivery.strategy == ResponseStrategy.LISTEN:
            core = [_LISTEN[delivery.formality]]
        elif delivery.strategy == ResponseStrategy.ASK_WHAT_WOULD_HELP:
            core = ["What would help you right now?"]
        else:
            return None

        limit = delivery.sentence_limit
        sentences = []
        if delivery.acknowledge_reported_need and limit > 1:
            sentences.append(_ACKNOWLEDGE[delivery.warmth])
        sentences.extend(core[: limit - len(sentences)])
        if delivery.offer_check_in and len(sentences) < limit:
            sentences.append("Would you like to pause before continuing?")

        return RenderedResponse(
            session_id=turn.session_id,
            turn_id=turn_id,
            strategy=delivery.strategy,
            profile_id=delivery.profile_id,
            pace=delivery.pace,
            sentences=tuple(sentences),
        )
