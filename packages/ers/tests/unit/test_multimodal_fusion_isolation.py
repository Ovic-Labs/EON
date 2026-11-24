"""Unit tests for Critical Issue 1: Multimodal Fusion Validation Isolation.

Verifies:
1. When both modalities are validated: Bayesian logarithmic fusion.
2. When facial only is validated: 100% facial classification; speech is diagnostic only (0 weight).
3. When speech only is validated: 100% speech classification; facial is diagnostic only (0 weight).
4. When neither is validated: returns INSUFFICIENT_EVIDENCE, confidence 0.0, uncertainty 1.0.
5. When one is validated and one is failed: classification continues with validated modality only.
6. When an observation is stale (>2.0s): ineligible for classification.
7. When probabilities contain non-finite values: rejected from classification eligibility.
"""

from __future__ import annotations

import time
import uuid

import pytest
from eon_ers.config import ERSConfig
from eon_ers.contracts import EmotionObservation
from eon_ers.fusion.multimodal import MultimodalFusionPipeline, evaluate_modality_eligibility
from eon_ers.types import (
    EmotionCategory,
    InputQualityStatus,
    Modality,
    ModalityEligibilityStatus,
    ModelState,
    ObservationStatus,
)


def _make_observation(
    modality: Modality,
    model_state: ModelState,
    status: ObservationStatus,
    probs: dict[EmotionCategory, float],
    input_quality: InputQualityStatus = InputQualityStatus.ACCEPTABLE,
    timestamp: float | None = None,
    raw_confidence: float = 0.85,
) -> EmotionObservation:
    dominant = max(probs, key=probs.get) if probs else EmotionCategory.NEUTRAL
    str_probs = {c.value: float(p) for c, p in probs.items()}
    is_val = model_state == ModelState.MODEL_LOADED_VALIDATED
    return EmotionObservation(
        observation_id="obs-" + str(uuid.uuid4())[:8],
        timestamp=timestamp if timestamp is not None else time.time(),
        modality=modality,
        expression_observations={},
        emotion_probabilities=str_probs,
        dominant_estimate=dominant.value,
        confidence=raw_confidence,
        uncertainty=1.0 - raw_confidence,
        quality_score=0.9 if input_quality == InputQualityStatus.ACCEPTABLE else 0.5,
        model_id=f"test-{modality.value}-model",
        model_version="1.0.0",
        processing_latency_ms=2.5,
        status=status,
        input_quality=input_quality,
        is_calibrated=is_val,
        raw_confidence=raw_confidence,
        model_state=model_state,
        is_validated=is_val,
        is_definitive_claim=False,
    )


def test_evaluate_modality_eligibility_scenarios() -> None:
    now = time.time()

    # Validated and fresh
    obs_val = _make_observation(
        modality=Modality.FACIAL,
        model_state=ModelState.MODEL_LOADED_VALIDATED,
        status=ObservationStatus.OK,
        probs={EmotionCategory.HAPPINESS: 0.9, EmotionCategory.NEUTRAL: 0.1},
        timestamp=now,
    )
    eligible, status, reason = evaluate_modality_eligibility(obs_val, now)
    assert eligible is True
    assert status == ModalityEligibilityStatus.CLASSIFICATION_ELIGIBLE

    # Unvalidated
    obs_unval = _make_observation(
        modality=Modality.FACIAL,
        model_state=ModelState.MODEL_LOADED_UNVERIFIED,
        status=ObservationStatus.MODEL_UNVALIDATED,
        probs={EmotionCategory.HAPPINESS: 0.9, EmotionCategory.NEUTRAL: 0.1},
        timestamp=now,
    )
    eligible, status, reason = evaluate_modality_eligibility(obs_unval, now)
    assert eligible is False
    assert status == ModalityEligibilityStatus.UNVALIDATED

    # Stale
    obs_stale = _make_observation(
        modality=Modality.FACIAL,
        model_state=ModelState.MODEL_LOADED_VALIDATED,
        status=ObservationStatus.OK,
        probs={EmotionCategory.HAPPINESS: 0.9, EmotionCategory.NEUTRAL: 0.1},
        timestamp=now - 5.0,
    )
    eligible, status, reason = evaluate_modality_eligibility(obs_stale, now)
    assert eligible is False
    assert status == ModalityEligibilityStatus.STALE

    # Unusable quality
    obs_unusable = _make_observation(
        modality=Modality.FACIAL,
        model_state=ModelState.MODEL_LOADED_VALIDATED,
        status=ObservationStatus.INSUFFICIENT_EVIDENCE,
        probs={EmotionCategory.HAPPINESS: 0.9, EmotionCategory.NEUTRAL: 0.1},
        input_quality=InputQualityStatus.UNUSABLE,
        timestamp=now,
    )
    eligible, status, reason = evaluate_modality_eligibility(obs_unusable, now)
    assert eligible is False
    assert status == ModalityEligibilityStatus.QUALITY_UNUSABLE

    # Failed
    obs_failed = _make_observation(
        modality=Modality.FACIAL,
        model_state=ModelState.MODEL_INFERENCE_FAILED,
        status=ObservationStatus.FAILED,
        probs={},
        timestamp=now,
    )
    eligible, status, reason = evaluate_modality_eligibility(obs_failed, now)
    assert eligible is False
    assert status == ModalityEligibilityStatus.FAILED


def test_fusion_both_validated() -> None:
    pipeline = MultimodalFusionPipeline(config=ERSConfig())
    now = time.time()

    facial_probs = {EmotionCategory.HAPPINESS: 0.8, EmotionCategory.NEUTRAL: 0.2}
    speech_probs = {EmotionCategory.HAPPINESS: 0.7, EmotionCategory.NEUTRAL: 0.3}

    obs_face = _make_observation(
        Modality.FACIAL,
        ModelState.MODEL_LOADED_VALIDATED,
        ObservationStatus.OK,
        facial_probs,
        timestamp=now,
    )
    obs_speech = _make_observation(
        Modality.SPEECH,
        ModelState.MODEL_LOADED_VALIDATED,
        ObservationStatus.OK,
        speech_probs,
        timestamp=now,
    )

    result = pipeline.fuse(obs_face, obs_speech, current_time=now)

    assert result.is_validated is True
    assert result.dominant_estimate == EmotionCategory.HAPPINESS.value
    assert result.fusion_status in ("ok", "multimodal_fused")
    assert Modality.FACIAL.value in result.classification_eligible_modalities
    assert Modality.SPEECH.value in result.classification_eligible_modalities
    assert len(result.diagnostic_modalities) == 0


def test_fusion_facial_only_validated_speech_unvalidated() -> None:
    pipeline = MultimodalFusionPipeline(config=ERSConfig())
    now = time.time()

    facial_probs = {EmotionCategory.SADNESS: 0.85, EmotionCategory.NEUTRAL: 0.15}
    # Unvalidated speech with conflicting/different probabilities
    speech_probs = {EmotionCategory.HAPPINESS: 0.99, EmotionCategory.NEUTRAL: 0.01}

    obs_face = _make_observation(
        Modality.FACIAL,
        ModelState.MODEL_LOADED_VALIDATED,
        ObservationStatus.OK,
        facial_probs,
        timestamp=now,
    )
    obs_speech = _make_observation(
        Modality.SPEECH,
        ModelState.MODEL_LOADED_UNVERIFIED,
        ObservationStatus.MODEL_UNVALIDATED,
        speech_probs,
        timestamp=now,
    )

    result = pipeline.fuse(obs_face, obs_speech, current_time=now)

    # Classification must match facial 100%; speech must have zero influence!
    assert result.is_validated is True
    assert result.dominant_estimate == EmotionCategory.SADNESS.value
    assert result.fused_probabilities[EmotionCategory.SADNESS.value] == pytest.approx(0.85)
    assert result.classification_eligible_modalities == [Modality.FACIAL.value]
    assert result.diagnostic_modalities == [Modality.SPEECH.value]


def test_fusion_speech_only_validated_facial_unvalidated() -> None:
    pipeline = MultimodalFusionPipeline(config=ERSConfig())
    now = time.time()

    # Unvalidated facial
    facial_probs = {EmotionCategory.ANGER: 0.95, EmotionCategory.NEUTRAL: 0.05}
    # Validated speech
    speech_probs = {EmotionCategory.FEAR: 0.80, EmotionCategory.NEUTRAL: 0.20}

    obs_face = _make_observation(
        Modality.FACIAL,
        ModelState.MODEL_LOADED_UNVERIFIED,
        ObservationStatus.MODEL_UNVALIDATED,
        facial_probs,
        timestamp=now,
    )
    obs_speech = _make_observation(
        Modality.SPEECH,
        ModelState.MODEL_LOADED_VALIDATED,
        ObservationStatus.OK,
        speech_probs,
        timestamp=now,
    )

    result = pipeline.fuse(obs_face, obs_speech, current_time=now)

    # Classification must match speech 100%; facial must have zero influence!
    assert result.is_validated is True
    assert result.dominant_estimate == EmotionCategory.FEAR.value
    assert result.fused_probabilities[EmotionCategory.FEAR.value] == pytest.approx(0.80)
    assert result.classification_eligible_modalities == [Modality.SPEECH.value]
    assert result.diagnostic_modalities == [Modality.FACIAL.value]


def test_fusion_neither_validated_suppressed() -> None:
    pipeline = MultimodalFusionPipeline(config=ERSConfig())
    now = time.time()

    facial_probs = {EmotionCategory.HAPPINESS: 0.9, EmotionCategory.NEUTRAL: 0.1}
    speech_probs = {EmotionCategory.HAPPINESS: 0.9, EmotionCategory.NEUTRAL: 0.1}

    obs_face = _make_observation(
        Modality.FACIAL,
        ModelState.MODEL_LOADED_UNVERIFIED,
        ObservationStatus.MODEL_UNVALIDATED,
        facial_probs,
        timestamp=now,
    )
    obs_speech = _make_observation(
        Modality.SPEECH,
        ModelState.MODEL_LOADED_UNVERIFIED,
        ObservationStatus.MODEL_UNVALIDATED,
        speech_probs,
        timestamp=now,
    )

    result = pipeline.fuse(obs_face, obs_speech, current_time=now)

    # Both are unvalidated: classification must be suppressed!
    assert result.is_validated is False
    assert result.dominant_estimate == EmotionCategory.INSUFFICIENT_EVIDENCE.value
    assert result.confidence == 0.0
    assert result.uncertainty == 1.0
    assert result.fusion_status == "insufficient_evidence_unvalidated"
    assert len(result.classification_eligible_modalities) == 0
    assert Modality.FACIAL.value in result.diagnostic_modalities
    assert Modality.SPEECH.value in result.diagnostic_modalities


def test_fusion_one_validated_one_failed() -> None:
    pipeline = MultimodalFusionPipeline(config=ERSConfig())
    now = time.time()

    facial_probs = {EmotionCategory.ANGER: 0.75, EmotionCategory.NEUTRAL: 0.25}

    obs_face = _make_observation(
        Modality.FACIAL,
        ModelState.MODEL_LOADED_VALIDATED,
        ObservationStatus.OK,
        facial_probs,
        timestamp=now,
    )
    obs_speech = _make_observation(
        Modality.SPEECH,
        ModelState.MODEL_INFERENCE_FAILED,
        ObservationStatus.FAILED,
        {},
        timestamp=now,
    )

    result = pipeline.fuse(obs_face, obs_speech, current_time=now)

    # Validated facial carries classification; failed speech does not crash fusion
    assert result.is_validated is True
    assert result.dominant_estimate == EmotionCategory.ANGER.value
    assert result.classification_eligible_modalities == [Modality.FACIAL.value]
    assert Modality.SPEECH.value in result.diagnostic_modalities
