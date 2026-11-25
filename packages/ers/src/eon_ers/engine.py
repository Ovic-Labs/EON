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
from eon_ers.text.postprocessing import TextPipeline
from eon_ers.types import EmotionCategory, EngineState, Modality, ObservationStatus
from eon_ers.video.pipeline import VideoAnalysisJobResult, VideoPipeline

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
        self._text_pipeline: TextPipeline | None = None
        self._video_pipeline: VideoPipeline | None = None
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

            if self.config.enable_text:
                self._text_pipeline = TextPipeline(self.config)

            if self.config.enable_video:
                self._video_pipeline = VideoPipeline(
                    self.config, facial_pipeline=self._facial_pipeline
                )

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
        h["text_enabled"] = self.config.enable_text
        h["video_enabled"] = self.config.enable_video
        h["fusion_enabled"] = self.config.enable_multimodal_fusion
        h["facial_pipeline_ready"] = self._facial_pipeline is not None
        h["speech_pipeline_ready"] = self._speech_pipeline is not None
        h["text_pipeline_ready"] = self._text_pipeline is not None
        h["video_pipeline_ready"] = self._video_pipeline is not None
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
            elif inp.modality == Modality.TEXT:
                return await self.process_text(inp)
            elif inp.modality == Modality.MULTIMODAL:
                # If multimodal envelope contains any subset of facial/speech/text payloads
                face_inp = (
                    ERSInput(
                        observation_id=f"{inp.observation_id}-face",
                        session_id=inp.session_id,
                        timestamp=inp.timestamp,
                        modality=Modality.FACIAL,
                        consent_reference=inp.consent_reference,
                        image_payload=inp.image_payload,
                        image_dimensions=inp.image_dimensions,
                        source_metadata=inp.source_metadata,
                    )
                    if inp.image_payload is not None
                    else None
                )
                speech_inp = (
                    ERSInput(
                        observation_id=f"{inp.observation_id}-speech",
                        session_id=inp.session_id,
                        timestamp=inp.timestamp,
                        modality=Modality.SPEECH,
                        consent_reference=inp.consent_reference,
                        audio_payload=inp.audio_payload,
                        sample_rate=inp.sample_rate,
                        source_metadata=inp.source_metadata,
                    )
                    if inp.audio_payload is not None
                    else None
                )
                text_inp = (
                    ERSInput(
                        observation_id=f"{inp.observation_id}-text",
                        session_id=inp.session_id,
                        timestamp=inp.timestamp,
                        modality=Modality.TEXT,
                        consent_reference=inp.consent_reference,
                        text_payload=inp.text_payload,
                        source_metadata=inp.source_metadata,
                    )
                    if inp.text_payload is not None
                    else None
                )
                return await self.process_multimodal(face_inp, speech_inp, text_input=text_inp)
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

        smoothed_obs = obs.model_copy(
            update={
                "emotion_probabilities": smoothed_probs,
                "dominant_estimate": smoothed_dominant,
                "is_definitive_claim": False,
            }
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

        smoothed_obs = obs.model_copy(
            update={
                "emotion_probabilities": smoothed_probs,
                "dominant_estimate": smoothed_dominant,
                "is_definitive_claim": False,
            }
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

    async def process_text(self, inp: ERSInput) -> EmotionObservation:
        """Process UTF-8 text input for distinct textual sentiment and affect estimation."""
        if not self.config.enable_text or self._text_pipeline is None:
            inp.scrub_media_payload()
            return EmotionObservation(
                observation_id=inp.observation_id,
                timestamp=inp.timestamp,
                modality=Modality.TEXT,
                expression_observations={},
                emotion_probabilities={EmotionCategory.INSUFFICIENT_EVIDENCE.value: 1.0},
                dominant_estimate=EmotionCategory.INSUFFICIENT_EVIDENCE.value,
                confidence=0.0,
                uncertainty=1.0,
                quality_score=0.0,
                model_id="none",
                model_version="0.0.0",
                processing_latency_ms=0.0,
                limitations=["Text affect pipeline is disabled in configuration."],
                status=ObservationStatus.INSUFFICIENT_EVIDENCE,
                is_definitive_claim=False,
            )

        try:
            self.consent_mgr.validate_consent(inp.session_id, inp.consent_reference)
        except Exception:
            inp.scrub_media_payload()
            raise

        loop = asyncio.get_running_loop()
        obs: EmotionObservation = await loop.run_in_executor(None, self._text_pipeline.process, inp)

        self.metrics.record_process(
            total_latency_ms=obs.processing_latency_ms,
            modality="text",
            is_error=(obs.status == ObservationStatus.FAILED),
            is_abstention=(obs.status == ObservationStatus.INSUFFICIENT_EVIDENCE),
        )
        await self.event_bus.publish(
            TOPIC_OBSERVATION_CREATED,
            {
                "observation_id": obs.observation_id,
                "modality": obs.modality.value,
                "dominant_estimate": obs.dominant_estimate,
                "confidence": obs.confidence,
            },
        )
        return obs

    async def process_video(
        self,
        job_id: str,
        inp: ERSInput,
        cancel_event: Any | None = None,
    ) -> VideoAnalysisJobResult:
        """Process a bounded video upload through streaming frame decoding and facial analysis."""
        try:
            self.consent_mgr.validate_consent(inp.session_id, inp.consent_reference)
        except Exception:
            inp.scrub_media_payload()
            raise

        if not self.config.enable_video or self._video_pipeline is None:
            inp.scrub_media_payload()
            return VideoAnalysisJobResult(
                job_id=job_id,
                session_id=inp.session_id,
                status="failed",
                error="Video processing pipeline is disabled in configuration.",
            )

        video_bytes = inp.video_payload or b""
        inp.scrub_media_payload()
        loop = asyncio.get_running_loop()
        res: VideoAnalysisJobResult = await loop.run_in_executor(
            None,
            lambda: self._video_pipeline.process_video(  # type: ignore[union-attr]
                job_id=job_id,
                session_id=inp.session_id,
                consent_reference=inp.consent_reference,
                video_bytes=video_bytes,
                cancel_event=cancel_event,
            ),
        )
        self.metrics.record_process(
            total_latency_ms=res.processing_latency_ms,
            modality="video",
            is_error=(res.status == "failed"),
            is_abstention=(not res.is_validated),
        )
        return res

    async def process_multimodal(
        self,
        facial_input: ERSInput | None,
        speech_input: ERSInput | None,
        *,
        text_input: ERSInput | None = None,
    ) -> FusionResult:
        """Process synchronized facial, vocal speech, and optional text observations."""
        start_time = time.perf_counter()
        first_inp = facial_input or speech_input or text_input
        session_id = first_inp.session_id if first_inp is not None else "default"

        tasks: list[tuple[str, Any]] = []
        if facial_input is not None:
            tasks.append(("facial", self.process_facial(facial_input)))
        if speech_input is not None:
            tasks.append(("speech", self.process_speech(speech_input)))
        if text_input is not None:
            tasks.append(("text", self.process_text(text_input)))

        results_map: dict[str, EmotionObservation | None] = {
            "facial": None,
            "speech": None,
            "text": None,
        }
        if tasks:
            resolved = await asyncio.gather(*(coro for _, coro in tasks))
            for (name, _), obs in zip(tasks, resolved):
                results_map[name] = obs

        face_obs = results_map["facial"]
        speech_obs = results_map["speech"]
        text_obs = results_map["text"]

        if self._fusion_pipeline is None:
            self._fusion_pipeline = MultimodalFusionPipeline(self.config)

        fused = self._fusion_pipeline.fuse(
            face_obs,
            speech_obs,
            text_obs=text_obs,
            session_id=session_id,
        )

        # Apply temporal smoothing to fused distribution, preserving unvalidated isolation
        smoothed_probs = self.tracker.record_observation(session_id, fused)
        if not fused.is_validated or fused.dominant_estimate in (
            EmotionCategory.INSUFFICIENT_EVIDENCE.value,
            EmotionCategory.UNKNOWN.value,
        ):
            smoothed_dominant = fused.dominant_estimate
        else:
            smoothed_dominant = max(smoothed_probs.items(), key=lambda it: it[1])[0]

        total_latency_ms = (time.perf_counter() - start_time) * 1000.0
        final_fused = fused.model_copy(
            update={
                "session_id": session_id,
                "fused_probabilities": smoothed_probs,
                "dominant_estimate": smoothed_dominant,
                "processing_latency_ms": round(total_latency_ms, 2),
                "is_definitive_claim": False,
            }
        )

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
