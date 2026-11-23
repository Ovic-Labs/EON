"""Unit tests for emotion estimate schemas and ethical guardrails."""

import pytest
from pydantic import ValidationError

from eon.schemas.emotions import (
    DiscreteEmotionScore,
    EmotionEstimatePayload,
    PrimaryEmotionCategory,
)
from eon.schemas.identifiers import generate_event_id


def test_valid_emotion_estimate() -> None:
    """AC-1.2-07: Verify valid emotion estimate construction."""
    obs_id = generate_event_id()
    payload = EmotionEstimatePayload(
        source_observation_ids=[obs_id],
        valence=0.65,
        arousal=0.40,
        dominance=0.10,
        primary_category=PrimaryEmotionCategory.JOY,
        confidence=0.85,
        uncertainty=0.15,
        discrete_scores=[
            DiscreteEmotionScore(category=PrimaryEmotionCategory.JOY, probability=0.85),
            DiscreteEmotionScore(category=PrimaryEmotionCategory.ENGAGED, probability=0.70),
        ],
        model_metadata={"model": "affect_fusion_v1", "calibration": "balanced"},
    )
    assert payload.valence == 0.65
    assert payload.arousal == 0.40
    assert payload.dominance == 0.10
    assert payload.primary_category == PrimaryEmotionCategory.JOY
    assert "Automated affective estimation" in payload.disclaimer


def test_emotion_numerical_bounds_enforced() -> None:
    """AC-1.2-07: Verify valence and arousal bounds in [-1.0, 1.0]."""
    obs_id = generate_event_id()

    # Valence out of bounds
    with pytest.raises(ValidationError):
        EmotionEstimatePayload(
            source_observation_ids=[obs_id],
            valence=1.05,
            arousal=0.0,
            primary_category=PrimaryEmotionCategory.NEUTRAL,
            confidence=0.5,
            uncertainty=0.5,
        )

    with pytest.raises(ValidationError):
        EmotionEstimatePayload(
            source_observation_ids=[obs_id],
            valence=-1.5,
            arousal=0.0,
            primary_category=PrimaryEmotionCategory.NEUTRAL,
            confidence=0.5,
            uncertainty=0.5,
        )

    # Arousal out of bounds
    with pytest.raises(ValidationError):
        EmotionEstimatePayload(
            source_observation_ids=[obs_id],
            valence=0.0,
            arousal=2.0,
            primary_category=PrimaryEmotionCategory.NEUTRAL,
            confidence=0.5,
            uncertainty=0.5,
        )


def test_empty_source_observations_rejected() -> None:
    """AC-1.2-07: Verify traceability requires at least one source observation."""
    with pytest.raises(ValidationError):
        EmotionEstimatePayload(
            source_observation_ids=[],  # Empty list violates min_length=1
            valence=0.0,
            arousal=0.0,
            primary_category=PrimaryEmotionCategory.NEUTRAL,
            confidence=0.5,
            uncertainty=0.5,
        )


def test_ethical_disclaimer_cannot_be_cleared() -> None:
    """AC-1.2-07: Verify ethical disclaimer cannot be cleared or set to empty string."""
    obs_id = generate_event_id()
    with pytest.raises(ValidationError):
        EmotionEstimatePayload(
            source_observation_ids=[obs_id],
            valence=0.0,
            arousal=0.0,
            primary_category=PrimaryEmotionCategory.NEUTRAL,
            confidence=0.5,
            uncertainty=0.5,
            disclaimer="   ",  # Invalid empty disclaimer
        )
