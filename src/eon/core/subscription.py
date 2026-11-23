"""Subscription definition, handler contracts, and subscriber state for OVIC EON."""

import asyncio
import inspect
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

from eon.core.backpressure import BackpressurePolicy
from eon.core.queue_manager import SubscriberQueue
from eon.schemas.events import EventEnvelope

# Event handler signature: async callable receiving an EventEnvelope[Any]
EventHandler = Callable[[EventEnvelope[Any]], Awaitable[None] | None]
SubscriptionId = str


def generate_subscription_id() -> SubscriptionId:
    """Generate a unique UUID4 subscription identifier."""
    return str(uuid4())


@dataclass
class Subscription:
    """Represents an active event subscription with isolated queue and worker tasks."""

    subscription_id: SubscriptionId
    event_type: str
    handler: EventHandler
    name: str
    backpressure_policy: BackpressurePolicy
    queue_capacity: int
    timeout_seconds: float
    max_concurrency: int = 1
    queue: SubscriberQueue = field(init=False)
    workers: list[asyncio.Task[None]] = field(default_factory=list, init=False)
    is_active: bool = field(default=True, init=False)

    def __post_init__(self) -> None:
        self.queue = SubscriberQueue(capacity=self.queue_capacity, name=self.name)

    async def invoke_handler(self, event: EventEnvelope[Any]) -> None:
        """Safely invoke the subscriber handler, handling both async and sync callables."""
        if inspect.iscoroutinefunction(self.handler):
            await self.handler(event)
        else:
            # Sync callable or callable object returning a coroutine or None
            res = self.handler(event)
            if inspect.isawaitable(res):
                await res
