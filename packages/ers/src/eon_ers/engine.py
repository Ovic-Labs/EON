"""Master Emotion Recognition System (ERS) engine.

Orchestrates facial, speech, and multimodal affective perception pipelines
conforming to OVIC EON responsible AI principles.
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

from eon_ers.config import ERSConfig
from eon_ers.contracts import EmotionObservation, ERSInput, FusionResult
from eon_ers.core.adapter import (
    TOPIC_FUSION_COMPLETED,
    TOPIC_INPUT_RECEIVED,
    TOPIC_OBSERVATION_CREATED,
    CoreEventBusAdapter,
)
from eon_ers.exceptions import ERSLifecycleError
from eon_ers.facial.pipeline import FacialPipeline
from eon_ers.fusion.multimodal import MultimodalFusionPipeline
from eon_ers.lifecycle import EngineLifecycleManager
from eon_ers.metrics.performance import PerformanceTracker
from eon_ers.privacy.consent import ConsentManager
from eon_ers.privacy.retention import MediaRetentionGuard
from eon_ers.speech.pipeline import SpeechPipeline
from eon_ers.temporal.tracking import SessionObservationTracker
from eon_ers.types import EmotionCategory, EngineState, Modality, ObservationStatus

logger = logging.getLogger("eon.ers.engine")


class ERSEngine:
    """Master asynchronous Emotion Recognition System engine."""

    def __init__(self, config: ERSConfig | None = None) -> None:
        self.config = config or ERSConfig()
        self.lifecycle = EngineLifecycleManager(engine_name="eon.ers")
        self.event_bus = CoreEventBusAdapter(external_bus=self.config.event_bus)
        self.consent_mgr = ConsentManager(enforce_consent=self.config.require_explicit_consent)
        self.retention_guard = MediaRetentionGuard(
            zero_disk_retention=self.config.zero_disk_retention
        )
        self.tracker = SessionObservationTracker(
            max_buffer_size=self.config.max_buffer_size,
            alpha=self.config.temporal_smoothing_alpha,
            half_life_seconds=self.config.temporal_half_life_seconds,
        )
        self.metrics = PerformanceTracker()

        # Concurrency bounding semaphore
        self._concurrency_semaphore = asyncio.Semaphore(self.config.num_threads * 2)

        # Pipelines initialized in initialize()
        self._facial_pipeline: FacialPipeline | None = None
        self._speech_pipeline: SpeechPipeline | None = None
        self._fusion_pipeline: MultimodalFusionPipeline | None = None

    @property
    def state(self) -> EngineState:
        """Current engine lifecycle state."""
        return self.lifecycle.state

    @property
    def is_running(self) -> bool:
        """Whether the engine is active and ready to accept observations."""
        return self.lifecycle.is_running

    def register_consent(self, session_id: str, consent_reference: str) -> None:
        """Register active user consent for an interaction session."""
        self.consent_mgr.register_consent(session_id, consent_reference)

    def revoke_consent(self, session_id: str) -> None:
        """Revoke user consent for an interaction session immediately."""
        self.consent_mgr.revoke_consent(session_id)

    async def initialize(self) -> None:
        """Initialize engine components, pipelines, and model adapters."""
        await self.lifecycle.transition_to(
            EngineState.INITIALIZING, "Initializing pipelines and models"
        )
        try:
            if self.config.enable_facial:
                self._facial_pipeline = FacialPipeline(self.config)

            if self.config.enable_speech:
                self._speech_pipeline = SpeechPipeline(self.config)

            if self.config.enable_multimodal_fusion:
                self._fusion_pipeline = MultimodalFusionPipeline(self.config)

            await self.lifecycle.transition_to(
                EngineState.INITIALIZED, "Engine initialization complete"
            )
        except Exception as exc:
            await self.lifecycle.transition_to(EngineState.FAILED, f"Initialization error: {exc}")
            raise

    async def start(self) -> None:
        """Transition engine from INITIALIZED to RUNNING."""
        if self.lifecycle.state != EngineState.INITIALIZED:
            if self.lifecycle.state == EngineState.UNINITIALIZED:
                await self.initialize()
            elif self.lifecycle.state == EngineState.PAUSED:
                await self.lifecycle.transition_to(EngineState.RUNNING, "Resumed from paused")
                return
            elif self.lifecycle.state == EngineState.RUNNING:
                return
            else:
                raise ERSLifecycleError(
                    f"Cannot start engine in state {self.lifecycle.state.value}"
                )

        await self.lifecycle.transition_to(EngineState.STARTING, "Starting processing workers")
        await self.lifecycle.transition_to(EngineState.RUNNING, "Engine actively running")

    async def pause(self) -> None:
        """Pause observation processing."""
        await self.lifecycle.transition_to(EngineState.PAUSED, "Paused by request")

    async def stop(self) -> None:
        """Gracefully stop engine and flush resources."""
        if self.lifecycle.state in (EngineState.STOPPED, EngineState.UNINITIALIZED):
            return
        await self.lifecycle.transition_to(EngineState.STOPPING, "Stopping engine")
        self.tracker.reset_all_sessions()
        await self.lifecycle.transition_to(EngineState.STOPPED, "Engine stopped cleanly")

    async def close(self) -> None:
        """Alias for stop() for context manager / teardown consistency."""
        await self.stop()

    async def __aenter__(self) -> ERSEngine:
        await self.start()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        await self.close()

    def health(self) -> dict[str, Any]:
        """Query engine and component health status."""
        h = self.lifecycle.get_health_status()
        h["facial_enabled"] = self.config.enable_facial
        h["speech_enabled"] = self.config.enable_speech
        h["fusion_enabled"] = self.config.enable_multimodal_fusion
        h["facial_pipeline_ready"] = self._facial_pipeline is not None
        h["speech_pipeline_ready"] = self._speech_pipeline is not None
        return h

    def get_metrics(self) -> dict[str, Any]:
        """Query performance metrics and latency statistics."""
        return self.metrics.get_summary()

    def reset_session(self, session_id: str) -> None:
        """Securely clear all history, buffers, and smoother memory for a session."""
        self.tracker.reset_session(session_id)
        logger.info(f"Session history flushed for '{session_id}'")

    async def process(self, inp: ERSInput) -> EmotionObservation | FusionResult:
        """Universal processing entrypoint routing by input modality."""
        if not self.is_running:
            raise ERSLifecycleError(
                f"ERS engine cannot process in state {self.lifecycle.state.value}"
            )

        # Validate consent before processing; scrub payloads even on rejection
        try:
            self.consent_mgr.validate_consent(inp.session_id, inp.consent_reference)
        except Exception:
            inp.scrub_media_payload()
            raise

        async with self._concurrency_semaphore:
            # Publish input received event
            await self.event_bus.publish(
                TOPIC_INPUT_RECEIVED,
                {"observation_id": inp.observation_id, "modality": inp.modality.value},
            )

            if inp.modality == Modality.FACIAL:
                return await self.process_facial(inp)
            elif inp.modality == Modality.SPEECH:
                return await self.process_speech(inp)
            elif inp.modality == Modality.MULTIMODAL:
                # If multimodal envelope contains both payloads
                face_inp = ERSInput(
                    observation_id=f"{inp.observation_id}-face",
                    session_id=inp.session_id,
                    timestamp=inp.timestamp,
                    modality=Modality.FACIAL,
                    consent_reference=inp.consent_reference,
                    image_payload=inp.image_payload,
                    image_dimensions=inp.image_dimensions,
                    source_metadata=inp.source_metadata,
                )
                speech_inp = ERSInput(
                    observation_id=f"{inp.observation_id}-speech",
                    session_id=inp.session_id,
                    timestamp=inp.timestamp,
                    modality=Modality.SPEECH,
                    consent_reference=inp.consent_reference,
                    audio_payload=inp.audio_payload,
                    sample_rate=inp.sample_rate,
                    source_metadata=inp.source_metadata,
                )
                return await self.process_multimodal(face_inp, speech_inp)
            else:
                raise ValueError(f"Unsupported modality: {inp.modality}")

    async def process_facial(self, inp: ERSInput) -> EmotionObservation:
        """Process facial visual input and apply temporal smoothing."""
        if not self.config.enable_facial or self._facial_pipeline is None:
            inp.scrub_media_payload()
            return EmotionObservation(
                observation_id=inp.observation_id,
                timestamp=inp.timestamp,
                modality=Modality.FACIAL,
                expression_observations={},
                emotion_probabilities={EmotionCategory.INSUFFICIENT_EVIDENCE.value: 1.0},
                dominant_estimate=EmotionCategory.INSUFFICIENT_EVIDENCE.value,
                confidence=0.0,
                uncertainty=1.0,
                quality_score=0.0,
                model_id="none",
                model_version="0.0.0",
                processing_latency_ms=0.0,
                limitations=["Facial expression pipeline is disabled in configuration."],
                status=ObservationStatus.INSUFFICIENT_EVIDENCE,
                is_definitive_claim=False,
            )

        try:
            self.consent_mgr.validate_consent(inp.session_id, inp.consent_reference)
        except Exception:
            inp.scrub_media_payload()
            raise

        # Run pipeline in worker thread to prevent blocking asyncio event loop
        loop = asyncio.get_running_loop()
        obs: EmotionObservation = await loop.run_in_executor(
            None, self._facial_pipeline.process, inp
        )

        # Apply temporal smoothing
        smoothed_probs = self.tracker.record_observation(inp.session_id, obs)
        # Epistemic honesty: If observation is unvalidated or abstaining, suppress discrete categorization
        if not obs.is_validated or obs.status in (
            ObservationStatus.INSUFFICIENT_EVIDENCE,
            ObservationStatus.MODEL_UNVALIDATED,
        ):
            smoothed_dominant = obs.dominant_estimate
        else:
            smoothed_dominant = max(smoothed_probs.items(), key=lambda it: it[1])[0]

        smoothed_obs = EmotionObservation(
            observation_id=obs.observation_id,
            timestamp=obs.timestamp,
            modality=obs.modality,
            expression_observations=obs.expression_observations,
            emotion_probabilities=smoothed_probs,
            dominant_estimate=smoothed_dominant,
            confidence=obs.confidence,
            uncertainty=obs.uncertainty,
            quality_score=obs.quality_score,
            model_id=obs.model_id,
            model_version=obs.model_version,
            processing_latency_ms=obs.processing_latency_ms,
            limitations=obs.limitations,
            status=obs.status,
            model_state=obs.model_state,
            is_validated=obs.is_validated,
            is_definitive_claim=False,
        )

        self.metrics.record_process(
            total_latency_ms=smoothed_obs.processing_latency_ms,
            modality="facial",
            is_error=(smoothed_obs.status == ObservationStatus.FAILED),
            is_abstention=(smoothed_obs.status == ObservationStatus.INSUFFICIENT_EVIDENCE),
        )

        await self.event_bus.publish(
            TOPIC_OBSERVATION_CREATED,
            {
                "observation_id": smoothed_obs.observation_id,
                "modality": smoothed_obs.modality.value,
                "dominant_estimate": smoothed_obs.dominant_estimate,
                "confidence": smoothed_obs.confidence,
            },
        )

        return smoothed_obs

    async def process_speech(self, inp: ERSInput) -> EmotionObservation:
        """Process acoustic speech input and apply temporal smoothing."""
        if not self.config.enable_speech or self._speech_pipeline is None:
            inp.scrub_media_payload()
            return EmotionObservation(
                observation_id=inp.observation_id,
                timestamp=inp.timestamp,
                modality=Modality.SPEECH,
                expression_observations={},
                emotion_probabilities={EmotionCategory.INSUFFICIENT_EVIDENCE.value: 1.0},
                dominant_estimate=EmotionCategory.INSUFFICIENT_EVIDENCE.value,
                confidence=0.0,
                uncertainty=1.0,
                quality_score=0.0,
                model_id="none",
                model_version="0.0.0",
                processing_latency_ms=0.0,
                limitations=["Speech acoustic pipeline is disabled in configuration."],
                status=ObservationStatus.INSUFFICIENT_EVIDENCE,
                is_definitive_claim=False,
            )

        try:
            self.consent_mgr.validate_consent(inp.session_id, inp.consent_reference)
        except Exception:
            inp.scrub_media_payload()
            raise

        loop = asyncio.get_running_loop()
        obs: EmotionObservation = await loop.run_in_executor(
            None, self._speech_pipeline.process, inp
        )

        smoothed_probs = self.tracker.record_observation(inp.session_id, obs)
        # Epistemic honesty: If observation is unvalidated or abstaining, suppress discrete categorization
        if not obs.is_validated or obs.status in (
            ObservationStatus.INSUFFICIENT_EVIDENCE,
            ObservationStatus.MODEL_UNVALIDATED,
        ):
            smoothed_dominant = obs.dominant_estimate
        else:
            smoothed_dominant = max(smoothed_probs.items(), key=lambda it: it[1])[0]

        smoothed_obs = EmotionObservation(
            observation_id=obs.observation_id,
            timestamp=obs.timestamp,
            modality=obs.modality,
            expression_observations=obs.expression_observations,
            emotion_probabilities=smoothed_probs,
            dominant_estimate=smoothed_dominant,
            confidence=obs.confidence,
            uncertainty=obs.uncertainty,
            quality_score=obs.quality_score,
            model_id=obs.model_id,
            model_version=obs.model_version,
            processing_latency_ms=obs.processing_latency_ms,
            limitations=obs.limitations,
            status=obs.status,
            model_state=obs.model_state,
            is_validated=obs.is_validated,
            is_definitive_claim=False,
        )

        self.metrics.record_process(
            total_latency_ms=smoothed_obs.processing_latency_ms,
            modality="speech",
            is_error=(smoothed_obs.status == ObservationStatus.FAILED),
            is_abstention=(smoothed_obs.status == ObservationStatus.INSUFFICIENT_EVIDENCE),
        )

        await self.event_bus.publish(
            TOPIC_OBSERVATION_CREATED,
            {
                "observation_id": smoothed_obs.observation_id,
                "modality": smoothed_obs.modality.value,
                "dominant_estimate": smoothed_obs.dominant_estimate,
                "confidence": smoothed_obs.confidence,
            },
        )

        return smoothed_obs

    async def process_multimodal(
        self, facial_input: ERSInput | None, speech_input: ERSInput | None
    ) -> FusionResult:
        """Process synchronized facial and acoustic observations and return fused estimate."""
        start_time = time.perf_counter()
        session_id = (
            facial_input.session_id
            if facial_input
            else (speech_input.session_id if speech_input else "default")
        )

        # Process unimodal streams concurrently
        face_obs = None
        speech_obs = None

        if facial_input is not None and speech_input is not None:
            face_obs, speech_obs = await asyncio.gather(
                self.process_facial(facial_input),
                self.process_speech(speech_input),
            )
        elif facial_input is not None:
            face_obs = await self.process_facial(facial_input)
        elif speech_input is not None:
            speech_obs = await self.process_speech(speech_input)

        if self._fusion_pipeline is None:
            self._fusion_pipeline = MultimodalFusionPipeline(self.config)

        fused = self._fusion_pipeline.fuse(face_obs, speech_obs)

        # Apply temporal smoothing to fused distribution, preserving unvalidated isolation
        smoothed_probs = self.tracker.record_observation(session_id, fused)
        if not fused.is_validated or fused.dominant_estimate in (
            EmotionCategory.INSUFFICIENT_EVIDENCE.value,
            EmotionCategory.UNKNOWN.value,
        ):
            smoothed_dominant = fused.dominant_estimate
        else:
            smoothed_dominant = max(smoothed_probs.items(), key=lambda it: it[1])[0]

        final_fused = FusionResult(
            result_id=fused.result_id,
            timestamp=fused.timestamp,
            facial_observation=fused.facial_observation,
            speech_observation=fused.speech_observation,
            fused_probabilities=smoothed_probs,
            dominant_estimate=smoothed_dominant,
            modality_weights=fused.modality_weights,
            confidence=fused.confidence,
            uncertainty=fused.uncertainty,
            conflicting_evidence=fused.conflicting_evidence,
            conflict_metric=fused.conflict_metric,
            missing_modalities=fused.missing_modalities,
            quality_summary=fused.quality_summary,
            limitations=fused.limitations,
            contributing_model_states=fused.contributing_model_states,
            classification_eligible_modalities=fused.classification_eligible_modalities,
            diagnostic_modalities=fused.diagnostic_modalities,
            fusion_status=fused.fusion_status,
            contributing_artifact_hashes=fused.contributing_artifact_hashes,
            contributing_validation_records=fused.contributing_validation_records,
            is_validated=fused.is_validated,
            is_definitive_claim=False,
        )

        total_latency_ms = (time.perf_counter() - start_time) * 1000.0
        self.metrics.record_process(
            total_latency_ms=total_latency_ms,
            modality="multimodal",
            is_error=False,
            is_abstention=(final_fused.confidence < self.config.confidence_threshold),
        )

        await self.event_bus.publish(
            TOPIC_FUSION_COMPLETED,
            {
                "result_id": final_fused.result_id,
                "dominant_estimate": final_fused.dominant_estimate,
                "confidence": final_fused.confidence,
                "conflicting_evidence": final_fused.conflicting_evidence,
            },
        )

        return final_fused
