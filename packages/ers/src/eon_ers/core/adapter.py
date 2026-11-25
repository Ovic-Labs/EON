"""EON Core event bus integration boundary adapter for ERS.

ARCHITECTURAL SPECIFICATION:
This adapter serves as the formal boundary between ERS and the upcoming EON Core subsystem.
When running standalone (as in Phase 3.1 before Core is implemented), it operates in decoupled
local mode and reports its health status explicitly as 'NOT_CONNECTED'.

SAFETY INVARIANT:
ERS is strictly a perceptual observation engine. It has NO actuation capability.
Payload inspection intercepts and prohibits any robot motion or actuator commands.
"""

from __future__ import annotations

import asyncio
import logging
from enum import Enum
from typing import Any, Callable, Protocol, runtime_checkable

from eon_ers.safety.actuator_isolation import FORBIDDEN_MOTION_KEYS, assert_no_actuator_commands

__all__ = [
    "CoreEventBusAdapter",
    "CoreIntegrationStatus",
    "EONCoreEventBusProtocol",
    "FORBIDDEN_MOTION_KEYS",
    "TOPIC_FUSION_COMPLETED",
    "TOPIC_INPUT_RECEIVED",
    "TOPIC_MODEL_UNAVAILABLE",
    "TOPIC_OBSERVATION_CREATED",
    "TOPIC_PROCESSING_DEGRADED",
    "TOPIC_PROCESSING_FAILED",
]

logger = logging.getLogger("eon.ers.core")

# Well-known ERS event topics conforming to EON event taxonomy
TOPIC_INPUT_RECEIVED = "ers.input.received"
TOPIC_OBSERVATION_CREATED = "ers.observation.created"
TOPIC_FUSION_COMPLETED = "ers.fusion.completed"
TOPIC_PROCESSING_DEGRADED = "ers.processing.degraded"
TOPIC_MODEL_UNAVAILABLE = "ers.model.unavailable"
TOPIC_PROCESSING_FAILED = "ers.processing.failed"


class CoreIntegrationStatus(str, Enum):
    """Connection health status between ERS and EON Core event bus."""

    NOT_CONNECTED = "NOT_CONNECTED"
    CONNECTED = "CONNECTED"
    DEGRADED = "DEGRADED"
    ERROR = "ERROR"


@runtime_checkable
class EONCoreEventBusProtocol(Protocol):
    """Protocol specification required for external EON Core event bus implementations."""

    def publish(self, topic: str, payload: Any, **kwargs: Any) -> Any:
        """Publish an event to the message bus."""
        ...

    def subscribe(self, topic: str, handler: Callable[..., Any], **kwargs: Any) -> Any:
        """Register a subscriber handler for a topic."""
        ...


class CoreEventBusAdapter:
    """Decoupled integration boundary adapter connecting ERS to EON Core."""

    def __init__(self, external_bus: Any | None = None) -> None:
        self._external_bus = external_bus
        self._local_subscribers: dict[str, list[Callable[[str, Any], Any]]] = {}
        self._last_error: str | None = None

    @property
    def integration_status(self) -> CoreIntegrationStatus:
        """Determine connection status with external EON Core subsystem."""
        if self._last_error is not None:
            return CoreIntegrationStatus.ERROR
        if self._external_bus is None:
            return CoreIntegrationStatus.NOT_CONNECTED
        return CoreIntegrationStatus.CONNECTED

    def check_health(self) -> dict[str, Any]:
        """Inspect integration boundary health and report status transparently."""
        status = self.integration_status
        return {
            "status": status.value,
            "boundary_classification": "integration_boundary",
            "external_bus_detected": self._external_bus is not None,
            "is_connected_to_core": (status == CoreIntegrationStatus.CONNECTED),
            "registered_local_handlers": sum(len(h) for h in self._local_subscribers.values()),
            "missing_dependencies": (
                [] if self._external_bus is not None else ["eon.core.event_bus"]
            ),
            "safety_interlocks_active": True,
            "verified_against_production_core": False,
            "last_error": self._last_error,
        }

    def subscribe(self, topic: str, handler: Callable[[str, Any], Any]) -> None:
        """Register local in-process subscriber for ERS events."""
        if topic not in self._local_subscribers:
            self._local_subscribers[topic] = []
        self._local_subscribers[topic].append(handler)

    async def publish(
        self, topic: str, payload: Any, metadata: dict[str, Any] | None = None
    ) -> None:
        """Publish an event to the bus with strict motion invariant verification.

        Raises:
            RuntimeError: If payload attempts to issue robot movement or actuator commands.
        """
        # Safety enforcement: ERS must never authorize or issue robot motion commands
        assert_no_actuator_commands(payload)

        # 1. Forward to external eon.core bus if present
        if self._external_bus is not None:
            try:
                if hasattr(self._external_bus, "publish"):
                    res = self._external_bus.publish(topic, payload)
                    if asyncio.iscoroutine(res):
                        await res
            except Exception as exc:
                self._last_error = str(exc)
                logger.error(
                    "External EON Core event bus publication failed for %s: %s",
                    topic,
                    exc,
                    exc_info=True,
                )
                raise RuntimeError(
                    f"EON Core event bus publication failed on topic '{topic}': {exc}"
                ) from exc

        # 2. Dispatch to local subscribers
        handlers = self._local_subscribers.get(topic, [])
        for handler in handlers:
            try:
                res = handler(topic, payload)
                if asyncio.iscoroutine(res):
                    await res
            except Exception as exc:
                logger.warning("Local ERS subscriber failed on %s: %s", topic, exc, exc_info=True)
