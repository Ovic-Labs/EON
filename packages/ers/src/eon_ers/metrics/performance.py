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
        self._fusion_latencies: collections.deque[float] = collections.deque(maxlen=max_history)
        self._start_time = time.time()
        self._processed_count = 0
        self._error_count = 0
        self._abstention_count = 0

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
            elif modality == "multimodal":
                self._fusion_latencies.append(total_latency_ms)

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

            # Attempt to read process RSS
            rss_mb = 0.0
            try:
                import psutil

                rss_mb = round(psutil.Process(os.getpid()).memory_info().rss / (1024 * 1024), 2)
            except Exception:
                pass

            return {
                "uptime_seconds": round(uptime, 2),
                "total_processed": self._processed_count,
                "error_count": self._error_count,
                "abstention_count": self._abstention_count,
                "throughput_per_second": round(throughput, 2),
                "rss_memory_mb": rss_mb,
                "total_latency_ms": compute_percentiles(self._latencies),
                "facial_latency_ms": compute_percentiles(self._facial_latencies),
                "speech_latency_ms": compute_percentiles(self._speech_latencies),
                "fusion_latency_ms": compute_percentiles(self._fusion_latencies),
            }
