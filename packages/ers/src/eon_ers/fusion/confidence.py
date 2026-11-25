"""Conflict detection and uncertainty estimation for multimodal fusion in ERS."""

from __future__ import annotations

import numpy as np


class DivergenceCalculator:
    """Computes Jensen-Shannon divergence to identify conflicting multimodal evidence."""

    @staticmethod
    def jensen_shannon_divergence(dist_p: dict[str, float], dist_q: dict[str, float]) -> float:
        """Compute normalized Jensen-Shannon divergence in [0.0, 1.0] between two distributions."""
        all_keys = sorted(set(dist_p.keys()) | set(dist_q.keys()))
        eps = 1e-12

        p = np.array([max(eps, dist_p.get(k, 0.0)) for k in all_keys], dtype=np.float64)
        q = np.array([max(eps, dist_q.get(k, 0.0)) for k in all_keys], dtype=np.float64)

        # Normalize
        p /= np.sum(p)
        q /= np.sum(q)

        m = 0.5 * (p + q)

        kl_pm = np.sum(p * np.log(p / m))
        kl_qm = np.sum(q * np.log(q / m))
        jsd = 0.5 * (kl_pm + kl_qm)

        # Maximum possible JSD for discrete distributions with natural log is ln(2)
        max_jsd = np.log(2.0)
        norm_jsd = float(np.clip(jsd / max_jsd, 0.0, 1.0))
        return norm_jsd

    @classmethod
    def multi_stream_divergence(cls, distributions: dict[str, dict[str, float]]) -> float:
        """Compute maximum normalized pairwise JSD across all active probability distributions."""
        keys = list(distributions.keys())
        if len(keys) < 2:
            return 0.0
        max_div = 0.0
        for i in range(len(keys)):
            for j in range(i + 1, len(keys)):
                div = cls.jensen_shannon_divergence(distributions[keys[i]], distributions[keys[j]])
                if div > max_div:
                    max_div = div
        return max_div
