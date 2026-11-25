"""Bounded overlapping audio window segmentation for streaming or long recordings."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class AudioSegment:
    """Single bounded time-stamped audio analysis window."""

    index: int
    start_seconds: float
    end_seconds: float
    samples: np.ndarray


class AudioSegmenter:
    """Slices continuous mono audio waveforms into fixed bounded analysis windows."""

    def __init__(
        self,
        window_seconds: float = 2.0,
        hop_seconds: float = 1.0,
        max_segments: int = 30,
    ) -> None:
        if window_seconds <= 0.05 or hop_seconds <= 0.05:
            raise ValueError("Audio window and hop durations must exceed 0.05s.")
        self.window_seconds = window_seconds
        self.hop_seconds = hop_seconds
        self.max_segments = max_segments

    def segment(self, samples: np.ndarray, sample_rate: int) -> list[AudioSegment]:
        """Slice waveform into bounded overlapping `AudioSegment` objects."""
        if len(samples) == 0 or sample_rate <= 0:
            return []

        win_samples = max(1, int(round(self.window_seconds * sample_rate)))
        hop_samples = max(1, int(round(self.hop_seconds * sample_rate)))
        n = len(samples)

        if n <= win_samples:
            return [
                AudioSegment(
                    index=0,
                    start_seconds=0.0,
                    end_seconds=round(n / sample_rate, 4),
                    samples=samples,
                )
            ]

        segments: list[AudioSegment] = []
        offset = 0
        idx = 0
        while offset < n and len(segments) < self.max_segments:
            end = min(n, offset + win_samples)
            if (end - offset) < max(1, win_samples // 4) and idx > 0:
                break
            segments.append(
                AudioSegment(
                    index=idx,
                    start_seconds=round(offset / sample_rate, 4),
                    end_seconds=round(end / sample_rate, 4),
                    samples=samples[offset:end],
                )
            )
            idx += 1
            if end >= n:
                break
            offset += hop_samples
        return segments
