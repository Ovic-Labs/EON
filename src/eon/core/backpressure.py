"""Backpressure management and queue-full policies for OVIC EON."""

from enum import Enum


class BackpressurePolicy(str, Enum):
    """Backpressure policies applied when a subscriber's bounded queue reaches capacity.

    Policies:
    - WAIT: Asynchronously wait for queue capacity up to a configurable timeout boundary.
      If timeout expires, raises QueueFullError or marks event rejected.
    - REJECT: Immediately reject the event and raise QueueFullError / record rejection.
    - DROP_NEWEST: Discard the incoming event without raising an exception; records metrics.
    - DROP_OLDEST: Evict the oldest queued event from the queue; records metrics; enqueues new.
    """

    WAIT = "wait"
    REJECT = "reject"
    DROP_NEWEST = "drop_newest"
    DROP_OLDEST = "drop_oldest"
