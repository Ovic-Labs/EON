"""Multimodal probability distribution fusion orchestrator for ERS.

Adheres strictly to Phase 3.1.4 Modality Eligibility and Scientific Isolation Rules:
- A modality is eligible for affective classification ONLY when its model is genuinely
  validated (MODEL_LOADED_VALIDATED), its output passes schema/probability validation,
  its observation is sufficiently fresh, and its sensory quality is non-unusable.
- Unvalidated, experimental, unavailable, failed or stale modalities are strictly isolated
  as diagnostic-only signals and NEVER influence classification probabilities or dominant claims.
"""

from __future__ import annotations

import time

import numpy as np

from eon_ers.config import ERSConfig
from eon_ers.contracts import EmotionObservation, FusionResult
from eon_ers.fusion.alignment import ObservationAligner
from eon_ers.fusion.confidence import DivergenceCalculator
from eon_ers.fusion.weighting import ReliabilityWeighter
from eon_ers.types import (
    EmotionCategory,
    InputQualityStatus,
    Modality,
    ModalityEligibilityStatus,
    ModelState,
    ObservationStatus,
)


def evaluate_modality_eligibility(
    obs: EmotionObservation | None,
    now: float,
    max_staleness_seconds: float = 3.0,
) -> tuple[bool, ModalityEligibilityStatus, str]:
    """Evaluate whether an observation satisfies all strict criteria for classification eligibility."""
    if obs is None:
        return False, ModalityEligibilityStatus.MISSING, "Modality observation is absent."

    # Staleness check
    age = now - obs.timestamp
    if age > max_staleness_seconds or age < -1.0:
        return (
            False,
            ModalityEligibilityStatus.STALE,
            f"Observation is stale (age: {age:.2f}s > {max_staleness_seconds}s limit).",
        )

    # Failed status
    if (
        obs.status == ObservationStatus.FAILED
        or obs.model_state == ModelState.MODEL_INFERENCE_FAILED
    ):
        return False, ModalityEligibilityStatus.FAILED, "Observation inference failed."

    # Unavailable model
    if obs.status == ObservationStatus.MODEL_UNAVAILABLE or obs.model_state in (
        ModelState.MODEL_UNAVAILABLE,
        ModelState.MODEL_MISSING,
    ):
        return False, ModalityEligibilityStatus.FAILED, "Model is unavailable."

    # Quality check
    if (
        obs.input_quality == InputQualityStatus.UNUSABLE
        or obs.status == ObservationStatus.INSUFFICIENT_EVIDENCE
    ):
        return (
            False,
            ModalityEligibilityStatus.QUALITY_UNUSABLE,
            "Sensory input quality is unusable.",
        )

    # Validation check - MUST be genuinely validated!
    if not obs.is_validated or obs.model_state != ModelState.MODEL_LOADED_VALIDATED:
        return (
            False,
            ModalityEligibilityStatus.UNVALIDATED,
            f"Model '{obs.model_id}' is unvalidated (state: {obs.model_state.value}).",
        )

    # Probability schema validation: non-empty, finite, non-negative
    probs = obs.emotion_probabilities
    if not probs:
        return (
            False,
            ModalityEligibilityStatus.DIAGNOSTIC_ONLY,
            "Empty probability distribution.",
        )

    prob_vals = list(probs.values())
    if not np.isfinite(prob_vals).all() or any(p < 0.0 for p in prob_vals):
        return (
            False,
            ModalityEligibilityStatus.DIAGNOSTIC_ONLY,
            "Probability distribution contains non-finite or negative values.",
        )

    return (
        True,
        ModalityEligibilityStatus.CLASSIFICATION_ELIGIBLE,
        "Observation is validated and eligible.",
    )


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
        """Fuse facial and acoustic speech observations with strict validation isolation."""
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

        # 2. Traceability: Collect contributing model states
        contributing_states: dict[str, str] = {}
        if aligned_face is not None:
            contributing_states[Modality.FACIAL.value] = aligned_face.model_state.value
        if aligned_speech is not None:
            contributing_states[Modality.SPEECH.value] = aligned_speech.model_state.value

        # 3. Evaluate Modality Eligibility
        face_eligible, face_status, face_reason = evaluate_modality_eligibility(
            aligned_face, now, self.aligner.max_staleness_seconds
        )
        speech_eligible, speech_status, speech_reason = evaluate_modality_eligibility(
            aligned_speech, now, self.aligner.max_staleness_seconds
        )

        eligible_modalities: list[str] = []
        diagnostic_modalities: list[str] = []

        if face_eligible:
            eligible_modalities.append(Modality.FACIAL.value)
        elif aligned_face is not None:
            diagnostic_modalities.append(Modality.FACIAL.value)
            limitations.append(f"Facial stream isolated to diagnostic-only: {face_reason}")

        if speech_eligible:
            eligible_modalities.append(Modality.SPEECH.value)
        elif aligned_speech is not None:
            diagnostic_modalities.append(Modality.SPEECH.value)
            limitations.append(f"Speech stream isolated to diagnostic-only: {speech_reason}")

        # 4. Strict Fusion Decision Tree based on Eligible Modalities

        # Case A: Neither modality is eligible for classification
        if not eligible_modalities:
            limitations.append(
                "Neither sensory modality is validated or eligible. Classification suppressed to INSUFFICIENT_EVIDENCE."
            )
            return FusionResult(
                timestamp=now,
                facial_observation=aligned_face,
                speech_observation=aligned_speech,
                fused_probabilities={EmotionCategory.INSUFFICIENT_EVIDENCE.value: 1.0},
                dominant_estimate=EmotionCategory.INSUFFICIENT_EVIDENCE.value,
                modality_weights={Modality.FACIAL.value: 0.0, Modality.SPEECH.value: 0.0},
                confidence=0.0,
                uncertainty=1.0,
                conflicting_evidence=False,
                conflict_metric=0.0,
                missing_modalities=missing_modalities,
                quality_summary=quality_summary,
                limitations=limitations,
                contributing_model_states=contributing_states,
                classification_eligible_modalities=[],
                diagnostic_modalities=diagnostic_modalities,
                fusion_status="insufficient_evidence_unvalidated",
                is_validated=False,
                is_definitive_claim=False,
            )

        # Case B: Facial eligible only (Speech is unvalidated, failed, stale, or absent)
        if eligible_modalities == [Modality.FACIAL.value]:
            assert aligned_face is not None
            weights = {Modality.FACIAL.value: 1.0, Modality.SPEECH.value: 0.0}
            if aligned_speech is not None:
                limitations.append(
                    "Speech stream is unvalidated/diagnostic; classification is strictly grounded in validated facial evidence."
                )
            else:
                limitations.append(
                    "Speech modality was absent; result reflects facial-only observation."
                )

            return FusionResult(
                timestamp=now,
                facial_observation=aligned_face,
                speech_observation=aligned_speech,  # Retained for diagnostic observability
                fused_probabilities=dict(aligned_face.emotion_probabilities),
                dominant_estimate=aligned_face.dominant_estimate,
                modality_weights=weights,
                confidence=aligned_face.confidence,
                uncertainty=aligned_face.uncertainty,
                conflicting_evidence=False,
                conflict_metric=0.0,
                missing_modalities=missing_modalities,
                quality_summary=quality_summary,
                limitations=limitations,
                contributing_model_states=contributing_states,
                classification_eligible_modalities=eligible_modalities,
                diagnostic_modalities=diagnostic_modalities,
                fusion_status="facial_only_validated",
                is_validated=True,
                is_definitive_claim=False,
            )

        # Case C: Speech eligible only (Facial is unvalidated, failed, stale, or absent)
        if eligible_modalities == [Modality.SPEECH.value]:
            assert aligned_speech is not None
            weights = {Modality.FACIAL.value: 0.0, Modality.SPEECH.value: 1.0}
            if aligned_face is not None:
                limitations.append(
                    "Facial stream is unvalidated/diagnostic; classification is strictly grounded in validated speech evidence."
                )
            else:
                limitations.append(
                    "Facial modality was absent; result reflects speech-only observation."
                )

            return FusionResult(
                timestamp=now,
                facial_observation=aligned_face,  # Retained for diagnostic observability
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
                limitations=limitations,
                contributing_model_states=contributing_states,
                classification_eligible_modalities=eligible_modalities,
                diagnostic_modalities=diagnostic_modalities,
                fusion_status="speech_only_validated",
                is_validated=True,
                is_definitive_claim=False,
            )

        # Case D: Both modalities are validated and eligible for fusion
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

        # Logarithmic Bayesian probability fusion of eligible streams
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

        # Threshold gating on fused observation
        if (
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
            classification_eligible_modalities=eligible_modalities,
            diagnostic_modalities=diagnostic_modalities,
            fusion_status="multimodal_fused",
            is_validated=True,
            is_definitive_claim=False,
        )
