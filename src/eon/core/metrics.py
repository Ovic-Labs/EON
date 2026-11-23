"""Lightweight in-process metrics and operational observability for OVIC EON Event Bus."""

import asyncio
from collections import deque
from typing import Final

from pydantic import Field

from eon.schemas.base import EonBaseModel

# Bounded rolling window for latency percentiles to prevent memory growth
MAX_LATENCY_SAMPLES: Final[int] = 1000


class EventBusMetricsSnapshot(EonBaseModel):
    """Immutable snapshot of Event Bus operational metrics.

    Privacy Guarantee: Never contains event payloads, user identifiers, or biometrics.
    """

    total_published: int = Field(default=0, description="Total events submitted to publish()")
    accepted_events: int = Field(default=0, description="Total events accepted into bus routing")
    delivered_events: int = Field(
        default=0, description="Total successful deliveries across subscribers"
    )
    rejected_events: int = Field(
        default=0, description="Total events rejected due to backpressure or closed bus"
    )
    dropped_events: int = Field(
        default=0, description="Total events dropped due to lossy backpressure policies"
    )
    failed_deliveries: int = Field(
        default=0, description="Total handler execution exceptions or timeouts"
    )
    cancelled_deliveries: int = Field(
        default=0, description="Total deliveries cancelled during shutdown"
    )
    active_subscriptions: int = Field(
        default=0, description="Current count of registered subscriptions"
    )
    active_workers: int = Field(
        default=0, description="Current count of active dispatch worker tasks"
    )
    current_queue_depth: int = Field(
        default=0, description="Aggregate depth across all subscriber queues"
    )
    max_queue_depth: int = Field(default=0, description="Highest observed aggregate queue depth")
    publish_latency_p50_ms: float = Field(
        default=0.0, description="p50 publish latency in milliseconds"
    )
    publish_latency_p95_ms: float = Field(
        default=0.0, description="p95 publish latency in milliseconds"
    )
    publish_latency_p99_ms: float = Field(
        default=0.0, description="p99 publish latency in milliseconds"
    )
    handler_execution_p50_ms: float = Field(
        default=0.0, description="p50 handler duration in milliseconds"
    )
    handler_execution_p95_ms: float = Field(
        default=0.0, description="p95 handler duration in milliseconds"
    )
    handler_execution_p99_ms: float = Field(
        default=0.0, description="p99 handler duration in milliseconds"
    )
    handler_timeout_count: int = Field(
        default=0, description="Total subscriber handler timeouts observed"
    )


class EventBusMetrics:
    """Concurrency-safe metrics collector for the Event Bus."""

    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._total_published = 0
        self._accepted_events = 0
        self._delivered_events = 0
        self._rejected_events = 0
        self._dropped_events = 0
        self._failed_deliveries = 0
        self._cancelled_deliveries = 0
        self._handler_timeout_count = 0
        self._max_queue_depth = 0

        # Bounded reservoirs for latency measurements (in ms)
        self._publish_latencies: deque[float] = deque(maxlen=MAX_LATENCY_SAMPLES)
        self._handler_durations: deque[float] = deque(maxlen=MAX_LATENCY_SAMPLES)

    def record_published(self) -> None:
        self._total_published += 1

    def record_accepted(self) -> None:
        self._accepted_events += 1

    def record_delivered(self, duration_ms: float = 0.0) -> None:
        self._delivered_events += 1
        if duration_ms >= 0:
            self._handler_durations.append(duration_ms)

    def record_rejected(self) -> None:
        self._rejected_events += 1

    def record_dropped(self) -> None:
        self._dropped_events += 1

    def record_failed(self, is_timeout: bool = False) -> None:
        self._failed_deliveries += 1
        if is_timeout:
            self._handler_timeout_count += 1

    def record_cancelled(self) -> None:
        self._cancelled_deliveries += 1

    def record_publish_latency(self, latency_ms: float) -> None:
        if latency_ms >= 0:
            self._publish_latencies.append(latency_ms)

    def update_max_queue_depth(self, current_depth: int) -> None:
        if current_depth > self._max_queue_depth:
            self._max_queue_depth = current_depth

    @staticmethod
    def _compute_percentile(samples: list[float], percentile: float) -> float:
        if not samples:
            return 0.0
        sorted_samples = sorted(samples)
        idx = int(len(sorted_samples) * (percentile / 100.0))
        idx = min(idx, len(sorted_samples) - 1)
        return round(sorted_samples[idx], 3)

    def snapshot(
        self,
        active_subscriptions: int = 0,
        active_workers: int = 0,
        current_queue_depth: int = 0,
    ) -> EventBusMetricsSnapshot:
        """Generate an immutable snapshot of current metrics."""
        self.update_max_queue_depth(current_queue_depth)

        pub_samples = list(self._publish_latencies)
        hand_samples = list(self._handler_durations)

        return EventBusMetricsSnapshot(
            total_published=self._total_published,
            accepted_events=self._accepted_events,
            delivered_events=self._delivered_events,
            rejected_events=self._rejected_events,
            dropped_events=self._dropped_events,
            failed_deliveries=self._failed_deliveries,
            cancelled_deliveries=self._cancelled_deliveries,
            active_subscriptions=active_subscriptions,
            active_workers=active_workers,
            current_queue_depth=current_queue_depth,
            max_queue_depth=self._max_queue_depth,
            publish_latency_p50_ms=self._compute_percentile(pub_samples, 50.0),
            publish_latency_p95_ms=self._compute_percentile(pub_samples, 95.0),
            publish_latency_p99_ms=self._compute_percentile(pub_samples, 99.0),
            handler_execution_p50_ms=self._compute_percentile(hand_samples, 50.0),
            handler_execution_p95_ms=self._compute_percentile(hand_samples, 95.0),
            handler_execution_p99_ms=self._compute_percentile(hand_samples, 99.0),
            handler_timeout_count=self._handler_timeout_count,
        )
