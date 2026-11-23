"""Unit tests for event bus metrics and operational snapshot collection."""

from eon.core.metrics import EventBusMetrics, EventBusMetricsSnapshot


def test_metrics_counter_recording() -> None:
    """Verify metrics accurately accumulate publishing and delivery counts."""
    m = EventBusMetrics()
    m.record_published()
    m.record_published()
    m.record_accepted()
    m.record_delivered(duration_ms=2.5)
    m.record_rejected()
    m.record_dropped()
    m.record_failed(is_timeout=True)
    m.record_cancelled()

    snap = m.snapshot(active_subscriptions=3, active_workers=3, current_queue_depth=5)
    assert snap.total_published == 2
    assert snap.accepted_events == 1
    assert snap.delivered_events == 1
    assert snap.rejected_events == 1
    assert snap.dropped_events == 1
    assert snap.failed_deliveries == 1
    assert snap.handler_timeout_count == 1
    assert snap.cancelled_deliveries == 1
    assert snap.active_subscriptions == 3
    assert snap.active_workers == 3
    assert snap.current_queue_depth == 5
    assert snap.max_queue_depth == 5


def test_metrics_latency_percentiles() -> None:
    """Verify latency percentiles (p50, p95, p99) compute correctly."""
    m = EventBusMetrics()
    for latency in range(1, 101):
        m.record_publish_latency(float(latency))

    snap = m.snapshot()
    # 1 to 100 values
    assert snap.publish_latency_p50_ms == 51.0
    assert snap.publish_latency_p95_ms == 96.0
    assert snap.publish_latency_p99_ms == 100.0


def test_metrics_snapshot_immutability() -> None:
    """Verify metrics snapshot is an immutable Pydantic model."""
    m = EventBusMetrics()
    snap = m.snapshot()
    assert isinstance(snap, EventBusMetricsSnapshot)
    # Extra fields are forbidden
    assert hasattr(snap, "total_published")
