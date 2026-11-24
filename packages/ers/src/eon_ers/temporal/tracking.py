"""Session-isolated observation tracking and bounded ring-buffer memory."""

from __future__ import annotations

import collections
import threading
from typing import Any

from eon_ers.contracts import EmotionObservation, FusionResult
from eon_ers.temporal.smoothing import TemporalSmoother


class SessionObservationTracker:
    """Maintains bounded, session-isolated perceptual history with strict memory boundaries.

    Ensures zero cross-session bleed, preventing long-term profiling or persistent tracking.
    """

    def __init__(
        self,
        max_buffer_size: int = 100,
        alpha: float = 0.35,
        half_life_seconds: float = 3.0,
    ) -> None:
        self.max_buffer_size = max_buffer_size
        self.alpha = alpha
        self.half_life_seconds = half_life_seconds
        self._lock = threading.Lock()
        self._buffers: dict[str, collections.deque[Any]] = {}
        self._smoothers: dict[str, TemporalSmoother] = {}

    def record_observation(
        self, session_id: str, obs: EmotionObservation | FusionResult
    ) -> dict[str, float]:
        """Record observation into session ring buffer and return temporally smoothed probabilities."""
        with self._lock:
            if session_id not in self._buffers:
                self._buffers[session_id] = collections.deque(maxlen=self.max_buffer_size)
                self._smoothers[session_id] = TemporalSmoother(
                    alpha=self.alpha, half_life_seconds=self.half_life_seconds
                )

            self._buffers[session_id].append(obs)

            if isinstance(obs, FusionResult):
                raw_probs = obs.fused_probabilities
            else:
                raw_probs = obs.emotion_probabilities

            smoothed = self._smoothers[session_id].update(raw_probs, obs.timestamp)
            return smoothed

    def get_recent_observations(
        self, session_id: str, max_count: int = 10
    ) -> list[EmotionObservation | FusionResult]:
        """Retrieve recent chronological observations for a session."""
        with self._lock:
            buf = self._buffers.get(session_id)
            if not buf:
                return []
            return list(buf)[-max_count:]

    def reset_session(self, session_id: str) -> None:
        """Securely flush and delete all history and smoother memory for a specific session."""
        with self._lock:
            if session_id in self._buffers:
                self._buffers[session_id].clear()
                del self._buffers[session_id]
            if session_id in self._smoothers:
                self._smoothers[session_id].reset()
                del self._smoothers[session_id]

    def reset_all_sessions(self) -> None:
        """Clear all active session buffers."""
        with self._lock:
            self._buffers.clear()
            self._smoothers.clear()
