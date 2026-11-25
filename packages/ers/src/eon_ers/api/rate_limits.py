"""Thread-safe sliding-window rate limiter for ERS REST and WebSocket endpoints."""

from __future__ import annotations

import collections
import threading
import time

from eon_ers.exceptions import ERSRateLimitError


class SlidingWindowRateLimiter:
    """Enforces per-client request rate limits using a bounded 60-second sliding window."""

    def __init__(self, max_requests_per_minute: int = 600, window_seconds: float = 60.0) -> None:
        self.max_requests = max(1, int(max_requests_per_minute))
        self.window_seconds = max(1.0, float(window_seconds))
        self._lock = threading.Lock()
        self._buckets: dict[str, collections.deque[float]] = {}

    def check_and_record(self, client_key: str) -> int:
        """Record an inbound request or raise `ERSRateLimitError`; returns remaining quota."""
        now = time.monotonic()
        cutoff = now - self.window_seconds
        with self._lock:
            dq = self._buckets.get(client_key)
            if dq is None:
                dq = collections.deque()
                self._buckets[client_key] = dq
            while dq and dq[0] < cutoff:
                dq.popleft()
            if len(dq) >= self.max_requests:
                raise ERSRateLimitError(
                    f"Rate limit exceeded ({self.max_requests} requests per {int(self.window_seconds)}s).",
                    context={"limit": self.max_requests},
                )
            dq.append(now)
            return max(0, self.max_requests - len(dq))
