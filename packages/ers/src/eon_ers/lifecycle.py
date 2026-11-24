"""Engine lifecycle management conforming to OVIC EON engine lifecycle specifications."""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Callable

from eon_ers.exceptions import ERSLifecycleError
from eon_ers.types import EngineState

logger = logging.getLogger("eon.ers.lifecycle")

VALID_TRANSITIONS: dict[EngineState, set[EngineState]] = {
    EngineState.UNINITIALIZED: {EngineState.INITIALIZING, EngineState.FAILED},
    EngineState.INITIALIZING: {EngineState.INITIALIZED, EngineState.FAILED},
    EngineState.INITIALIZED: {
        EngineState.STARTING,
        EngineState.STOPPING,
        EngineState.STOPPED,
        EngineState.FAILED,
    },
    EngineState.STARTING: {EngineState.RUNNING, EngineState.FAILED},
    EngineState.RUNNING: {
        EngineState.PAUSED,
        EngineState.DEGRADED,
        EngineState.STOPPING,
        EngineState.FAILED,
    },
    EngineState.PAUSED: {EngineState.RUNNING, EngineState.STOPPING, EngineState.FAILED},
    EngineState.DEGRADED: {EngineState.RUNNING, EngineState.STOPPING, EngineState.FAILED},
    EngineState.STOPPING: {EngineState.STOPPED, EngineState.FAILED},
    EngineState.STOPPED: {EngineState.INITIALIZING, EngineState.STARTING},
    EngineState.FAILED: {EngineState.STOPPING, EngineState.STOPPED, EngineState.INITIALIZING},
}


class EngineLifecycleManager:
    """Manages deterministic lifecycle state transitions and health reporting."""

    def __init__(self, engine_name: str = "eon.ers") -> None:
        self.engine_name = engine_name
        self._state: EngineState = EngineState.UNINITIALIZED
        self._lock = asyncio.Lock()
        self._listeners: list[Callable[[EngineState, EngineState, str], Any]] = []
        self._failure_reason: str | None = None

    @property
    def state(self) -> EngineState:
        """Current lifecycle state."""
        return self._state

    @property
    def is_running(self) -> bool:
        """Whether engine is in active processing state (RUNNING or DEGRADED)."""
        return self._state in (EngineState.RUNNING, EngineState.DEGRADED)

    @property
    def failure_reason(self) -> str | None:
        """Detailed message if engine encountered failure."""
        return self._failure_reason

    def add_state_listener(self, callback: Callable[[EngineState, EngineState, str], Any]) -> None:
        """Register a callback invoked when the engine state transitions."""
        self._listeners.append(callback)

    async def transition_to(self, new_state: EngineState, reason: str = "") -> None:
        """Safely transition to a new lifecycle state, enforcing state machine integrity."""
        async with self._lock:
            allowed = VALID_TRANSITIONS.get(self._state, set())
            if new_state not in allowed:
                err_msg = (
                    f"Illegal lifecycle transition for {self.engine_name}: "
                    f"{self._state.value} -> {new_state.value}. Allowed: {[s.value for s in allowed]}"
                )
                logger.error(err_msg)
                raise ERSLifecycleError(err_msg)

            old_state = self._state
            self._state = new_state
            if new_state == EngineState.FAILED:
                self._failure_reason = reason
            elif new_state in (EngineState.RUNNING, EngineState.INITIALIZED):
                self._failure_reason = None

            logger.info(
                f"[{self.engine_name}] State transition: {old_state.value} -> {new_state.value} ({reason})"
            )

            for listener in self._listeners:
                try:
                    res = listener(old_state, new_state, reason)
                    if asyncio.iscoroutine(res):
                        await res
                except Exception as exc:
                    logger.warning(f"Error in lifecycle state listener: {exc}", exc_info=True)

    def get_health_status(self) -> dict[str, Any]:
        """Generate component health status report."""
        return {
            "component": self.engine_name,
            "status": "healthy"
            if self._state == EngineState.RUNNING
            else (
                "degraded"
                if self._state == EngineState.DEGRADED
                else ("failed" if self._state == EngineState.FAILED else "stopped")
            ),
            "state": self._state.value,
            "failure_reason": self._failure_reason,
        }
