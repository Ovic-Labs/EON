"""Host CPU, memory, thread, and ONNX runtime provider diagnostics."""

from __future__ import annotations

import os
import platform
from typing import Any


def collect_system_diagnostics() -> dict[str, Any]:
    """Collect real local CPU, RSS memory, thread, and inference provider telemetry."""
    rss_mb = 0.0
    cpu_pct = 0.0
    num_threads = 0
    try:
        import psutil

        proc = psutil.Process(os.getpid())
        rss_mb = round(proc.memory_info().rss / (1024 * 1024), 2)
        cpu_pct = round(float(proc.cpu_percent(interval=None)), 2)
        num_threads = proc.num_threads()
    except Exception:
        pass

    ort_providers: list[str] = []
    ort_version: str | None = None
    try:
        import onnxruntime as ort

        ort_providers = list(ort.get_available_providers())
        ort_version = getattr(ort, "__version__", None)
    except Exception:
        pass

    return {
        "platform": platform.system(),
        "machine": platform.machine(),
        "python_version": platform.python_version(),
        "cpu_count": os.cpu_count() or 1,
        "process_cpu_percent": cpu_pct,
        "process_rss_mb": rss_mb,
        "process_threads": num_threads,
        "onnxruntime_version": ort_version,
        "onnxruntime_providers": ort_providers,
    }
