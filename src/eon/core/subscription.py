"""Subscription definition, handler contracts, and subscriber state for OVIC EON."""

import asyncio
import inspect
from collections.abc import Awaitable, Callable
from concurrent.futures import Executor
from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

from eon.core.backpressure import BackpressurePolicy
from eon.core.queue_manager import SubscriberQueue
from eon.schemas.events import EventEnvelope

# Event handler signature: async or sync callable receiving an EventEnvelope[Any]
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
    starvation_threshold: int = 10
    queue: SubscriberQueue = field(init=False)
    workers: list[asyncio.Task[None]] = field(default_factory=list, init=False)
    is_active: bool = field(default=True, init=False)

    def __post_init__(self) -> None:
        self.queue = SubscriberQueue(
            capacity=self.queue_capacity,
            name=self.name,
            starvation_threshold=self.starvation_threshold,
        )

    async def invoke_handler(
        self,
        event: EventEnvelope[Any],
        executor: Executor | None = None,
    ) -> None:
        """Safely invoke the subscriber handler, handling both async and sync callables.

        Synchronous handlers are dispatched to a bounded thread pool executor (passed via executor)
        to prevent blocking the asyncio event loop thread.

        Cancellation Limitations:
        Standard Python threads running synchronous code cannot be forcibly terminated
        once running. If an asyncio task awaiting invoke_handler is cancelled (e.g. on timeout
        or bus shutdown), the asyncio task unblocks immediately, but the thread continues executing
        until the synchronous handler returns. Handlers should use cooperative checks or timeouts.
        """
        if inspect.iscoroutinefunction(self.handler):
            await self.handler(event)
        else:
            loop = asyncio.get_running_loop()
            res = await loop.run_in_executor(executor, self.handler, event)
            if inspect.isawaitable(res):
                await res
