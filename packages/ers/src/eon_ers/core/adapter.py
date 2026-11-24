"""EON Core event bus integration adapter for ERS.

Follows clean architectural boundaries:
- Plugs into existing eon.core.EventBus if present.
- Provides standalone decoupled event dispatch when Core is not loaded.
- Enforces failure isolation: event dispatch exceptions never crash ERS processing.
- Strictly rejects any robot actuator or motion command payloads.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Callable

logger = logging.getLogger("eon.ers.core")

# Well-known ERS event topics conforming to EON event taxonomy
TOPIC_INPUT_RECEIVED = "ers.input.received"
TOPIC_OBSERVATION_CREATED = "ers.observation.created"
TOPIC_FUSION_COMPLETED = "ers.fusion.completed"
TOPIC_PROCESSING_DEGRADED = "ers.processing.degraded"
TOPIC_MODEL_UNAVAILABLE = "ers.model.unavailable"
TOPIC_PROCESSING_FAILED = "ers.processing.failed"

# Explicit motion command blacklisted keys to enforce safety invariant
FORBIDDEN_MOTION_KEYS = {"cmd_vel", "motion", "actuator", "motor", "joint", "trajectory"}


class CoreEventBusAdapter:
    """Dispatches ERS lifecycle and emotion observation events to EON Core."""

    def __init__(self, external_bus: Any | None = None) -> None:
        self._external_bus = external_bus
        self._local_subscribers: dict[str, list[Callable[[str, Any], Any]]] = {}

    def subscribe(self, topic: str, handler: Callable[[str, Any], Any]) -> None:
        """Register local in-process subscriber for ERS events."""
        if topic not in self._local_subscribers:
            self._local_subscribers[topic] = []
        self._local_subscribers[topic].append(handler)

    async def publish(
        self, topic: str, payload: Any, metadata: dict[str, Any] | None = None
    ) -> None:
        """Publish an event to the bus with strict failure isolation and motion invariant check."""
        # Safety enforcement: ERS must never issue robot motion commands
        if isinstance(payload, dict):
            for k in payload.keys():
                if any(forbidden in str(k).lower() for forbidden in FORBIDDEN_MOTION_KEYS):
                    raise RuntimeError(
                        f"Safety violation: ERS event payload contains forbidden motion key '{k}'. ERS must never issue robot actuator commands."
                    )

        # 1. Forward to external eon.core bus if configured
        if self._external_bus is not None:
            try:
                if hasattr(self._external_bus, "publish"):
                    res = self._external_bus.publish(topic, payload)
                    if asyncio.iscoroutine(res):
                        await res
            except Exception as exc:
                logger.error(
                    f"External EON Core event bus publication failed for {topic}: {exc}",
                    exc_info=True,
                )

        # 2. Dispatch to local subscribers
        handlers = self._local_subscribers.get(topic, [])
        for handler in handlers:
            try:
                res = handler(topic, payload)
                if asyncio.iscoroutine(res):
                    await res
            except Exception as exc:
                logger.warning(f"Local ERS subscriber failed on {topic}: {exc}", exc_info=True)
