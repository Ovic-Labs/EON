"""Bounded streaming video processing pipeline and async job tracking for ERS."""

from __future__ import annotations

import threading
import time
from collections.abc import Callable

from pydantic import BaseModel, ConfigDict, Field

from eon_ers.config import ERSConfig
from eon_ers.contracts import EmotionObservation, ERSInput
from eon_ers.facial.detection import BoundingBox
from eon_ers.facial.pipeline import FacialPipeline
from eon_ers.types import EmotionCategory, Modality, ObservationStatus
from eon_ers.video.decoder import VideoDecoder
from eon_ers.video.frame_sampler import FrameSampler
from eon_ers.video.tracking import SessionFaceTracker


class VideoAnalysisJobResult(BaseModel):
    """Structured video interval analysis result with bounded frame-level provenance."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    job_id: str = Field(...)
    session_id: str = Field(...)
    status: str = Field(
        ..., description="Job state ('queued', 'running', 'completed', 'cancelled', 'failed')."
    )
    progress: float = Field(default=0.0, ge=0.0, le=1.0)
    frames_decoded: int = Field(default=0, ge=0)
    frames_processed: int = Field(default=0, ge=0)
    skipped_duplicates: int = Field(default=0, ge=0)
    frame_observations: list[EmotionObservation] = Field(default_factory=list)
    aggregated_dominant_estimate: str = Field(default=EmotionCategory.INSUFFICIENT_EVIDENCE.value)
    aggregated_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    aggregated_uncertainty: float = Field(default=1.0, ge=0.0, le=1.0)
    is_validated: bool = Field(default=False)
    is_definitive_claim: bool = Field(default=False, frozen=True)
    limitations: list[str] = Field(default_factory=list)
    processing_latency_ms: float = Field(default=0.0, ge=0.0)
    error: str | None = Field(default=None)


class VideoPipeline:
    """Orchestrates bounded CPU video decoding, frame sampling, tracking, and facial inference."""

    def __init__(
        self,
        config: ERSConfig | None = None,
        facial_pipeline: FacialPipeline | None = None,
    ) -> None:
        self.config = config or ERSConfig()
        self.decoder = VideoDecoder(max_video_bytes=self.config.video_max_bytes)
        self.sampler = FrameSampler(
            sample_fps=self.config.video_sample_fps,
            max_frames=self.config.video_max_frames,
        )
        self.facial_pipeline = facial_pipeline or FacialPipeline(self.config)

    def process_video(
        self,
        job_id: str,
        session_id: str,
        consent_reference: str,
        video_bytes: bytes,
        *,
        cancel_event: threading.Event | None = None,
        progress_callback: Callable[[float, int], None] | None = None,
    ) -> VideoAnalysisJobResult:
        """Process bounded video stream frame-by-frame with cancellation and memory caps."""
        start_time = time.perf_counter()
        tracker = SessionFaceTracker()
        frame_observations: list[EmotionObservation] = []
        decoded_count = 0

        for sampled in self.sampler.sample(self.decoder.iter_frames(video_bytes)):
            if cancel_event is not None and cancel_event.is_set():
                return VideoAnalysisJobResult(
                    job_id=job_id,
                    session_id=session_id,
                    status="cancelled",
                    progress=min(
                        1.0, len(frame_observations) / max(1, self.config.video_max_frames)
                    ),
                    frames_decoded=decoded_count,
                    frames_processed=len(frame_observations),
                    skipped_duplicates=self.sampler.skipped_duplicates,
                    frame_observations=frame_observations,
                    limitations=["Video analysis cancelled before completion."],
                    processing_latency_ms=round((time.perf_counter() - start_time) * 1000.0, 2),
                )

            decoded_count += 1
            frame_inp = ERSInput(
                observation_id=f"{job_id}-f{sampled.frame_index}",
                session_id=session_id,
                timestamp=sampled.timestamp_seconds,
                modality=Modality.FACIAL,
                consent_reference=consent_reference,
                image_payload=sampled.image_bytes,
                image_dimensions=(sampled.width, sampled.height),
            )
            obs = self.facial_pipeline.process(frame_inp)
            if obs.face_bbox:
                bbox = BoundingBox(
                    x_min=obs.face_bbox["x_min"],
                    y_min=obs.face_bbox["y_min"],
                    x_max=obs.face_bbox["x_max"],
                    y_max=obs.face_bbox["y_max"],
                    confidence=obs.face_bbox.get("confidence", 0.5),
                )
                tracks = tracker.update([bbox], sampled.timestamp_seconds)
                if tracks:
                    obs = obs.model_copy(update={"face_id": tracks[0].track_id})
            frame_observations.append(obs)
            if progress_callback is not None:
                progress_callback(
                    min(0.99, len(frame_observations) / max(1, self.config.video_max_frames)),
                    len(frame_observations),
                )

        # Interval aggregation honoring strict validation isolation
        validated_obs = [
            o
            for o in frame_observations
            if o.is_validated and o.status in (ObservationStatus.OK, ObservationStatus.DEGRADED)
        ]
        limitations: list[str] = [
            "Epistemic modesty: Aggregated video cues summarize temporal frames, never true inner emotions."
        ]
        if not validated_obs:
            limitations.append(
                "No empirically validated facial frames available; aggregated video estimate remains INSUFFICIENT_EVIDENCE."
            )
            agg_dom = (
                ObservationStatus.MODEL_UNVALIDATED.value
                if any(o.status == ObservationStatus.MODEL_UNVALIDATED for o in frame_observations)
                else EmotionCategory.INSUFFICIENT_EVIDENCE.value
            )
            agg_conf = 0.0
            agg_unc = 1.0
            is_val = False
        else:
            agg_probs: dict[str, float] = {}
            for o in validated_obs:
                for k, v in o.emotion_probabilities.items():
                    agg_probs[k] = agg_probs.get(k, 0.0) + float(v)
            total_w = sum(agg_probs.values()) or 1.0
            agg_probs = {k: v / total_w for k, v in agg_probs.items()}
            agg_dom = max(agg_probs.items(), key=lambda it: it[1])[0]
            agg_conf = round(float(agg_probs[agg_dom]), 4)
            agg_unc = round(1.0 - agg_conf, 4)
            is_val = True

        latency_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
        return VideoAnalysisJobResult(
            job_id=job_id,
            session_id=session_id,
            status="completed",
            progress=1.0,
            frames_decoded=decoded_count,
            frames_processed=len(frame_observations),
            skipped_duplicates=self.sampler.skipped_duplicates,
            frame_observations=frame_observations,
            aggregated_dominant_estimate=agg_dom,
            aggregated_confidence=agg_conf,
            aggregated_uncertainty=agg_unc,
            is_validated=is_val,
            is_definitive_claim=False,
            limitations=limitations,
            processing_latency_ms=latency_ms,
        )
