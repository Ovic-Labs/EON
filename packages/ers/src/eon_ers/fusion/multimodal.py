"""Multimodal probability distribution fusion orchestrator for ERS."""

from __future__ import annotations

import time

import numpy as np

from eon_ers.config import ERSConfig
from eon_ers.contracts import EmotionObservation, FusionResult
from eon_ers.fusion.alignment import ObservationAligner
from eon_ers.fusion.confidence import DivergenceCalculator
from eon_ers.fusion.weighting import ReliabilityWeighter
from eon_ers.types import EmotionCategory, Modality


class MultimodalFusionPipeline:
    """Executes quality-aware Bayesian reliability fusion across facial and speech streams."""

    def __init__(self, config: ERSConfig) -> None:
        self.config = config
        self.aligner = ObservationAligner(
            max_divergence_seconds=config.alignment_window_seconds,
            max_staleness_seconds=3.0,
        )
        self.weighter = ReliabilityWeighter()
        self.divergence_calc = DivergenceCalculator()

    def fuse(
        self,
        facial_obs: EmotionObservation | None,
        speech_obs: EmotionObservation | None,
        current_time: float | None = None,
    ) -> FusionResult:
        """Fuse facial and acoustic speech observations into a unified FusionResult."""
        now = current_time or time.time()
        limitations: list[str] = [
            "Epistemic modesty: Fused multimodal emotion estimates reflect probabilistic observable cues, not certified psychological diagnosis."
        ]

        # 1. Temporal alignment & staleness filter
        aligned_face, aligned_speech, alignment_caveats = self.aligner.align(
            facial_obs, speech_obs, current_time=now
        )
        limitations.extend(alignment_caveats)

        missing_modalities: list[Modality] = []
        if aligned_face is None:
            missing_modalities.append(Modality.FACIAL)
        if aligned_speech is None:
            missing_modalities.append(Modality.SPEECH)

        quality_summary: dict[str, float] = {}
        if aligned_face is not None:
            quality_summary["facial_quality"] = aligned_face.quality_score
        if aligned_speech is not None:
            quality_summary["speech_quality"] = aligned_speech.quality_score

        # 2. Both modalities missing or rejected
        if aligned_face is None and aligned_speech is None:
            return FusionResult(
                timestamp=now,
                facial_observation=None,
                speech_observation=None,
                fused_probabilities={EmotionCategory.INSUFFICIENT_EVIDENCE.value: 1.0},
                dominant_estimate=EmotionCategory.INSUFFICIENT_EVIDENCE.value,
                modality_weights={Modality.FACIAL.value: 0.0, Modality.SPEECH.value: 0.0},
                confidence=0.0,
                uncertainty=1.0,
                conflicting_evidence=False,
                conflict_metric=0.0,
                missing_modalities=missing_modalities,
                quality_summary=quality_summary,
                limitations=limitations
                + ["Both sensory modalities are missing or rejected by temporal alignment."],
                contributing_model_states={},
                is_validated=False,
                is_definitive_claim=False,
            )

        # 3. Unimodal fallback: only one modality present
        if aligned_face is not None and aligned_speech is None:
            weights = {Modality.FACIAL.value: 1.0, Modality.SPEECH.value: 0.0}
            c_states = {Modality.FACIAL.value: aligned_face.model_state.value}
            return FusionResult(
                timestamp=now,
                facial_observation=aligned_face,
                speech_observation=None,
                fused_probabilities=dict(aligned_face.emotion_probabilities),
                dominant_estimate=aligned_face.dominant_estimate,
                modality_weights=weights,
                confidence=aligned_face.confidence,
                uncertainty=aligned_face.uncertainty,
                conflicting_evidence=False,
                conflict_metric=0.0,
                missing_modalities=missing_modalities,
                quality_summary=quality_summary,
                limitations=limitations
                + ["Speech modality was absent; result reflects facial-only observation."],
                contributing_model_states=c_states,
                is_validated=aligned_face.is_validated,
                is_definitive_claim=False,
            )

        if aligned_face is None and aligned_speech is not None:
            weights = {Modality.FACIAL.value: 0.0, Modality.SPEECH.value: 1.0}
            c_states = {Modality.SPEECH.value: aligned_speech.model_state.value}
            return FusionResult(
                timestamp=now,
                facial_observation=None,
                speech_observation=aligned_speech,
                fused_probabilities=dict(aligned_speech.emotion_probabilities),
                dominant_estimate=aligned_speech.dominant_estimate,
                modality_weights=weights,
                confidence=aligned_speech.confidence,
                uncertainty=aligned_speech.uncertainty,
                conflicting_evidence=False,
                conflict_metric=0.0,
                missing_modalities=missing_modalities,
                quality_summary=quality_summary,
                limitations=limitations
                + ["Facial modality was absent; result reflects speech-only observation."],
                contributing_model_states=c_states,
                is_validated=aligned_speech.is_validated,
                is_definitive_claim=False,
            )

        # 4. Multimodal Fusion: both streams present
        assert aligned_face is not None and aligned_speech is not None
        weights = self.weighter.compute_weights(aligned_face, aligned_speech)
        w_face = weights[Modality.FACIAL.value]
        w_speech = weights[Modality.SPEECH.value]

        # Conflict estimation via Jensen-Shannon Divergence
        jsd = self.divergence_calc.jensen_shannon_divergence(
            aligned_face.emotion_probabilities, aligned_speech.emotion_probabilities
        )
        is_conflicting = bool(jsd > self.config.conflict_threshold)
        if is_conflicting:
            limitations.append(
                f"Statistically divergent evidence between face and speech streams (JSD: {jsd:.2f} > {self.config.conflict_threshold})."
            )

        # Logarithmic Bayesian probability fusion
        all_categories = sorted(
            set(aligned_face.emotion_probabilities.keys())
            | set(aligned_speech.emotion_probabilities.keys())
        )
        eps = 1e-6
        log_fused: dict[str, float] = {}
        for cat in all_categories:
            p_face = aligned_face.emotion_probabilities.get(cat, eps)
            p_speech = aligned_speech.emotion_probabilities.get(cat, eps)
            log_p = w_face * np.log(max(eps, p_face)) + w_speech * np.log(max(eps, p_speech))
            log_fused[cat] = float(log_p)

        # Softmax normalization
        log_vals = np.array(list(log_fused.values()), dtype=np.float64)
        exp_vals = np.exp(log_vals - np.max(log_vals))
        fused_probs_arr = exp_vals / np.sum(exp_vals)

        fused_probabilities: dict[str, float] = {
            cat: round(float(fused_probs_arr[i]), 4) for i, cat in enumerate(log_fused.keys())
        }

        dominant_cat = max(fused_probabilities.items(), key=lambda item: item[1])[0]
        max_fused_prob = float(fused_probabilities[dominant_cat])

        # Attenuate confidence if conflict is detected
        avg_quality = float(0.5 * (aligned_face.quality_score + aligned_speech.quality_score))
        conflict_attenuation = float(1.0 - 0.4 * jsd)
        fused_confidence = float(
            np.clip(max_fused_prob * avg_quality * conflict_attenuation, 0.0, 1.0)
        )

        # Composite fused uncertainty
        clean_probs = fused_probs_arr[fused_probs_arr > 1e-12]
        entropy = -np.sum(clean_probs * np.log(clean_probs))
        k = len(fused_probabilities)
        norm_entropy = float(np.clip(entropy / (np.log(k) if k > 1 else 1.0), 0.0, 1.0))

        fused_uncertainty = float(
            np.clip(
                0.4 * norm_entropy + 0.35 * jsd + 0.25 * (1.0 - avg_quality),
                0.0,
                1.0,
            )
        )

        # Check contributing validation states
        face_val = aligned_face.is_validated if aligned_face else False
        speech_val = aligned_speech.is_validated if aligned_speech else False
        is_fused_validated = face_val or speech_val

        contributing_states: dict[str, str] = {}
        if aligned_face is not None:
            contributing_states[Modality.FACIAL.value] = aligned_face.model_state.value
        if aligned_speech is not None:
            contributing_states[Modality.SPEECH.value] = aligned_speech.model_state.value

        # Scientific Honesty: If neither contributing modality is validated,
        # we strictly suppress discrete classification to prevent fabricated emotion claims.
        if not is_fused_validated:
            dominant_cat = EmotionCategory.INSUFFICIENT_EVIDENCE.value
            fused_confidence = 0.0
            fused_uncertainty = 1.0
            limitations.append(
                "Contributing sensory models are unvalidated; discrete multimodal emotion classification suppressed."
            )
        elif (
            fused_confidence < self.config.confidence_threshold
            or fused_uncertainty > self.config.uncertainty_threshold
        ):
            dominant_cat = EmotionCategory.INSUFFICIENT_EVIDENCE.value
            fused_confidence = 0.0
            fused_uncertainty = 1.0
            limitations.append(
                f"Abstention triggered: Fused confidence {fused_confidence:.2f} < {self.config.confidence_threshold} or uncertainty {fused_uncertainty:.2f} > {self.config.uncertainty_threshold}."
            )

        return FusionResult(
            timestamp=now,
            facial_observation=aligned_face,
            speech_observation=aligned_speech,
            fused_probabilities=fused_probabilities,
            dominant_estimate=dominant_cat,
            modality_weights=weights,
            confidence=round(fused_confidence, 4),
            uncertainty=round(fused_uncertainty, 4),
            conflicting_evidence=is_conflicting,
            conflict_metric=round(jsd, 4),
            missing_modalities=missing_modalities,
            quality_summary=quality_summary,
            limitations=limitations,
            contributing_model_states=contributing_states,
            is_validated=is_fused_validated,
            is_definitive_claim=False,
        )
