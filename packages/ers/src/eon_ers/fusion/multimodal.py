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

SUPPORTED_EMOTION_CLASSES: frozenset[str] = frozenset(
    {
        EmotionCategory.NEUTRAL.value,
        EmotionCategory.HAPPINESS.value,
        EmotionCategory.SADNESS.value,
        EmotionCategory.ANGER.value,
        EmotionCategory.FEAR.value,
        EmotionCategory.SURPRISE.value,
        EmotionCategory.DISGUST.value,
    }
)
PROBABILITY_SUM_TOLERANCE: float = 0.02


def validate_emotion_probabilities(
    probs: dict[str, float] | None,
    tolerance: float = PROBABILITY_SUM_TOLERANCE,
) -> tuple[bool, str]:
    """Validate that probability distribution covers all supported emotion classes and sums to 1 within tolerance."""
    if not probs:
        return False, "Empty or absent probability distribution."

    prob_keys = set(probs.keys())
    if prob_keys != SUPPORTED_EMOTION_CLASSES:
        missing = SUPPORTED_EMOTION_CLASSES - prob_keys
        extra = prob_keys - SUPPORTED_EMOTION_CLASSES
        reasons: list[str] = []
        if missing:
            reasons.append(f"missing classes: {sorted(missing)}")
        if extra:
            reasons.append(f"unsupported classes: {sorted(extra)}")
        return False, f"Invalid emotion probability keys ({'; '.join(reasons)})."

    vals = list(probs.values())
    if not np.isfinite(vals).all():
        return False, "Probability distribution contains non-finite values (NaN or Inf)."

    if any(p < 0.0 for p in vals):
        return False, "Probability distribution contains negative probability values."

    total = float(sum(vals))
    if abs(total - 1.0) > tolerance:
        return (
            False,
            f"Probability distribution does not sum to 1.0 within tolerance {tolerance} (sum={total:.4f}).",
        )

    return True, "Valid emotion probability distribution."


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

    # Probability schema and distribution validation: supported classes, finite, non-negative, unit sum
    probs = obs.emotion_probabilities
    is_valid, prob_reason = validate_emotion_probabilities(probs)
    if not is_valid:
        return (
            False,
            ModalityEligibilityStatus.DIAGNOSTIC_ONLY,
            f"Invalid probability distribution: {prob_reason}",
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
        *,
        text_obs: EmotionObservation | None = None,
        session_id: str | None = None,
    ) -> FusionResult:
        """Fuse facial, acoustic speech, and optional text affect observations with validation isolation."""
        t0 = time.perf_counter()
        now = current_time or time.time()
        limitations: list[str] = [
            "Epistemic modesty: Fused multimodal emotion estimates reflect probabilistic observable cues, not certified psychological diagnosis."
        ]

        include_text = text_obs is not None

        # 1. Temporal alignment & staleness filter
        if include_text:
            aligned_map, alignment_caveats = self.aligner.align_many(
                {
                    Modality.FACIAL.value: facial_obs,
                    Modality.SPEECH.value: speech_obs,
                    Modality.TEXT.value: text_obs,
                },
                current_time=now,
            )
            aligned_face = aligned_map[Modality.FACIAL.value]
            aligned_speech = aligned_map[Modality.SPEECH.value]
            aligned_text = aligned_map[Modality.TEXT.value]
        else:
            aligned_face, aligned_speech, alignment_caveats = self.aligner.align(
                facial_obs, speech_obs, current_time=now
            )
            aligned_text = None
        limitations.extend(alignment_caveats)

        missing_modalities: list[Modality] = []
        if aligned_face is None:
            missing_modalities.append(Modality.FACIAL)
        if aligned_speech is None:
            missing_modalities.append(Modality.SPEECH)
        if include_text and aligned_text is None:
            missing_modalities.append(Modality.TEXT)

        quality_summary: dict[str, float] = {}
        if aligned_face is not None:
            quality_summary["facial_quality"] = aligned_face.quality_score
        if aligned_speech is not None:
            quality_summary["speech_quality"] = aligned_speech.quality_score
        if aligned_text is not None:
            quality_summary["text_quality"] = aligned_text.quality_score

        # 2. Traceability: Collect contributing model states
        contributing_states: dict[str, str] = {}
        if aligned_face is not None:
            contributing_states[Modality.FACIAL.value] = aligned_face.model_state.value
        if aligned_speech is not None:
            contributing_states[Modality.SPEECH.value] = aligned_speech.model_state.value
        if aligned_text is not None:
            contributing_states[Modality.TEXT.value] = aligned_text.model_state.value

        # 3. Evaluate Modality Eligibility
        obs_by_name: dict[str, EmotionObservation | None] = {
            Modality.FACIAL.value: aligned_face,
            Modality.SPEECH.value: aligned_speech,
        }
        if include_text:
            obs_by_name[Modality.TEXT.value] = aligned_text

        eligible_obs: dict[str, EmotionObservation] = {}
        eligible_modalities: list[str] = []
        diagnostic_modalities: list[str] = []
        excluded_modalities: list[str] = [m.value for m in missing_modalities]

        for mod_name, mod_obs in obs_by_name.items():
            is_el, _, reason = evaluate_modality_eligibility(
                mod_obs, now, self.aligner.max_staleness_seconds
            )
            if is_el and mod_obs is not None:
                eligible_modalities.append(mod_name)
                eligible_obs[mod_name] = mod_obs
            elif mod_obs is not None:
                diagnostic_modalities.append(mod_name)
                excluded_modalities.append(mod_name)
                limitations.append(
                    f"{mod_name.capitalize()} stream isolated to diagnostic-only: {reason}"
                )

        # 4. Strict Fusion Decision Tree based on Eligible Modalities
        base_zero_weights = {k: 0.0 for k in obs_by_name}

        # Case A: No modality is eligible for classification
        if not eligible_modalities:
            limitations.append(
                "No sensory modality is validated or eligible. Classification suppressed to INSUFFICIENT_EVIDENCE."
            )
            return FusionResult(
                session_id=session_id,
                timestamp=now,
                facial_observation=aligned_face,
                speech_observation=aligned_speech,
                text_observation=aligned_text,
                fused_probabilities={EmotionCategory.INSUFFICIENT_EVIDENCE.value: 1.0},
                dominant_estimate=EmotionCategory.INSUFFICIENT_EVIDENCE.value,
                modality_weights=base_zero_weights,
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
                excluded_modalities=excluded_modalities,
                fusion_status="insufficient_evidence_unvalidated",
                is_validated=False,
                processing_latency_ms=round((time.perf_counter() - t0) * 1000.0, 2),
                is_definitive_claim=False,
            )

        # Case B/C/T: Single eligible modality fallback
        if len(eligible_modalities) == 1:
            sole_name = eligible_modalities[0]
            sole_obs = eligible_obs[sole_name]
            weights = {k: (1.0 if k == sole_name else 0.0) for k in obs_by_name}
            limitations.append(
                f"Single-modality fallback grounded strictly in validated {sole_name} evidence."
            )
            return FusionResult(
                session_id=session_id,
                timestamp=now,
                facial_observation=aligned_face,
                speech_observation=aligned_speech,
                text_observation=aligned_text,
                fused_probabilities=dict(sole_obs.emotion_probabilities),
                dominant_estimate=sole_obs.dominant_estimate,
                modality_weights=weights,
                confidence=sole_obs.confidence,
                uncertainty=sole_obs.uncertainty,
                conflicting_evidence=False,
                conflict_metric=0.0,
                missing_modalities=missing_modalities,
                quality_summary=quality_summary,
                limitations=limitations,
                contributing_model_states=contributing_states,
                classification_eligible_modalities=eligible_modalities,
                diagnostic_modalities=diagnostic_modalities,
                excluded_modalities=excluded_modalities,
                fusion_status=f"{sole_name}_only_validated",
                is_validated=True,
                processing_latency_ms=round((time.perf_counter() - t0) * 1000.0, 2),
                is_definitive_claim=False,
            )

        # Case D: Multi-modality (2 or 3 validated eligible streams) Bayesian log-opinion fusion
        weights = (
            self.weighter.compute_weights(aligned_face, aligned_speech)
            if not include_text and len(eligible_modalities) == 2
            else self.weighter.compute_n_weights(
                {k: (eligible_obs[k] if k in eligible_obs else None) for k in obs_by_name}
            )
        )

        # Conflict estimation across all eligible probability distributions
        jsd = self.divergence_calc.multi_stream_divergence(
            {k: v.emotion_probabilities for k, v in eligible_obs.items()}
        )
        is_conflicting = bool(jsd > self.config.conflict_threshold)
        if is_conflicting:
            limitations.append(
                f"Statistically divergent evidence across modalities (max JSD: {jsd:.2f} > {self.config.conflict_threshold})."
            )

        all_categories = sorted(
            {cat for obs in eligible_obs.values() for cat in obs.emotion_probabilities.keys()}
        )
        eps = 1e-6
        log_fused: dict[str, float] = {}
        for cat in all_categories:
            log_p = sum(
                weights.get(mod, 0.0) * np.log(max(eps, obs.emotion_probabilities.get(cat, eps)))
                for mod, obs in eligible_obs.items()
            )
            log_fused[cat] = float(log_p)

        log_vals = np.array(list(log_fused.values()), dtype=np.float64)
        exp_vals = np.exp(log_vals - np.max(log_vals))
        fused_probs_arr = exp_vals / np.sum(exp_vals)
        fused_probabilities: dict[str, float] = {
            cat: round(float(fused_probs_arr[i]), 4) for i, cat in enumerate(log_fused.keys())
        }

        dominant_cat = max(fused_probabilities.items(), key=lambda item: item[1])[0]
        max_fused_prob = float(fused_probabilities[dominant_cat])

        avg_quality = float(
            sum(obs.quality_score for obs in eligible_obs.values()) / len(eligible_obs)
        )
        conflict_attenuation = float(1.0 - 0.4 * jsd)
        # Prevent false over-confidence merely from agreeing correlated streams
        corr_cap = (
            self.config.correlated_agreement_dampening
            if not is_conflicting and len(eligible_obs) >= 2
            else 1.0
        )
        fused_confidence = float(
            np.clip(min(corr_cap, max_fused_prob) * avg_quality * conflict_attenuation, 0.0, 1.0)
        )

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

        if (
            fused_confidence < self.config.confidence_threshold
            or fused_uncertainty > self.config.uncertainty_threshold
        ):
            limitations.append(
                f"Abstention triggered: Fused confidence {fused_confidence:.2f} < {self.config.confidence_threshold} or uncertainty {fused_uncertainty:.2f} > {self.config.uncertainty_threshold}."
            )
            dominant_cat = EmotionCategory.INSUFFICIENT_EVIDENCE.value
            fused_confidence = 0.0
            fused_uncertainty = 1.0

        return FusionResult(
            session_id=session_id,
            timestamp=now,
            facial_observation=aligned_face,
            speech_observation=aligned_speech,
            text_observation=aligned_text,
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
            excluded_modalities=excluded_modalities,
            fusion_status="multimodal_fused",
            is_validated=True,
            processing_latency_ms=round((time.perf_counter() - t0) * 1000.0, 2),
            is_definitive_claim=False,
        )
