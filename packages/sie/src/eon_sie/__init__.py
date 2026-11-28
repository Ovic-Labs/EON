"""Offline turn-taking and session lifecycle policy for the OVIC EON SDK."""

from __future__ import annotations

import time
from enum import StrEnum
from math import isfinite
from threading import Lock
from typing import Literal
from uuid import uuid4

from eon_ere import ResponsePlan, ResponseStrategy
from eon_pse import DeliveryPlan
from pydantic import BaseModel, ConfigDict, model_validator

__all__ = [
    "SessionSnapshot",
    "SessionState",
    "SocialInteractionEngine",
    "TurnAction",
    "TurnDecision",
]


class SessionState(StrEnum):
    READY = "ready"
    ACTIVE = "active"
    PAUSED = "paused"
    CLOSED = "closed"


class TurnAction(StrEnum):
    RESPOND = "respond"
    BUSY = "busy"
    PAUSE = "pause"
    CLOSED = "closed"


class SessionSnapshot(BaseModel):
    """Current session state, captured atomically."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    session_id: str
    state: SessionState
    active_turn_id: str | None = None


class TurnDecision(BaseModel):
    """Versioned delivery authorization for a single interaction session."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["1.0"] = "1.0"
    session_id: str
    action: TurnAction
    turn_id: str | None = None
    cancelled_turn_id: str | None = None
    delivery: DeliveryPlan | None = None

    @model_validator(mode="after")
    def _validate_action(self) -> TurnDecision:
        if self.action == TurnAction.RESPOND:
            if not self.turn_id or self.delivery is None or self.delivery.mode != "respond":
                raise ValueError("A response requires a turn ID and active delivery plan.")
        elif self.turn_id is not None or self.delivery is not None:
            raise ValueError("Only a response decision may carry delivery authorization.")
        if self.cancelled_turn_id is not None and self.action != TurnAction.PAUSE:
            raise ValueError("Only a pause decision may cancel a previous turn.")
        return self


class SocialInteractionEngine:
    """Coordinate turns for one application-authorized session.

    The host owns the session and stops live output for any cancelled ID.
    SIE keeps volatile state and does not generate or play a response.
    """

    def __init__(self, *, session_id: str, turn_timeout_seconds: float = 60.0) -> None:
        if (
            not isinstance(session_id, str)
            or not 1 <= len(session_id) <= 128
            or session_id != session_id.strip()
            or "\x00" in session_id
        ):
            raise ValueError(
                "session_id must contain 1–128 characters with no edge whitespace or NUL"
            )
        if (
            isinstance(turn_timeout_seconds, bool)
            or not isinstance(turn_timeout_seconds, (int, float))
            or not isfinite(turn_timeout_seconds)
            or not 0 < turn_timeout_seconds <= 3600
        ):
            raise ValueError("turn_timeout_seconds must be greater than 0 and at most 3600")
        self._session_id = session_id
        self._turn_timeout_seconds = turn_timeout_seconds
        self._state = SessionState.READY
        self._active_turn: TurnDecision | None = None
        self._deadline: float | None = None
        self._lock = Lock()

    def snapshot(self) -> SessionSnapshot:
        with self._lock:
            return SessionSnapshot(
                session_id=self._session_id,
                state=self._state,
                active_turn_id=self._active_turn.turn_id if self._active_turn is not None else None,
            )

    def submit(self, response: ResponsePlan, delivery: DeliveryPlan) -> TurnDecision:
        """Accept one matching pair of plans or return the reason no turn was started."""
        if not isinstance(response, ResponsePlan) or not isinstance(delivery, DeliveryPlan):
            raise TypeError("Expected an ERE ResponsePlan and a PSE DeliveryPlan.")
        delivery = DeliveryPlan.model_validate(delivery.model_dump())
        if not _plans_match(response, delivery):
            raise ValueError("PSE delivery does not match the ERE response plan.")

        with self._lock:
            if self._state == SessionState.CLOSED:
                return TurnDecision(session_id=self._session_id, action=TurnAction.CLOSED)
            if response.strategy == ResponseStrategy.GIVE_SPACE:
                cancelled = self._finish(SessionState.PAUSED)
                return TurnDecision(
                    session_id=self._session_id,
                    action=TurnAction.PAUSE,
                    cancelled_turn_id=cancelled,
                )
            if self._state == SessionState.PAUSED:
                return TurnDecision(session_id=self._session_id, action=TurnAction.PAUSE)
            if self._state == SessionState.ACTIVE:
                return TurnDecision(session_id=self._session_id, action=TurnAction.BUSY)

            turn_id = uuid4().hex
            decision = TurnDecision(
                session_id=self._session_id,
                action=TurnAction.RESPOND,
                turn_id=turn_id,
                delivery=delivery,
            )
            self._deadline = time.monotonic() + self._turn_timeout_seconds
            self._active_turn = decision
            self._state = SessionState.ACTIVE
            return decision

    def authorizes(self, turn: TurnDecision) -> bool:
        """Check whether this exact, unexpired decision is still active."""
        with self._lock:
            return (
                self._state == SessionState.ACTIVE
                and self._active_turn == turn
                and self._deadline is not None
                and time.monotonic() < self._deadline
            )

    def complete(self, turn_id: str) -> bool:
        """Release the current turn after delivery completes."""
        if not isinstance(turn_id, str) or not turn_id:
            raise ValueError("A turn ID is required to complete delivery.")
        return self.interrupt(turn_id=turn_id) is not None

    def interrupt(self, *, turn_id: str | None = None) -> str | None:
        """Cancel the active turn, optionally requiring a matching ID."""
        with self._lock:
            if self._active_turn is None or (
                turn_id is not None and turn_id != self._active_turn.turn_id
            ):
                return None
            return self._finish(SessionState.READY)

    def pause(self) -> str | None:
        """Give the user space immediately, returning any turn the host must stop."""
        with self._lock:
            if self._state == SessionState.CLOSED:
                return None
            return self._finish(SessionState.PAUSED)

    def resume(self) -> bool:
        """Reopen a paused session after the host verifies that the user is ready."""
        with self._lock:
            if self._state != SessionState.PAUSED:
                return False
            self._state = SessionState.READY
            return True

    def close(self) -> str | None:
        """End this session permanently and return any turn the host must stop."""
        with self._lock:
            return self._finish(SessionState.CLOSED)

    def expire_overdue(self) -> str | None:
        """Cancel an overdue turn when called by the host's scheduler."""
        with self._lock:
            if self._deadline is None or time.monotonic() < self._deadline:
                return None
            return self._finish(SessionState.READY)

    def _finish(self, state: SessionState) -> str | None:
        turn_id = self._active_turn.turn_id if self._active_turn is not None else None
        self._active_turn = None
        self._deadline = None
        self._state = state
        return turn_id


def _plans_match(response: ResponsePlan, delivery: DeliveryPlan) -> bool:
    paused = response.strategy == ResponseStrategy.GIVE_SPACE
    return (
        delivery.strategy == response.strategy
        and delivery.tone == response.tone
        and delivery.reply_style == response.reply_style
        and (delivery.mode == "pause") == paused
        and delivery.acknowledge_reported_need
        == (response.acknowledge_reported_need and not paused)
        and delivery.offer_check_in == (response.offer_check_in and not paused)
    )
