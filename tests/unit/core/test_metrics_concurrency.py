"""Tests for EventBusMetrics thread safety and internally consistent snapshots."""

import concurrent.futures
import threading

from eon.core.metrics import EventBusMetrics


def test_concurrent_metrics_thread_safety() -> None:
    """Verify EventBusMetrics maintains consistency under high-concurrency multi-threaded access."""
    metrics = EventBusMetrics()
    n_threads = 8
    updates_per_thread = 500
    expected_total = n_threads * updates_per_thread

    snapshots_captured = []
    stop_event = threading.Event()

    def updater(_thread_id: int) -> None:
        for _ in range(updates_per_thread):
            metrics.record_published()
            metrics.record_accepted()
            metrics.record_delivered(1.5)
            metrics.record_publish_latency(0.8)

    def snapshotter() -> None:
        while not stop_event.is_set():
            snap = metrics.snapshot(active_subscriptions=2, active_workers=4, current_queue_depth=5)
            snapshots_captured.append(snap)

    with concurrent.futures.ThreadPoolExecutor(max_workers=n_threads + 1) as executor:
        snap_future = executor.submit(snapshotter)
        updater_futures = [executor.submit(updater, i) for i in range(n_threads)]

        concurrent.futures.wait(updater_futures)
        stop_event.set()
        snap_future.result()

    final_snap = metrics.snapshot()
    assert final_snap.total_published == expected_total
    assert final_snap.accepted_events == expected_total
    assert final_snap.delivered_events == expected_total

    # Verify every captured snapshot is internally consistent
    for snap in snapshots_captured:
        assert snap.total_published >= snap.accepted_events
        assert snap.total_published >= snap.delivered_events
        assert snap.active_subscriptions == 2
        assert snap.active_workers == 4
