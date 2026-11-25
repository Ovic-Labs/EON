"""Explicit state machine and lifecycle tracking for live ERS streaming sessions."""

from __future__ import annotations

import collections
import time
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eon_ers.exceptions import ERSLifecycleError


class LiveSessionState(str, Enum):
    """Explicit lifecycle states for real-time live streaming sessions."""

    CREATED = "CREATED"
    AUTHENTICATING = "AUTHENTICATING"
    CONSENT_PENDING = "CONSENT_PENDING"
    READY = "READY"
    STREAMING = "STREAMING"
    PAUSED = "PAUSED"
    STOPPING = "STOPPING"
    CLOSED = "CLOSED"
    FAILED = "FAILED"
    EXPIRED = "EXPIRED"
    REVOKED = "REVOKED"


TERMINAL_LIVE_STATES: frozenset[LiveSessionState] = frozenset(
    {
        LiveSessionState.CLOSED,
        LiveSessionState.FAILED,
        LiveSessionState.EXPIRED,
        LiveSessionState.REVOKED,
    }
)

VALID_LIVE_TRANSITIONS: dict[LiveSessionState, set[LiveSessionState]] = {
    LiveSessionState.CREATED: {
        LiveSessionState.AUTHENTICATING,
        LiveSessionState.CONSENT_PENDING,
        LiveSessionState.READY,
        LiveSessionState.REVOKED,
        LiveSessionState.CLOSED,
        LiveSessionState.FAILED,
        LiveSessionState.EXPIRED,
    },
    LiveSessionState.AUTHENTICATING: {
        LiveSessionState.CONSENT_PENDING,
        LiveSessionState.READY,
        LiveSessionState.REVOKED,
        LiveSessionState.CLOSED,
        LiveSessionState.FAILED,
        LiveSessionState.EXPIRED,
    },
    LiveSessionState.CONSENT_PENDING: {
        LiveSessionState.READY,
        LiveSessionState.REVOKED,
        LiveSessionState.CLOSED,
        LiveSessionState.FAILED,
        LiveSessionState.EXPIRED,
    },
    LiveSessionState.READY: {
        LiveSessionState.STREAMING,
        LiveSessionState.PAUSED,
        LiveSessionState.STOPPING,
        LiveSessionState.REVOKED,
        LiveSessionState.CLOSED,
        LiveSessionState.FAILED,
        LiveSessionState.EXPIRED,
    },
    LiveSessionState.STREAMING: {
        LiveSessionState.PAUSED,
        LiveSessionState.STOPPING,
        LiveSessionState.REVOKED,
        LiveSessionState.CLOSED,
        LiveSessionState.FAILED,
        LiveSessionState.EXPIRED,
    },
    LiveSessionState.PAUSED: {
        LiveSessionState.STREAMING,
        LiveSessionState.READY,
        LiveSessionState.STOPPING,
        LiveSessionState.REVOKED,
        LiveSessionState.CLOSED,
        LiveSessionState.FAILED,
        LiveSessionState.EXPIRED,
    },
    LiveSessionState.STOPPING: {
        LiveSessionState.CLOSED,
        LiveSessionState.REVOKED,
        LiveSessionState.FAILED,
    },
    LiveSessionState.CLOSED: set(),
    LiveSessionState.FAILED: set(),
    LiveSessionState.EXPIRED: set(),
    LiveSessionState.REVOKED: set(),
}


class LiveSessionRecord(BaseModel):
    """Structured metadata and bounded telemetry for a live ERS session."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    session_id: str
    owner_id: str = "anonymous"
    state: LiveSessionState = LiveSessionState.CREATED
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)
    expires_at: float | None = None
    consent_scope: list[str] = Field(default_factory=lambda: ["facial", "speech", "text"])
    history_opt_in: bool = False
    frame_count: int = 0
    audio_count: int = 0
    text_count: int = 0
    dropped_frames: int = 0
    camera_active: bool = False
    microphone_active: bool = False
    history: collections.deque[dict[str, Any]] = Field(
        default_factory=lambda: collections.deque(maxlen=100),
        exclude=True,
    )

    def transition_to(self, new_state: LiveSessionState) -> None:
        """Enforce legal live-session state transitions."""
        if new_state == self.state:
            return
        allowed = VALID_LIVE_TRANSITIONS.get(self.state, set())
        if new_state not in allowed:
            raise ERSLifecycleError(
                f"Illegal live session transition for '{self.session_id}': "
                f"{self.state.value} -> {new_state.value}.",
                context={"session_id": self.session_id},
            )
        self.state = new_state
        self.updated_at = time.time()
        if new_state in TERMINAL_LIVE_STATES or new_state == LiveSessionState.PAUSED:
            self.camera_active = False
            self.microphone_active = False

    def check_expired(self) -> bool:
        """Mark session EXPIRED if TTL has elapsed."""
        if (
            self.expires_at is not None
            and time.time() > self.expires_at
            and self.state not in TERMINAL_LIVE_STATES
        ):
            self.transition_to(LiveSessionState.EXPIRED)
            return True
        return self.state == LiveSessionState.EXPIRED

    def record_history_summary(self, entry: dict[str, Any]) -> None:
        """Retain bounded non-media summary if session history was explicitly opted in."""
        if self.history_opt_in:
            self.history.append(entry)

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "owner_id": self.owner_id,
            "state": self.state.value,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "expires_at": self.expires_at,
            "consent_scope": list(self.consent_scope),
            "history_opt_in": self.history_opt_in,
            "frame_count": self.frame_count,
            "audio_count": self.audio_count,
            "text_count": self.text_count,
            "dropped_frames": self.dropped_frames,
            "camera_active": self.camera_active,
            "microphone_active": self.microphone_active,
        }
