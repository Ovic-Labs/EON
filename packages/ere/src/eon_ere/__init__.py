"""On-device empathy policy that turns authorized context into a response plan."""

from __future__ import annotations

import sqlite3
import time
from enum import StrEnum
from math import isfinite
from typing import Literal

from eon_ems import EmotionalMemory, EMSError
from eon_ers import EmotionObservation
from eon_ers.types import EmotionCategory, InputQualityStatus, ModelState, ObservationStatus
from pydantic import BaseModel, ConfigDict, Field, field_validator

__all__ = [
    "EmpathyEngine",
    "EmpathyRequest",
    "InteractionGoal",
    "MemoryStatus",
    "ReportedNeed",
    "ResponsePlan",
    "ResponseStrategy",
]


class InteractionGoal(StrEnum):
    SOLVE = "solve"
    EXPLAIN = "explain"
    LISTEN = "listen"
    GIVE_SPACE = "give_space"
    UNSPECIFIED = "unspecified"


class ReportedNeed(StrEnum):
    FRUSTRATED = "frustrated"
    OVERWHELMED = "overwhelmed"
    UPSET = "upset"


class ResponseStrategy(StrEnum):
    OFFER_NEXT_STEP = "offer_next_step"
    EXPLAIN = "explain"
    LISTEN = "listen"
    GIVE_SPACE = "give_space"
    ASK_WHAT_WOULD_HELP = "ask_what_would_help"


class MemoryStatus(StrEnum):
    DISABLED = "disabled"
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"


class EmpathyRequest(BaseModel):
    """Trusted, per-turn context supplied by the host application."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    user_id: str = Field(min_length=1, max_length=128)
    goal: InteractionGoal = InteractionGoal.UNSPECIFIED
    reported_need: ReportedNeed | None = None
    reply_style: Literal["concise", "detailed"] | None = None
    use_memory: bool = Field(default=False, strict=True)
    memory_query: str | None = Field(default=None, min_length=1, max_length=512)
    use_affect_cue: bool = Field(default=False, strict=True)

    @field_validator("user_id")
    @classmethod
    def _validate_user_id(cls, value: str) -> str:
        if value != value.strip() or "\x00" in value:
            raise ValueError("user_id must be non-blank and contain no surrounding spaces or NUL")
        return value

    @field_validator("memory_query")
    @classmethod
    def _validate_memory_query(cls, value: str | None) -> str | None:
        if value is not None and (not value.strip() or "\x00" in value):
            raise ValueError("memory_query must be non-blank and contain no NUL")
        return value


class ResponsePlan(BaseModel):
    """Versioned guidance for a downstream dialogue or response generator."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["1.0"] = "1.0"
    strategy: ResponseStrategy
    tone: Literal["neutral", "supportive"]
    reply_style: Literal["concise", "detailed"]
    acknowledge_reported_need: bool
    offer_check_in: bool
    memory_status: MemoryStatus
    preference_id: str | None = None
    interaction_ids: tuple[str, ...] = ()
    observation_id: str | None = None


_STRATEGIES = {
    InteractionGoal.SOLVE: ResponseStrategy.OFFER_NEXT_STEP,
    InteractionGoal.EXPLAIN: ResponseStrategy.EXPLAIN,
    InteractionGoal.LISTEN: ResponseStrategy.LISTEN,
    InteractionGoal.GIVE_SPACE: ResponseStrategy.GIVE_SPACE,
    InteractionGoal.UNSPECIFIED: ResponseStrategy.ASK_WHAT_WOULD_HELP,
}
_DISTRESS_CUES = frozenset({EmotionCategory.ANGER, EmotionCategory.SADNESS, EmotionCategory.FEAR})
_MAX_CUE_AGE_SECONDS = 15


class EmpathyEngine:
    """Build a response plan without generating text or controlling hardware."""

    def reason(
        self,
        request: EmpathyRequest,
        *,
        memory: EmotionalMemory | None = None,
        observation: EmotionObservation | None = None,
    ) -> ResponsePlan:
        """Apply explicit requests first, then approved preferences and fresh ERS cues."""
        if memory is not None and memory.user_id != request.user_id:
            raise ValueError("EMS user does not match the ERE request.")

        strategy = _STRATEGIES[request.goal]
        if strategy == ResponseStrategy.GIVE_SPACE:
            return ResponsePlan(
                strategy=strategy,
                tone="neutral",
                reply_style="concise",
                acknowledge_reported_need=False,
                offer_check_in=False,
                memory_status=MemoryStatus.DISABLED,
            )

        acknowledge = request.reported_need is not None
        style: Literal["concise", "detailed"] = request.reply_style or "concise"
        memory_status = MemoryStatus.DISABLED
        preference_id = None
        interaction_ids: tuple[str, ...] = ()
        if request.use_memory:
            memory_status = MemoryStatus.UNAVAILABLE
            if memory is not None:
                try:
                    preference = (
                        memory.get_preference("reply_style")
                        if request.reply_style is None
                        else None
                    )
                    relevant = (
                        memory.recall(request.memory_query, kind="interaction", limit=3)
                        if request.memory_query is not None
                        else []
                    )
                except (sqlite3.Error, EMSError):
                    # An unreadable memory store cannot influence a response plan.
                    pass
                else:
                    memory_status = MemoryStatus.AVAILABLE
                    interaction_ids = tuple(record.id for record in relevant)
                    if preference is not None:
                        if preference.text.casefold() in ("concise", "one short step at a time."):
                            style = "concise"
                            preference_id = preference.id
                        elif preference.text.casefold() == "detailed":
                            style = "detailed"
                            preference_id = preference.id

        # A timely, qualified cue may suggest a gentle check-in. It cannot change
        # the requested action, become an emotion claim, or write to memory.
        cue = (
            observation
            if request.use_affect_cue and not acknowledge and _is_eligible_cue(observation)
            else None
        )
        return ResponsePlan(
            strategy=strategy,
            tone="supportive" if acknowledge else "neutral",
            reply_style=style,
            acknowledge_reported_need=acknowledge,
            offer_check_in=cue is not None,
            memory_status=memory_status,
            preference_id=preference_id,
            interaction_ids=interaction_ids,
            observation_id=cue.observation_id if cue is not None else None,
        )


def _is_eligible_cue(observation: EmotionObservation | None) -> bool:
    if observation is None or not isfinite(observation.timestamp):
        return False
    age = time.time() - observation.timestamp
    return (
        0 <= age <= _MAX_CUE_AGE_SECONDS
        and observation.status == ObservationStatus.OK
        and observation.input_quality == InputQualityStatus.ACCEPTABLE
        and observation.model_state == ModelState.MODEL_LOADED_VALIDATED
        and observation.is_validated
        and observation.is_calibrated
        and not observation.is_definitive_claim
        and 0.8 <= observation.confidence <= 1
        and 0 <= observation.uncertainty <= 0.2
        and 0.7 <= observation.quality_score <= 1
        and observation.dominant_estimate in _DISTRESS_CUES
    )
