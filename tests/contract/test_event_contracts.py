"""Contract tests validating end-to-end event chains and causality preservation."""

from eon.schemas.common import ModalityType, Provenance
from eon.schemas.context import InteractionContextPayload, InteractionStage
from eon.schemas.emotions import (
    DiscreteEmotionScore,
    EmotionEstimatePayload,
    PrimaryEmotionCategory,
)
from eon.schemas.events import (
    ContextUpdateEvent,
    EmotionEstimateEvent,
    EventMetadata,
    EventType,
    ObservationEvent,
    SafetyAdvisoryEvent,
)
from eon.schemas.identifiers import (
    generate_correlation_id,
    generate_session_id,
)
from eon.schemas.observations import (
    ObservationPayload,
    VisualObservationData,
)
from eon.schemas.safety import (
    SafetyAdvisoryLevel,
    SafetyAdvisoryPayload,
)
from eon.schemas.serialization import deserialize_event, serialize_to_json


def test_end_to_end_causality_chain_contract() -> None:
    """AC-1.2-04, AC-1.2-05: Contract verifying multi-engine causal event tracking."""
    session_id = generate_session_id()
    correlation_id = generate_correlation_id()

    # Step 1: Perceptual observation event from sensor ingest
    obs_payload = ObservationPayload(
        source_id="sensor.camera.rgb",
        modality=ModalityType.VISUAL,
        confidence=0.94,
        provenance=Provenance(source_id="sensor.camera.rgb", capture_device="realsense"),
        data=VisualObservationData(
            face_detected=True,
            face_bounding_box=(0.1, 0.1, 0.4, 0.5),
            head_pose_yaw=5.0,
            head_pose_pitch=2.0,
            facial_action_units={"AU12": 0.9, "AU06": 0.8},
        ),
    )
    obs_event = ObservationEvent(
        event_type=EventType.OBSERVATION,
        source="sensor.camera.rgb",
        metadata=EventMetadata(
            correlation_id=correlation_id,
            session_id=session_id,
        ),
        payload=obs_payload,
    )

    # Step 2: ERS consumes observation and publishes EmotionEstimateEvent
    ers_payload = EmotionEstimatePayload(
        source_observation_ids=[obs_event.event_id],
        valence=0.82,
        arousal=0.55,
        primary_category=PrimaryEmotionCategory.JOY,
        confidence=0.91,
        uncertainty=0.09,
        discrete_scores=[
            DiscreteEmotionScore(category=PrimaryEmotionCategory.JOY, probability=0.82),
            DiscreteEmotionScore(category=PrimaryEmotionCategory.ENGAGED, probability=0.75),
        ],
    )
    ers_event = EmotionEstimateEvent(
        event_type=EventType.EMOTION_ESTIMATE,
        source="eon.ers",
        metadata=EventMetadata(
            correlation_id=correlation_id,
            causation_id=obs_event.event_id,
            session_id=session_id,
        ),
        payload=ers_payload,
    )

    # Step 3: Context Manager updates interaction context
    ctx_payload = InteractionContextPayload(
        session_id=session_id,
        interaction_stage=InteractionStage.ACTIVE_DIALOGUE,
    )
    ctx_event = ContextUpdateEvent(
        event_type=EventType.CONTEXT_UPDATE,
        source="eon.core.context",
        metadata=EventMetadata(
            correlation_id=correlation_id,
            causation_id=ers_event.event_id,
            session_id=session_id,
        ),
        payload=ctx_payload,
    )

    # Step 4: Social Intelligence Engine assesses safety boundary and issues advisory
    adv_payload = SafetyAdvisoryPayload(
        level=SafetyAdvisoryLevel.INFO,
        advisory_code="ADV_ENGAGEMENT_OPTIMAL",
        human_readable_message="User positive engagement confirmed.",
        reason="Consistent joyful expression across social turns.",
        recommended_action="Maintain receptive conversational persona.",
    )
    adv_event = SafetyAdvisoryEvent(
        event_type=EventType.SAFETY_ADVISORY,
        source="eon.sie",
        metadata=EventMetadata(
            correlation_id=correlation_id,
            causation_id=ctx_event.event_id,
            session_id=session_id,
        ),
        payload=adv_payload,
    )

    # Validate causality linkages
    assert ers_event.metadata.causation_id == obs_event.event_id
    assert ctx_event.metadata.causation_id == ers_event.event_id
    assert adv_event.metadata.causation_id == ctx_event.event_id

    # Validate correlation preservation across all 4 events
    for ev in [obs_event, ers_event, ctx_event, adv_event]:
        assert ev.metadata.correlation_id == correlation_id
        assert ev.metadata.session_id == session_id

    # Verify serialization and deserialization of the entire chain
    for original_event in [obs_event, ers_event, ctx_event, adv_event]:
        serialized = serialize_to_json(original_event)
        recovered = deserialize_event(serialized)
        assert recovered.event_id == original_event.event_id
        assert recovered.metadata.causation_id == original_event.metadata.causation_id
        assert recovered.metadata.correlation_id == original_event.metadata.correlation_id
