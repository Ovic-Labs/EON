"""Temporal probability smoothing and exponential decay for ERS."""

from __future__ import annotations

import numpy as np


class TemporalSmoother:
    """Bounded exponential moving average smoother with time-decay half-life."""

    def __init__(self, alpha: float = 0.35, half_life_seconds: float = 3.0) -> None:
        self.alpha = alpha
        self.half_life_seconds = half_life_seconds
        self._last_state: dict[str, float] | None = None
        self._last_timestamp: float | None = None

    def update(self, instantaneous_probs: dict[str, float], timestamp: float) -> dict[str, float]:
        """Update smoothed probability state with a new instantaneous observation."""
        if self._last_state is None or self._last_timestamp is None:
            self._last_state = dict(instantaneous_probs)
            self._last_timestamp = timestamp
            return dict(self._last_state)

        dt = max(0.0, timestamp - self._last_timestamp)
        self._last_timestamp = timestamp

        # If observation gap is much larger than half-life, decay completely and reset
        if dt > 4.0 * self.half_life_seconds:
            self._last_state = dict(instantaneous_probs)
            return dict(self._last_state)

        # Decay factor: exp(-ln(2) * dt / t_half)
        decay = float(np.exp(-np.log(2.0) * (dt / self.half_life_seconds)))
        effective_alpha = self.alpha

        all_cats = sorted(set(instantaneous_probs.keys()) | set(self._last_state.keys()))
        new_state: dict[str, float] = {}

        for cat in all_cats:
            p_inst = instantaneous_probs.get(cat, 0.0)
            p_hist = self._last_state.get(cat, 0.0)
            # EMA with temporal decay
            smoothed_val = effective_alpha * p_inst + (1.0 - effective_alpha) * p_hist * decay
            new_state[cat] = float(smoothed_val)

        # Softmax / sum normalization
        vals = np.array(list(new_state.values()), dtype=np.float64)
        sum_vals = np.sum(vals)
        if sum_vals > 0:
            norm_vals = vals / sum_vals
        else:
            norm_vals = np.ones_like(vals) / len(vals)

        self._last_state = {
            cat: round(float(norm_vals[i]), 4) for i, cat in enumerate(new_state.keys())
        }
        return dict(self._last_state)

    def reset(self) -> None:
        """Clear temporal smoothed state."""
        self._last_state = None
        self._last_timestamp = None
