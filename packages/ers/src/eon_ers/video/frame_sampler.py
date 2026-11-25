"""Configurable frame sampler and perceptual duplicate-frame filter for ERS video."""

from __future__ import annotations

import io
from collections.abc import Iterable, Iterator

import numpy as np
from PIL import Image

from eon_ers.video.decoder import DecodedVideoFrame


class FrameSampler:
    """Samples frames at target FPS with duplicate skipping and hard frame limits."""

    def __init__(
        self,
        sample_fps: float = 2.0,
        max_frames: int = 120,
        duplicate_mae_threshold: float = 0.005,
    ) -> None:
        self.sample_fps = max(0.05, float(sample_fps))
        self.max_frames = max(1, int(max_frames))
        self.duplicate_mae_threshold = float(duplicate_mae_threshold)
        self.skipped_duplicates = 0

    def sample(self, frames: Iterable[DecodedVideoFrame]) -> Iterator[DecodedVideoFrame]:
        """Yield temporally spaced, non-duplicate frames up to `max_frames`."""
        min_interval = 1.0 / self.sample_fps
        last_ts = -1e9
        prev_thumb: np.ndarray | None = None
        emitted = 0
        self.skipped_duplicates = 0

        for frame in frames:
            if emitted >= self.max_frames:
                break
            if emitted > 0 and (frame.timestamp_seconds - last_ts) < (min_interval - 1e-6):
                continue

            try:
                img = Image.open(io.BytesIO(frame.image_bytes)).convert("L").resize((16, 16))
                thumb = np.array(img, dtype=np.float32) / 255.0
            except Exception:
                continue

            if prev_thumb is not None:
                mae = float(np.mean(np.abs(thumb - prev_thumb)))
                if mae < self.duplicate_mae_threshold:
                    self.skipped_duplicates += 1
                    continue

            prev_thumb = thumb
            last_ts = frame.timestamp_seconds
            emitted += 1
            yield frame
