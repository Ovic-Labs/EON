"""Temporal alignment and stale rejection for multimodal observations in ERS."""

from __future__ import annotations

import time

from eon_ers.contracts import EmotionObservation


class ObservationAligner:
    """Aligns asynchronous perceptual observations within a sliding time window."""

    def __init__(
        self, max_divergence_seconds: float = 0.5, max_staleness_seconds: float = 3.0
    ) -> None:
        self.max_divergence_seconds = max_divergence_seconds
        self.max_staleness_seconds = max_staleness_seconds

    def align(
        self,
        facial_obs: EmotionObservation | None,
        speech_obs: EmotionObservation | None,
        current_time: float | None = None,
    ) -> tuple[EmotionObservation | None, EmotionObservation | None, list[str]]:
        """Validate timestamps and align observations, returning aligned pair and caveats."""
        caveats: list[str] = []
        now = current_time or time.time()

        valid_face = facial_obs
        valid_speech = speech_obs

        # 1. Check staleness against current wall-clock
        if valid_face is not None:
            face_age = now - valid_face.timestamp
            if face_age > self.max_staleness_seconds:
                caveats.append(
                    f"Facial observation is stale (age: {face_age:.2f}s > {self.max_staleness_seconds}s)"
                )
                valid_face = None

        if valid_speech is not None:
            speech_age = now - valid_speech.timestamp
            if speech_age > self.max_staleness_seconds:
                caveats.append(
                    f"Speech observation is stale (age: {speech_age:.2f}s > {self.max_staleness_seconds}s)"
                )
                valid_speech = None

        # 2. Check temporal divergence between streams
        if valid_face is not None and valid_speech is not None:
            dt = abs(valid_face.timestamp - valid_speech.timestamp)
            if dt > self.max_divergence_seconds:
                caveats.append(
                    f"Temporal divergence between facial and speech observations exceeds window ({dt:.3f}s > {self.max_divergence_seconds}s). Discarding older modality."
                )
                if valid_face.timestamp > valid_speech.timestamp:
                    valid_speech = None
                else:
                    valid_face = None

        return valid_face, valid_speech, caveats

    def align_many(
        self,
        observations: dict[str, EmotionObservation | None],
        current_time: float | None = None,
    ) -> tuple[dict[str, EmotionObservation | None], list[str]]:
        """Align 2 or 3 modality streams within staleness and temporal divergence windows."""
        now = current_time or time.time()
        caveats: list[str] = []
        valid: dict[str, EmotionObservation | None] = dict(observations)

        for name, obs in list(valid.items()):
            if obs is None:
                continue
            age = now - obs.timestamp
            if age > self.max_staleness_seconds or age < -1.0:
                caveats.append(
                    f"{name.capitalize()} observation is stale (age: {age:.2f}s > {self.max_staleness_seconds}s)"
                )
                valid[name] = None

        active = [(k, v) for k, v in valid.items() if v is not None]
        if len(active) >= 2:
            newest_name, newest_obs = max(active, key=lambda kv: kv[1].timestamp)
            for name, obs in active:
                if name == newest_name:
                    continue
                dt = abs(newest_obs.timestamp - obs.timestamp)
                if dt > self.max_divergence_seconds:
                    caveats.append(
                        f"Temporal divergence between {newest_name} and {name} exceeds window "
                        f"({dt:.3f}s > {self.max_divergence_seconds}s). Discarding older {name} observation."
                    )
                    valid[name] = None

        return valid, caveats
