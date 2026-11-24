"""Unit tests for feature extraction and multimodal fusion mathematics."""

from eon_ers.contracts import EmotionObservation
from eon_ers.fusion.confidence import DivergenceCalculator
from eon_ers.fusion.weighting import ReliabilityWeighter
from eon_ers.temporal.smoothing import TemporalSmoother
from eon_ers.temporal.tracking import SessionObservationTracker
from eon_ers.types import Modality, ObservationStatus


def test_jensen_shannon_divergence_identical() -> None:
    p = {"neutral": 0.8, "happiness": 0.2}
    q = {"neutral": 0.8, "happiness": 0.2}
    jsd = DivergenceCalculator.jensen_shannon_divergence(p, q)
    assert jsd < 1e-6


def test_jensen_shannon_divergence_orthogonal() -> None:
    p = {"neutral": 1.0, "happiness": 0.0}
    q = {"neutral": 0.0, "happiness": 1.0}
    jsd = DivergenceCalculator.jensen_shannon_divergence(p, q)
    # Orthogonal distributions have maximum divergence 1.0
    assert abs(jsd - 1.0) < 0.05


def test_reliability_weighting() -> None:
    weighter = ReliabilityWeighter()

    # Create dummy observations
    face_obs = EmotionObservation(
        observation_id="f1",
        timestamp=10.0,
        modality=Modality.FACIAL,
        expression_observations={},
        emotion_probabilities={"neutral": 0.7, "happiness": 0.3},
        dominant_estimate="neutral",
        confidence=0.8,
        uncertainty=0.1,  # Highly certain
        quality_score=0.9,  # High quality
        model_id="m",
        model_version="1",
        processing_latency_ms=1.0,
        limitations=[],
        status=ObservationStatus.OK,
        is_definitive_claim=False,
    )

    speech_obs = EmotionObservation(
        observation_id="s1",
        timestamp=10.1,
        modality=Modality.SPEECH,
        expression_observations={},
        emotion_probabilities={"neutral": 0.7, "happiness": 0.3},
        dominant_estimate="neutral",
        confidence=0.3,
        uncertainty=0.7,  # Very uncertain
        quality_score=0.4,  # Degraded quality
        model_id="m",
        model_version="1",
        processing_latency_ms=1.0,
        limitations=[],
        status=ObservationStatus.DEGRADED,
        is_definitive_claim=False,
    )

    weights = weighter.compute_weights(face_obs, speech_obs)
    # Facial weight should dominate due to higher quality and lower uncertainty
    assert weights[Modality.FACIAL.value] > weights[Modality.SPEECH.value]
    assert abs(sum(weights.values()) - 1.0) < 0.01


def test_temporal_smoother() -> None:
    smoother = TemporalSmoother(alpha=0.3, half_life_seconds=2.0)
    p0 = {"neutral": 0.9, "happiness": 0.1}
    s0 = smoother.update(p0, timestamp=1.0)
    assert s0["neutral"] == 0.9

    # Next observation 0.2s later with sudden change
    p1 = {"neutral": 0.1, "happiness": 0.9}
    s1 = smoother.update(p1, timestamp=1.2)
    # Smoothed state should damp sudden change
    assert s1["neutral"] > 0.5
    assert s1["happiness"] < 0.5

    # Gap of 15 seconds (much larger than half-life) should reset to current
    p2 = {"anger": 1.0, "neutral": 0.0}
    s2 = smoother.update(p2, timestamp=16.2)
    assert s2["anger"] > 0.9


def test_session_tracker_isolation() -> None:
    tracker = SessionObservationTracker(max_buffer_size=10)
    obs_a = EmotionObservation(
        observation_id="a1",
        timestamp=1.0,
        modality=Modality.FACIAL,
        expression_observations={},
        emotion_probabilities={"happiness": 1.0},
        dominant_estimate="happiness",
        confidence=0.9,
        uncertainty=0.1,
        quality_score=1.0,
        model_id="m",
        model_version="1",
        processing_latency_ms=1.0,
        limitations=[],
        status=ObservationStatus.OK,
        is_definitive_claim=False,
    )

    tracker.record_observation("session-A", obs_a)
    assert len(tracker.get_recent_observations("session-A")) == 1
    assert len(tracker.get_recent_observations("session-B")) == 0

    # Resetting session A leaves session B untouched
    tracker.reset_session("session-A")
    assert len(tracker.get_recent_observations("session-A")) == 0
