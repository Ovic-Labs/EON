"""Media retention enforcement and memory buffer scrubber for ERS."""

from __future__ import annotations

import logging
from typing import Any

from eon_ers.contracts import ERSInput

logger = logging.getLogger("eon.ers.privacy.retention")


class MediaRetentionGuard:
    """Enforces the zero-disk-retention invariant by preventing disk persistence of raw media."""

    def __init__(self, zero_disk_retention: bool = True) -> None:
        self.zero_disk_retention = zero_disk_retention

    def scrub(self, inp: ERSInput) -> None:
        """Securely wipe raw image and audio payloads from the input envelope."""
        inp.scrub_media_payload()

    def assert_zero_disk_leak(self, path_or_obj: Any) -> None:
        """Ensure no raw binary media has been directed to persistent storage."""
        if not self.zero_disk_retention:
            return
        if (
            isinstance(path_or_obj, str)
            and not path_or_obj.startswith("/dev/shm")
            and not path_or_obj.startswith("memory://")
        ):
            if any(
                path_or_obj.lower().endswith(ext)
                for ext in [".jpg", ".jpeg", ".png", ".wav", ".pcm"]
            ):
                raise RuntimeError(
                    f"Privacy invariant violation: Attempted to write raw sensory media to persistent disk at '{path_or_obj}'."
                )
