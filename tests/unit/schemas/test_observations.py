"""Unit tests for structured perceptual observation contracts."""

import datetime

import pytest
from pydantic import ValidationError

from eon.schemas.common import ModalityType, Provenance
from eon.schemas.observations import (
    AudioObservationData,
    BehaviourObservationData,
    EnvironmentalObservationData,
    ObservationPayload,
    TextObservationData,
    VisualObservationData,
)
from eon.schemas.timestamps import utc_now


@pytest.fixture
def sample_provenance() -> Provenance:
    return Provenance(
        source_id="sensor.camera.rgb",
        engine_version="0.1.0",
        capture_device="realsense_d435",
    )


def test_visual_observation_valid(sample_provenance: Provenance) -> None:
    """AC-1.2-06: Verify valid visual observation construction."""
    data = VisualObservationData(
        face_detected=True,
        face_bounding_box=(0.1, 0.2, 0.5, 0.6),
        head_pose_yaw=15.0,
        head_pose_pitch=-5.0,
        facial_action_units={"AU01": 0.8, "AU04": 0.2},
    )
    obs = ObservationPayload(
        source_id="sensor.camera.rgb",
        modality=ModalityType.VISUAL,
        confidence=0.92,
        provenance=sample_provenance,
        data=data,
    )
    assert obs.modality == ModalityType.VISUAL
    assert obs.confidence == 0.92
    assert obs.data.face_detected is True  # type: ignore[union-attr]


def test_audio_observation_valid(sample_provenance: Provenance) -> None:
    """AC-1.2-06: Verify valid audio observation construction."""
    data = AudioObservationData(
        speech_detected=True,
        snr_db=18.5,
        pitch_hz=180.0,
        energy=0.72,
        duration_seconds=2.5,
    )
    obs = ObservationPayload(
        source_id="sensor.mic.array",
        modality=ModalityType.AUDIO,
        confidence=0.88,
        provenance=sample_provenance,
        data=data,
    )
    assert obs.modality == ModalityType.AUDIO
    assert obs.data.pitch_hz == 180.0  # type: ignore[union-attr]


def test_text_and_behaviour_observations(sample_provenance: Provenance) -> None:
    """Verify text, behavioural, and environmental observations."""
    text_data = TextObservationData(
        text="Hello robot, how are you today?",
        language="en",
        sentiment_hint=0.6,
    )
    obs_text = ObservationPayload(
        source_id="engine.asr",
        modality=ModalityType.TEXT,
        confidence=0.95,
        provenance=sample_provenance,
        data=text_data,
    )
    assert obs_text.data.text.startswith("Hello")  # type: ignore[union-attr]

    beh_data = BehaviourObservationData(
        action_label="waving_hand",
        movement_intensity=0.85,
        gaze_direction="direct",
        proximity_zone="social",
    )
    obs_beh = ObservationPayload(
        source_id="eon.hbu",
        modality=ModalityType.BEHAVIOURAL,
        confidence=0.89,
        provenance=sample_provenance,
        data=beh_data,
    )
    assert obs_beh.data.action_label == "waving_hand"  # type: ignore[union-attr]

    env_data = EnvironmentalObservationData(
        ambient_noise_db=45.0,
        ambient_lux=350.0,
        temperature_celsius=21.5,
        occupancy_count=2,
    )
    obs_env = ObservationPayload(
        source_id="sensor.env",
        modality=ModalityType.ENVIRONMENTAL,
        confidence=0.99,
        provenance=sample_provenance,
        data=env_data,
    )
    assert obs_env.data.ambient_lux == 350.0  # type: ignore[union-attr]


def test_observation_staleness_calculation(sample_provenance: Provenance) -> None:
    """AC-1.2-06: Verify is_stale detection based on max age and expires_at."""
    now = utc_now()
    past_time = now - datetime.timedelta(seconds=10)

    obs = ObservationPayload(
        source_id="sensor.camera",
        observed_at=past_time,
        modality=ModalityType.VISUAL,
        confidence=0.9,
        provenance=sample_provenance,
        data=VisualObservationData(face_detected=False),
    )
    # Older than 5 seconds should report as stale
    assert obs.is_stale(current_time=now, max_age_seconds=5.0) is True
    # Younger than 15 seconds should report not stale
    assert obs.is_stale(current_time=now, max_age_seconds=15.0) is False

    # Test explicit expires_at
    future_expire = now + datetime.timedelta(seconds=20)
    obs_exp = ObservationPayload(
        source_id="sensor.camera",
        observed_at=now,
        expires_at=future_expire,
        modality=ModalityType.VISUAL,
        confidence=0.9,
        provenance=sample_provenance,
        data=VisualObservationData(face_detected=False),
    )
    assert obs_exp.is_stale(current_time=now) is False
    assert obs_exp.is_stale(current_time=future_expire + datetime.timedelta(seconds=1)) is True


def test_invalid_expires_at_before_observed(sample_provenance: Provenance) -> None:
    """Verify error raised when expires_at is set before observed_at."""
    now = utc_now()
    with pytest.raises(ValidationError):
        ObservationPayload(
            source_id="sensor.camera",
            observed_at=now,
            expires_at=now - datetime.timedelta(seconds=5),
            modality=ModalityType.VISUAL,
            confidence=0.9,
            provenance=sample_provenance,
            data=VisualObservationData(face_detected=False),
        )
