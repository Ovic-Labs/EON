"""Runtime performance tracking and latency percentile computation for ERS."""

from __future__ import annotations

import collections
import os
import threading
import time
from typing import Any

import numpy as np


class PerformanceTracker:
    """Thread-safe performance, throughput, and latency monitor."""

    def __init__(self, max_history: int = 5000) -> None:
        self.max_history = max_history
        self._lock = threading.Lock()
        self._latencies: collections.deque[float] = collections.deque(maxlen=max_history)
        self._facial_latencies: collections.deque[float] = collections.deque(maxlen=max_history)
        self._speech_latencies: collections.deque[float] = collections.deque(maxlen=max_history)
        self._text_latencies: collections.deque[float] = collections.deque(maxlen=max_history)
        self._video_latencies: collections.deque[float] = collections.deque(maxlen=max_history)
        self._fusion_latencies: collections.deque[float] = collections.deque(maxlen=max_history)
        self._queue_delays: collections.deque[float] = collections.deque(maxlen=max_history)
        self._start_time = time.time()
        self._processed_count = 0
        self._error_count = 0
        self._abstention_count = 0
        self._dropped_frames = 0
        self._ws_active_connections = 0
        self._ws_messages_total = 0
        self._model_load_failures = 0
        self._dataset_integrity_failures = 0

    def record_process(
        self,
        total_latency_ms: float,
        modality: str,
        is_error: bool = False,
        is_abstention: bool = False,
    ) -> None:
        """Record the latency and outcome of an inference processing operation."""
        with self._lock:
            self._processed_count += 1
            if is_error:
                self._error_count += 1
            if is_abstention:
                self._abstention_count += 1

            self._latencies.append(total_latency_ms)
            if modality == "facial":
                self._facial_latencies.append(total_latency_ms)
            elif modality == "speech":
                self._speech_latencies.append(total_latency_ms)
            elif modality == "text":
                self._text_latencies.append(total_latency_ms)
            elif modality == "video":
                self._video_latencies.append(total_latency_ms)
            elif modality == "multimodal":
                self._fusion_latencies.append(total_latency_ms)

    def record_queue_delay(self, delay_ms: float) -> None:
        """Record queue wait time before worker execution."""
        with self._lock:
            self._queue_delays.append(max(0.0, float(delay_ms)))

    def record_dropped_frame(self, count: int = 1) -> None:
        """Increment dropped frame/chunk counter under overload backpressure."""
        with self._lock:
            self._dropped_frames += max(0, int(count))

    def record_ws_connect(self) -> None:
        with self._lock:
            self._ws_active_connections += 1

    def record_ws_disconnect(self) -> None:
        with self._lock:
            self._ws_active_connections = max(0, self._ws_active_connections - 1)

    def record_ws_message(self) -> None:
        with self._lock:
            self._ws_messages_total += 1

    def record_model_load_failure(self) -> None:
        with self._lock:
            self._model_load_failures += 1

    def record_dataset_integrity_failure(self) -> None:
        with self._lock:
            self._dataset_integrity_failures += 1

    def get_summary(self) -> dict[str, Any]:
        """Compute statistical summary including p50, p90, p95, p99 latencies and throughput."""
        with self._lock:
            uptime = max(0.001, time.time() - self._start_time)
            throughput = self._processed_count / uptime

            def compute_percentiles(dq: collections.deque[float]) -> dict[str, float]:
                if not dq:
                    return {"p50": 0.0, "p90": 0.0, "p95": 0.0, "p99": 0.0, "mean": 0.0}
                arr = np.array(dq, dtype=np.float64)
                return {
                    "p50": round(float(np.percentile(arr, 50)), 2),
                    "p90": round(float(np.percentile(arr, 90)), 2),
                    "p95": round(float(np.percentile(arr, 95)), 2),
                    "p99": round(float(np.percentile(arr, 99)), 2),
                    "mean": round(float(np.mean(arr)), 2),
                }

            rss_mb = 0.0
            cpu_percent = 0.0
            try:
                import psutil

                proc = psutil.Process(os.getpid())
                rss_mb = round(proc.memory_info().rss / (1024 * 1024), 2)
                cpu_percent = round(float(proc.cpu_percent(interval=None)), 2)
            except Exception:
                pass

            total_pcts = compute_percentiles(self._latencies)
            facial_pcts = compute_percentiles(self._facial_latencies)
            speech_pcts = compute_percentiles(self._speech_latencies)
            fusion_pcts = compute_percentiles(self._fusion_latencies)

            return {
                "uptime_seconds": round(uptime, 2),
                "total_processed": self._processed_count,
                "error_count": self._error_count,
                "abstention_count": self._abstention_count,
                "error_rate": round(self._error_count / max(1, self._processed_count), 4),
                "dropped_frames": self._dropped_frames,
                "ws_active_connections": self._ws_active_connections,
                "ws_messages_total": self._ws_messages_total,
                "model_load_failures": self._model_load_failures,
                "dataset_integrity_failures": self._dataset_integrity_failures,
                "throughput_per_second": round(throughput, 2),
                "rss_memory_mb": rss_mb,
                "cpu_percent": cpu_percent,
                "latency_p50_ms": total_pcts["p50"],
                "latency_p95_ms": total_pcts["p95"],
                "latency_p99_ms": total_pcts["p99"],
                "last_facial_latency_ms": self._facial_latencies[-1]
                if self._facial_latencies
                else 0.0,
                "last_speech_latency_ms": self._speech_latencies[-1]
                if self._speech_latencies
                else 0.0,
                "last_fusion_latency_ms": self._fusion_latencies[-1]
                if self._fusion_latencies
                else 0.0,
                "total_latency_ms": total_pcts,
                "facial_latency_ms": facial_pcts,
                "speech_latency_ms": speech_pcts,
                "text_latency_ms": compute_percentiles(self._text_latencies),
                "video_latency_ms": compute_percentiles(self._video_latencies),
                "fusion_latency_ms": fusion_pcts,
                "queue_delay_ms": compute_percentiles(self._queue_delays),
            }

    def render_prometheus(self) -> str:
        """Render runtime metrics in Prometheus text exposition format."""
        s = self.get_summary()
        lines = [
            "# HELP eon_ers_processed_total Total observations processed by ERS.",
            "# TYPE eon_ers_processed_total counter",
            f"eon_ers_processed_total {s['total_processed']}",
            "# HELP eon_ers_errors_total Total processing errors.",
            "# TYPE eon_ers_errors_total counter",
            f"eon_ers_errors_total {s['error_count']}",
            "# HELP eon_ers_dropped_frames_total Frames/chunks dropped under overload.",
            "# TYPE eon_ers_dropped_frames_total counter",
            f"eon_ers_dropped_frames_total {s['dropped_frames']}",
            "# HELP eon_ers_ws_active_connections Current open WebSocket streams.",
            "# TYPE eon_ers_ws_active_connections gauge",
            f"eon_ers_ws_active_connections {s['ws_active_connections']}",
            "# HELP eon_ers_memory_rss_mb Process resident set size in megabytes.",
            "# TYPE eon_ers_memory_rss_mb gauge",
            f"eon_ers_memory_rss_mb {s['rss_memory_mb']}",
            "# HELP eon_ers_latency_p95_ms 95th percentile end-to-end latency in milliseconds.",
            "# TYPE eon_ers_latency_p95_ms gauge",
            f"eon_ers_latency_p95_ms {s['latency_p95_ms']}",
        ]
        return "\n".join(lines) + "\n"
