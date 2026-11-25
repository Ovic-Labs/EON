"""Polyphase CPU audio sample-rate converter for ERS."""

from __future__ import annotations

import math

import numpy as np
from scipy.signal import resample_poly


class AudioResampler:
    """Resamples mono float32 waveforms to the model's expected sample rate."""

    def resample(
        self, samples: np.ndarray, source_rate: int, target_rate: int = 16000
    ) -> np.ndarray:
        """Convert audio waveform from `source_rate` to `target_rate` on CPU."""
        if len(samples) == 0 or source_rate <= 0 or target_rate <= 0:
            return samples.astype(np.float32, copy=False)
        if source_rate == target_rate:
            return samples.astype(np.float32, copy=False)

        gcd = math.gcd(int(source_rate), int(target_rate))
        up = int(target_rate) // gcd
        down = int(source_rate) // gcd
        resampled = resample_poly(samples.astype(np.float64), up=up, down=down)
        return np.clip(resampled, -1.0, 1.0).astype(np.float32)
