"""Quality-aware and uncertainty-attenuated reliability weighting for ERS."""

from __future__ import annotations

from eon_ers.contracts import EmotionObservation
from eon_ers.types import Modality


class ReliabilityWeighter:
    """Calculates dynamic fusion weights based on signal quality and model certainty."""

    def compute_weights(
        self,
        facial_obs: EmotionObservation | None,
        speech_obs: EmotionObservation | None,
    ) -> dict[str, float]:
        r"""Compute normalized weights for contributing modalities.

        Weight formulation:
        $R_m = Q_m \cdot (1 - U_m) \cdot C_m$
        where $Q_m$ is quality, $U_m$ is uncertainty, and $C_m$ is confidence.
        """
        weights: dict[str, float] = {
            Modality.FACIAL.value: 0.0,
            Modality.SPEECH.value: 0.0,
        }

        r_face = 0.0
        if facial_obs is not None:
            r_face = float(
                facial_obs.quality_score
                * (1.0 - facial_obs.uncertainty)
                * max(0.05, facial_obs.confidence)
            )

        r_speech = 0.0
        if speech_obs is not None:
            r_speech = float(
                speech_obs.quality_score
                * (1.0 - speech_obs.uncertainty)
                * max(0.05, speech_obs.confidence)
            )

        total_r = r_face + r_speech
        if total_r > 1e-9:
            weights[Modality.FACIAL.value] = round(r_face / total_r, 4)
            weights[Modality.SPEECH.value] = round(r_speech / total_r, 4)
        elif facial_obs is not None and speech_obs is not None:
            weights[Modality.FACIAL.value] = 0.5
            weights[Modality.SPEECH.value] = 0.5
        elif facial_obs is not None:
            weights[Modality.FACIAL.value] = 1.0
        elif speech_obs is not None:
            weights[Modality.SPEECH.value] = 1.0

        return weights

    def compute_n_weights(
        self, observations: dict[str, EmotionObservation | None]
    ) -> dict[str, float]:
        """Compute normalized quality- and uncertainty-attenuated reliability weights for N streams."""
        raw_scores: dict[str, float] = {}
        for name, obs in observations.items():
            if obs is None:
                raw_scores[name] = 0.0
            else:
                raw_scores[name] = float(
                    obs.quality_score * (1.0 - obs.uncertainty) * max(0.05, obs.confidence)
                )

        active_names = [k for k, v in observations.items() if v is not None]
        total_r = sum(raw_scores.values())
        if total_r > 1e-9:
            return {k: round(raw_scores[k] / total_r, 4) for k in observations}
        if active_names:
            uniform = round(1.0 / len(active_names), 4)
            return {k: (uniform if k in active_names else 0.0) for k in observations}
        return {k: 0.0 for k in observations}
