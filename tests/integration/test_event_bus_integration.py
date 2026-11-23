"""Integration tests for end-to-end multi-engine event bus workflows."""

import asyncio

import pytest

from eon.core.delivery import DeliveryState
from eon.core.event_bus import EventBus
from eon.core.priority import EventPriority
from eon.schemas.common import ModalityType, Provenance
from eon.schemas.emotions import (
    DiscreteEmotionScore,
    EmotionEstimatePayload,
    PrimaryEmotionCategory,
)
from eon.schemas.events import EventEnvelope, EventType
from eon.schemas.observations import (
    ObservationPayload,
    TextObservationData,
)


@pytest.mark.asyncio
async def test_end_to_end_perception_to_emotion_workflow() -> None:
    """AC-1.3-05 / AC-1.3-06: End-to-end perception -> emotion pipeline test."""
    async with EventBus() as bus:
        processed_observations: list[str] = []
        derived_emotions: list[str] = []

        # Subscriber 1: ERS Perceptual Ingest
        async def ers_ingest_handler(event: EventEnvelope[ObservationPayload]) -> None:
            processed_observations.append(event.source)
            # Emit derived emotion estimate event into the bus
            emo_payload = EmotionEstimatePayload(
                source_observation_ids=[str(event.payload.observation_id)],
                valence=0.6,
                arousal=0.3,
                dominance=0.1,
                primary_category=PrimaryEmotionCategory.JOY,
                confidence=0.85,
                uncertainty=0.15,
                discrete_scores=[
                    DiscreteEmotionScore(category=PrimaryEmotionCategory.JOY, probability=0.7),
                    DiscreteEmotionScore(category=PrimaryEmotionCategory.NEUTRAL, probability=0.3),
                ],
            )
            emo_event = EventEnvelope(
                event_type=EventType.EMOTION_ESTIMATE,
                source="engine.ers",
                payload=emo_payload,
            )
            await bus.publish(emo_event, priority=EventPriority.HIGH)

        # Subscriber 2: EMS Affective State Tracker
        async def ems_tracker_handler(event: EventEnvelope[EmotionEstimatePayload]) -> None:
            derived_emotions.append(event.source)

        await bus.subscribe_async(EventType.OBSERVATION, ers_ingest_handler)
        await bus.subscribe_async(EventType.EMOTION_ESTIMATE, ems_tracker_handler)

        # Publish initial perceptual observation
        prov = Provenance(
            source_id="sensor.mic.01",
            engine_version="0.1.0",
            capture_device="usb_mic",
        )
        obs_payload = ObservationPayload(
            source_id="sensor.mic.01",
            modality=ModalityType.TEXT,
            confidence=0.9,
            provenance=prov,
            data=TextObservationData(text="I am very happy today"),
        )
        obs_event = EventEnvelope(
            event_type=EventType.OBSERVATION,
            source="sensor.mic.01",
            payload=obs_payload,
        )

        outcomes = await bus.publish_and_wait(obs_event)
        assert len(outcomes) == 1
        assert outcomes[0].state == DeliveryState.QUEUED

        # Allow secondary derived emotion event to be dispatched
        await asyncio.sleep(0.05)

        assert processed_observations == ["sensor.mic.01"]
        assert derived_emotions == ["engine.ers"]

        # Check telemetry
        metrics = bus.get_metrics()
        assert metrics.total_published == 2
        assert metrics.delivered_events == 2
