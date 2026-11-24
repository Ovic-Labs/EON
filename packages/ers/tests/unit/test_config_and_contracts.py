"""Unit tests for ERS configuration, contracts, and lifecycle."""

import pytest
from eon_ers.config import ERSConfig
from eon_ers.contracts import EmotionObservation, ERSInput, FusionResult
from eon_ers.exceptions import ERSLifecycleError
from eon_ers.lifecycle import EngineLifecycleManager
from eon_ers.types import (
    DeviceType,
    EngineState,
    Modality,
    ObservationStatus,
)
from pydantic import ValidationError


def test_config_defaults() -> None:
    config = ERSConfig()
    assert config.device == DeviceType.CPU
    assert config.num_threads == 4
    assert config.enable_facial is True
    assert config.enable_speech is True
    assert config.enable_multimodal_fusion is True
    assert config.confidence_threshold == 0.35
    assert config.uncertainty_threshold == 0.65


def test_config_validation_extra_fields_forbidden() -> None:
    with pytest.raises(ValidationError):
        ERSConfig(invalid_unknown_parameter=True)  # type: ignore


def test_ers_input_contract_and_scrub() -> None:
    inp = ERSInput(
        session_id="session-test-01",
        modality=Modality.FACIAL,
        consent_reference="valid-token",
        image_payload=b"fake-bytes",
        audio_payload=b"fake-audio",
    )
    assert inp.image_payload == b"fake-bytes"
    inp.scrub_media_payload()
    assert inp.image_payload is None
    assert inp.audio_payload is None


def test_emotion_observation_is_definitive_claim_invariant() -> None:
    obs = EmotionObservation(
        observation_id="obs-01",
        timestamp=100.0,
        modality=Modality.FACIAL,
        expression_observations={"AU12": 0.5},
        emotion_probabilities={"neutral": 0.8, "happiness": 0.2},
        dominant_estimate="neutral",
        confidence=0.8,
        uncertainty=0.2,
        quality_score=0.9,
        model_id="test-model",
        model_version="1.0",
        processing_latency_ms=5.0,
        limitations=[],
        status=ObservationStatus.OK,
        is_definitive_claim=False,
    )
    assert obs.is_definitive_claim is False

    # Attempting to set is_definitive_claim to True must raise ValidationError
    with pytest.raises(ValidationError):
        EmotionObservation(
            observation_id="obs-02",
            timestamp=100.0,
            modality=Modality.FACIAL,
            expression_observations={},
            emotion_probabilities={"neutral": 1.0},
            dominant_estimate="neutral",
            confidence=0.8,
            uncertainty=0.2,
            quality_score=0.9,
            model_id="test",
            model_version="1.0",
            processing_latency_ms=5.0,
            limitations=[],
            status=ObservationStatus.OK,
            is_definitive_claim=True,  # Forbidden!
        )


def test_fusion_result_contract() -> None:
    fr = FusionResult(
        result_id="fuse-01",
        timestamp=100.0,
        facial_observation=None,
        speech_observation=None,
        fused_probabilities={"neutral": 1.0},
        dominant_estimate="neutral",
        modality_weights={"facial": 0.5, "speech": 0.5},
        confidence=0.5,
        uncertainty=0.5,
        conflicting_evidence=False,
        conflict_metric=0.0,
        missing_modalities=[],
        quality_summary={},
        limitations=[],
        is_definitive_claim=False,
    )
    assert fr.is_definitive_claim is False

    with pytest.raises(ValidationError):
        FusionResult(
            result_id="fuse-02",
            timestamp=100.0,
            facial_observation=None,
            speech_observation=None,
            fused_probabilities={"neutral": 1.0},
            dominant_estimate="neutral",
            modality_weights={"facial": 0.5, "speech": 0.5},
            confidence=0.5,
            uncertainty=0.5,
            conflicting_evidence=False,
            conflict_metric=0.0,
            missing_modalities=[],
            quality_summary={},
            limitations=[],
            is_definitive_claim=True,  # Forbidden!
        )


@pytest.mark.asyncio
async def test_lifecycle_manager_transitions() -> None:
    mgr = EngineLifecycleManager("test.engine")
    assert mgr.state == EngineState.UNINITIALIZED
    assert not mgr.is_running

    await mgr.transition_to(EngineState.INITIALIZING, "start init")
    assert mgr.state == EngineState.INITIALIZING

    await mgr.transition_to(EngineState.INITIALIZED, "init done")
    assert mgr.state == EngineState.INITIALIZED

    await mgr.transition_to(EngineState.STARTING, "starting")
    await mgr.transition_to(EngineState.RUNNING, "running")
    assert mgr.is_running

    await mgr.transition_to(EngineState.PAUSED, "paused")
    assert not mgr.is_running

    await mgr.transition_to(EngineState.RUNNING, "resumed")
    assert mgr.is_running

    await mgr.transition_to(EngineState.STOPPING, "stopping")
    await mgr.transition_to(EngineState.STOPPED, "stopped")
    assert mgr.state == EngineState.STOPPED


@pytest.mark.asyncio
async def test_illegal_lifecycle_transition_raises() -> None:
    mgr = EngineLifecycleManager("test.engine")
    with pytest.raises(ERSLifecycleError):
        await mgr.transition_to(EngineState.RUNNING, "illegal skip")
