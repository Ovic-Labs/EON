"""Live stream session manager for real-time ERS sensory processing."""

from __future__ import annotations

import logging
import threading
import time
import uuid
from typing import Any

from eon_ers.config import ERSConfig
from eon_ers.contracts import ERSInput
from eon_ers.engine import ERSEngine
from eon_ers.exceptions import ERSError, ERSPrivacyConsentError
from eon_ers.live.session import TERMINAL_LIVE_STATES, LiveSessionRecord, LiveSessionState
from eon_ers.types import Modality
from eon_ers.utils.validation import decode_bounded_base64
from eon_ers.video.pipeline import VideoAnalysisJobResult

logger = logging.getLogger("eon.ers.live.manager")


class LiveSessionManager:
    """Manages active streaming sessions, FSM transitions, consent state, and engine execution."""

    def __init__(self, engine: ERSEngine | None = None, *, max_sessions: int = 256) -> None:
        self.engine = engine or ERSEngine(ERSConfig())
        self.max_sessions = max(8, max_sessions)
        self._active_sessions: dict[str, dict[str, Any]] = {}
        self._sessions: dict[str, LiveSessionRecord] = {}
        self._video_jobs: dict[str, VideoAnalysisJobResult] = {}
        self._video_cancel_events: dict[str, threading.Event] = {}

    def _prune_stale_sessions_if_needed(self) -> None:
        """Evict terminal or expired sessions when approaching bounded session capacity."""
        if len(self._sessions) < self.max_sessions:
            return
        for rec in self._sessions.values():
            rec.check_expired()
        evict_ids = [
            sid
            for sid, rec in self._sessions.items()
            if rec.state in TERMINAL_LIVE_STATES or rec.state == LiveSessionState.EXPIRED
        ]
        for sid in evict_ids:
            self._sessions.pop(sid, None)
            self._active_sessions.pop(sid, None)

    async def initialize(self) -> None:
        """Ensure the underlying ERS engine is initialized and running."""
        if not self.engine.is_running:
            await self.engine.initialize()
            await self.engine.start()

    async def shutdown(self) -> None:
        """Stop engine, cancel video jobs, and clean up active session resources."""
        for evt in self._video_cancel_events.values():
            evt.set()
        for rec in self._sessions.values():
            if rec.state not in TERMINAL_LIVE_STATES:
                rec.transition_to(LiveSessionState.CLOSED)
        if self.engine.is_running:
            await self.engine.stop()
        self._active_sessions.clear()
        self._video_cancel_events.clear()

    def create_live_session(
        self,
        *,
        session_id: str | None = None,
        owner_id: str = "anonymous",
        consent_reference: str | None = None,
        consent_scope: list[str] | None = None,
        history_opt_in: bool = False,
        ttl_seconds: float | None = 3600.0,
    ) -> LiveSessionRecord:
        """Create a managed live session following the explicit lifecycle FSM."""
        sid = (session_id or f"live-{uuid.uuid4().hex[:12]}").strip()
        existing = self._sessions.get(sid)
        if existing is not None and existing.state == LiveSessionState.REVOKED:
            raise ERSPrivacyConsentError(
                f"Session '{sid}' was explicitly revoked and cannot be reused. Create a new session ID."
            )
        self._prune_stale_sessions_if_needed()
        if sid not in self._sessions and len(self._sessions) >= self.max_sessions:
            raise ERSError(
                f"Live session capacity reached ({self.max_sessions} active sessions). Try again later.",
                error_code="ERS_SESSION_CAPACITY_EXCEEDED",
            )
        rec = LiveSessionRecord(
            session_id=sid,
            owner_id=owner_id,
            state=LiveSessionState.CREATED,
            expires_at=(time.time() + ttl_seconds) if ttl_seconds else None,
            consent_scope=consent_scope or ["facial", "speech", "text"],
            history_opt_in=bool(history_opt_in and self.engine.config.enable_session_history),
        )
        rec.transition_to(LiveSessionState.CONSENT_PENDING)
        self._sessions[sid] = rec
        if consent_reference:
            self.register_session_consent(sid, consent_reference, owner_id=owner_id)
        return rec

    def get_live_session(self, session_id: str) -> LiveSessionRecord | None:
        rec = self._sessions.get(session_id.strip())
        if rec is not None:
            rec.check_expired()
        return rec

    def list_live_sessions(self, owner_id: str | None = None) -> list[LiveSessionRecord]:
        res: list[LiveSessionRecord] = []
        for rec in self._sessions.values():
            rec.check_expired()
            if owner_id is None or rec.owner_id == owner_id:
                res.append(rec)
        return res

    def register_session_consent(
        self, session_id: str, consent_reference: str, *, owner_id: str = "anonymous"
    ) -> None:
        """Register active user consent without caching plaintext secrets."""
        clean_session = session_id.strip()
        existing = self._sessions.get(clean_session)
        if existing is not None and existing.state == LiveSessionState.REVOKED:
            raise ERSPrivacyConsentError(
                f"Consent registration rejected: Session '{clean_session}' is permanently revoked. Use a new session ID."
            )
        self.engine.register_consent(session_id, consent_reference)
        self._active_sessions[clean_session] = {
            "created_at": time.time(),
            "owner_id": owner_id,
            "frame_count": 0,
            "audio_count": 0,
        }
        rec = self._sessions.get(clean_session)
        if rec is None:
            rec = LiveSessionRecord(
                session_id=clean_session,
                owner_id=owner_id,
                state=LiveSessionState.READY,
                history_opt_in=self.engine.config.enable_session_history,
            )
            self._sessions[clean_session] = rec
        elif rec.state in (
            LiveSessionState.CREATED,
            LiveSessionState.AUTHENTICATING,
            LiveSessionState.CONSENT_PENDING,
        ):
            rec.transition_to(LiveSessionState.READY)
        logger.info("Live session '%s' registered with consent.", clean_session)

    def revoke_session_consent(self, session_id: str) -> None:
        """Immediately revoke consent for a session and terminate active streaming."""
        self.engine.revoke_consent(session_id)
        clean_session = session_id.strip()
        if clean_session in self._active_sessions:
            del self._active_sessions[clean_session]
        rec = self._sessions.get(clean_session)
        if rec is not None and rec.state not in TERMINAL_LIVE_STATES:
            rec.transition_to(LiveSessionState.REVOKED)
        elif rec is not None:
            rec.camera_active = False
            rec.microphone_active = False
        logger.info("Live session '%s' consent revoked and state removed.", clean_session)

    def delete_live_session(self, session_id: str) -> bool:
        """Close session, revoke consent, and purge session history."""
        clean_session = session_id.strip()
        existed = clean_session in self._sessions or clean_session in self._active_sessions
        self.engine.reset_session(clean_session)
        if self.has_active_consent(clean_session):
            self.engine.revoke_consent(clean_session)
        self._active_sessions.pop(clean_session, None)
        rec = self._sessions.get(clean_session)
        if rec is not None:
            if rec.state not in TERMINAL_LIVE_STATES:
                if rec.state in (
                    LiveSessionState.READY,
                    LiveSessionState.STREAMING,
                    LiveSessionState.PAUSED,
                ):
                    rec.transition_to(LiveSessionState.STOPPING)
                rec.transition_to(LiveSessionState.CLOSED)
            rec.history.clear()
        return existed

    def has_active_consent(self, session_id: str) -> bool:
        """Check whether a session has active registered consent."""
        return self.engine.consent_mgr.has_active_consent(session_id)

    def has_consent(self, session_id: str) -> bool:
        """Alias for has_active_consent."""
        return self.has_active_consent(session_id)

    def get_session_consent_status(self, session_id: str) -> dict[str, Any]:
        """Inspect and return current consent state for a session."""
        return self.engine.consent_mgr.get_status(session_id)

    def get_health_status(self) -> dict[str, Any]:
        """Return engine and server health status report."""
        h = self.engine.health()
        return {
            "status": "HEALTHY" if self.engine.is_running else "UNHEALTHY",
            "state": self.engine.lifecycle.state.value,
            "is_running": self.engine.is_running,
            "core_integration_status": "NOT_CONNECTED",
            "missing_dependencies": [],
            "engine_health": h,
        }

    def _mark_streaming_activity(
        self, session_id: str, *, camera: bool = False, mic: bool = False
    ) -> None:
        rec = self._sessions.get(session_id.strip())
        now = time.time()
        if rec is not None and rec.state == LiveSessionState.READY:
            rec.transition_to(LiveSessionState.STREAMING)
        if rec is not None:
            if camera:
                rec.camera_active = True
                rec.last_camera_at = now
                rec.frame_count += 1
            if mic:
                rec.microphone_active = True
                rec.last_microphone_at = now
                rec.audio_count += 1

    def set_session_device_state(
        self,
        session_id: str,
        *,
        camera_active: bool | None = None,
        microphone_active: bool | None = None,
    ) -> None:
        """Update verified device state (for example on client stop or track disconnect)."""
        rec = self._sessions.get(session_id.strip())
        if rec is None:
            return
        if camera_active is not None:
            rec.camera_active = bool(camera_active)
        if microphone_active is not None:
            rec.microphone_active = bool(microphone_active)

    def get_verified_device_status(self, stale_after_seconds: float = 15.0) -> dict[str, Any]:
        """Compute true observed device telemetry rather than static hardcoded flags."""
        now = time.time()
        cam_active = False
        mic_active = False
        latest_capture: float | None = None
        consented_sessions: list[str] = []

        for sid, rec in self._sessions.items():
            rec.check_expired()
            if rec.state in TERMINAL_LIVE_STATES or not self.has_active_consent(sid):
                rec.camera_active = False
                rec.microphone_active = False
                continue
            consented_sessions.append(sid)
            if rec.camera_active and rec.last_camera_at is not None:
                if (
                    now - rec.last_camera_at
                ) <= stale_after_seconds and rec.state != LiveSessionState.PAUSED:
                    cam_active = True
                    latest_capture = max(latest_capture or 0.0, rec.last_camera_at)
                else:
                    rec.camera_active = False
            if rec.microphone_active and rec.last_microphone_at is not None:
                if (
                    now - rec.last_microphone_at
                ) <= stale_after_seconds and rec.state != LiveSessionState.PAUSED:
                    mic_active = True
                    latest_capture = max(latest_capture or 0.0, rec.last_microphone_at)
                else:
                    rec.microphone_active = False

        for sid in self._active_sessions:
            if sid not in consented_sessions and self.has_active_consent(sid):
                consented_sessions.append(sid)

        has_consent = len(consented_sessions) > 0
        return {
            "camera_active": cam_active,
            "microphone_active": mic_active,
            "camera_state": "active" if cam_active else ("inactive" if has_consent else "unknown"),
            "microphone_state": "active"
            if mic_active
            else ("inactive" if has_consent else "unknown"),
            "active_session_count": len(consented_sessions),
            "last_capture_timestamp": latest_capture,
            "has_consent": has_consent,
            "session_id": consented_sessions[0] if consented_sessions else None,
        }

    async def process_frame(
        self, session_id: str, image_base64: str, consent_reference: str | None = None
    ) -> dict[str, Any]:
        """Ingest and process a single visual webcam frame with bounded memory."""
        start_time = time.perf_counter()

        try:
            raw_bytes = decode_bounded_base64(image_base64, self.engine.config.max_image_bytes)
        except Exception as exc:
            return {
                "status": "error",
                "session_id": session_id,
                "modality": Modality.FACIAL.value,
                "error": f"Invalid image base64 payload: {exc}",
                "latency_ms": round((time.perf_counter() - start_time) * 1000.0, 2),
            }

        if not consent_reference or not consent_reference.strip():
            return {
                "status": "consent_rejected",
                "session_id": session_id,
                "modality": Modality.FACIAL.value,
                "error": "Missing or empty consent_reference; explicit caller consent is required.",
                "latency_ms": round((time.perf_counter() - start_time) * 1000.0, 2),
            }

        rec = self.get_live_session(session_id)
        if rec is not None and rec.state in (LiveSessionState.EXPIRED, LiveSessionState.CLOSED):
            return {
                "status": "consent_rejected",
                "session_id": session_id,
                "modality": Modality.FACIAL.value,
                "error": f"Live session is {rec.state.value}.",
                "latency_ms": round((time.perf_counter() - start_time) * 1000.0, 2),
            }

        inp = ERSInput(
            session_id=session_id,
            modality=Modality.FACIAL,
            consent_reference=consent_reference,
            image_payload=raw_bytes,
        )

        try:
            obs = await self.engine.process_facial(inp)
            if session_id in self._active_sessions:
                self._active_sessions[session_id]["frame_count"] += 1
            self._mark_streaming_activity(session_id, camera=True)

            latency_ms = (time.perf_counter() - start_time) * 1000.0
            payload = {
                "status": obs.status.value,
                "session_id": session_id,
                "modality": Modality.FACIAL.value,
                "dominant_estimate": obs.dominant_estimate,
                "emotion_probabilities": obs.emotion_probabilities,
                "confidence": obs.confidence,
                "uncertainty": obs.uncertainty,
                "quality_score": obs.quality_score,
                "model_id": obs.model_id,
                "model_version": obs.model_version,
                "model_state": obs.model_state.value,
                "is_validated": obs.is_validated,
                "is_definitive_claim": obs.is_definitive_claim,
                "face_id": obs.face_id,
                "face_bbox": obs.face_bbox,
                "face_count": obs.face_count,
                "expression_observations": obs.expression_observations,
                "limitations": obs.limitations,
                "latency_ms": round(latency_ms, 2),
            }
            if rec is not None:
                rec.record_history_summary(
                    {
                        "timestamp": obs.timestamp,
                        "modality": "facial",
                        "dominant_estimate": obs.dominant_estimate,
                        "confidence": obs.confidence,
                    }
                )
            return payload
        except ERSPrivacyConsentError as exc:
            return {
                "status": "consent_rejected",
                "session_id": session_id,
                "modality": Modality.FACIAL.value,
                "error": str(exc),
                "latency_ms": round((time.perf_counter() - start_time) * 1000.0, 2),
            }
        except ERSError as exc:
            return {
                "status": "processing_error",
                "session_id": session_id,
                "modality": Modality.FACIAL.value,
                "error": str(exc),
                "latency_ms": round((time.perf_counter() - start_time) * 1000.0, 2),
            }
        finally:
            inp.scrub_media_payload()

    async def process_audio(
        self,
        session_id: str,
        audio_base64: str,
        sample_rate: int = 16000,
        consent_reference: str | None = None,
    ) -> dict[str, Any]:
        """Ingest and process a single microphone audio chunk with caller-supplied consent."""
        start_time = time.perf_counter()

        try:
            raw_bytes = decode_bounded_base64(audio_base64, self.engine.config.max_audio_bytes)
        except Exception as exc:
            return {
                "status": "error",
                "session_id": session_id,
                "modality": Modality.SPEECH.value,
                "error": f"Invalid audio base64 payload: {exc}",
                "latency_ms": round((time.perf_counter() - start_time) * 1000.0, 2),
            }

        if not consent_reference or not consent_reference.strip():
            return {
                "status": "consent_rejected",
                "session_id": session_id,
                "modality": Modality.SPEECH.value,
                "error": "Missing or empty consent_reference; explicit caller consent is required.",
                "latency_ms": round((time.perf_counter() - start_time) * 1000.0, 2),
            }

        inp = ERSInput(
            session_id=session_id,
            modality=Modality.SPEECH,
            consent_reference=consent_reference,
            audio_payload=raw_bytes,
            sample_rate=sample_rate,
        )

        try:
            obs = await self.engine.process_speech(inp)
            if session_id in self._active_sessions:
                self._active_sessions[session_id]["audio_count"] += 1
            self._mark_streaming_activity(session_id, mic=True)

            latency_ms = (time.perf_counter() - start_time) * 1000.0
            return {
                "status": obs.status.value,
                "session_id": session_id,
                "modality": Modality.SPEECH.value,
                "dominant_estimate": obs.dominant_estimate,
                "emotion_probabilities": obs.emotion_probabilities,
                "confidence": obs.confidence,
                "uncertainty": obs.uncertainty,
                "quality_score": obs.quality_score,
                "model_id": obs.model_id,
                "model_version": obs.model_version,
                "model_state": obs.model_state.value,
                "is_validated": obs.is_validated,
                "is_definitive_claim": obs.is_definitive_claim,
                "voice_activity": obs.voice_activity,
                "speech_ratio": obs.speech_ratio,
                "expression_observations": obs.expression_observations,
                "limitations": obs.limitations,
                "latency_ms": round(latency_ms, 2),
            }
        except ERSPrivacyConsentError as exc:
            return {
                "status": "consent_rejected",
                "session_id": session_id,
                "modality": Modality.SPEECH.value,
                "error": str(exc),
                "latency_ms": round((time.perf_counter() - start_time) * 1000.0, 2),
            }
        except ERSError as exc:
            return {
                "status": "processing_error",
                "session_id": session_id,
                "modality": Modality.SPEECH.value,
                "error": str(exc),
                "latency_ms": round((time.perf_counter() - start_time) * 1000.0, 2),
            }
        finally:
            inp.scrub_media_payload()

    async def process_text(
        self,
        session_id: str,
        text: str,
        consent_reference: str | None = None,
    ) -> dict[str, Any]:
        """Process UTF-8 text affect observation with consent enforcement."""
        start_time = time.perf_counter()
        if not consent_reference or not consent_reference.strip():
            return {
                "status": "consent_rejected",
                "session_id": session_id,
                "modality": Modality.TEXT.value,
                "error": "Missing or empty consent_reference; explicit caller consent is required.",
                "latency_ms": round((time.perf_counter() - start_time) * 1000.0, 2),
            }
        inp = ERSInput(
            session_id=session_id,
            modality=Modality.TEXT,
            consent_reference=consent_reference,
            text_payload=text,
        )
        try:
            obs = await self.engine.process_text(inp)
            rec = self._sessions.get(session_id.strip())
            if rec is not None:
                rec.text_count += 1
            return {
                "status": obs.status.value,
                "session_id": session_id,
                "modality": Modality.TEXT.value,
                "dominant_estimate": obs.dominant_estimate,
                "emotion_probabilities": obs.emotion_probabilities,
                "confidence": obs.confidence,
                "uncertainty": obs.uncertainty,
                "quality_score": obs.quality_score,
                "model_id": obs.model_id,
                "model_version": obs.model_version,
                "model_state": obs.model_state.value,
                "is_validated": obs.is_validated,
                "is_definitive_claim": obs.is_definitive_claim,
                "expression_observations": obs.expression_observations,
                "limitations": obs.limitations,
                "latency_ms": round((time.perf_counter() - start_time) * 1000.0, 2),
            }
        except ERSPrivacyConsentError as exc:
            return {
                "status": "consent_rejected",
                "session_id": session_id,
                "modality": Modality.TEXT.value,
                "error": str(exc),
                "latency_ms": round((time.perf_counter() - start_time) * 1000.0, 2),
            }
        finally:
            inp.scrub_media_payload()

    async def process_multimodal_live(
        self,
        session_id: str,
        image_base64: str | None = None,
        audio_base64: str | None = None,
        sample_rate: int = 16000,
        consent_reference: str | None = None,
        text: str | None = None,
    ) -> dict[str, Any]:
        """Ingest and fuse concurrent facial, vocal, and optional text streams."""
        start_time = time.perf_counter()

        if not consent_reference or not consent_reference.strip():
            return {
                "status": "consent_rejected",
                "session_id": session_id,
                "error": "Missing or empty consent_reference; explicit caller consent is required.",
                "latency_ms": round((time.perf_counter() - start_time) * 1000.0, 2),
            }

        face_inp = None
        if image_base64 is not None:
            try:
                face_bytes = decode_bounded_base64(image_base64, self.engine.config.max_image_bytes)
                face_inp = ERSInput(
                    session_id=session_id,
                    modality=Modality.FACIAL,
                    consent_reference=consent_reference,
                    image_payload=face_bytes,
                )
            except Exception as exc:
                return {
                    "status": "error",
                    "error": f"Invalid multimodal face payload: {exc}",
                    "latency_ms": round((time.perf_counter() - start_time) * 1000.0, 2),
                }

        speech_inp = None
        if audio_base64 is not None:
            try:
                speech_bytes = decode_bounded_base64(
                    audio_base64, self.engine.config.max_audio_bytes
                )
                speech_inp = ERSInput(
                    session_id=session_id,
                    modality=Modality.SPEECH,
                    consent_reference=consent_reference,
                    audio_payload=speech_bytes,
                    sample_rate=sample_rate,
                )
            except Exception as exc:
                if face_inp is not None:
                    face_inp.scrub_media_payload()
                return {
                    "status": "error",
                    "error": f"Invalid multimodal speech payload: {exc}",
                    "latency_ms": round((time.perf_counter() - start_time) * 1000.0, 2),
                }

        text_inp = None
        if text is not None:
            text_inp = ERSInput(
                session_id=session_id,
                modality=Modality.TEXT,
                consent_reference=consent_reference,
                text_payload=text,
            )

        try:
            fused = await self.engine.process_multimodal(face_inp, speech_inp, text_input=text_inp)
            latency_ms = (time.perf_counter() - start_time) * 1000.0
            return {
                "schema_version": fused.schema_version,
                "status": "ok"
                if fused.is_validated
                and fused.confidence >= self.engine.config.confidence_threshold
                else "insufficient_evidence",
                "session_id": session_id,
                "result_id": fused.result_id,
                "dominant_estimate": fused.dominant_estimate,
                "fused_probabilities": fused.fused_probabilities,
                "confidence": fused.confidence,
                "uncertainty": fused.uncertainty,
                "modality_weights": fused.modality_weights,
                "conflicting_evidence": fused.conflicting_evidence,
                "conflict_metric": fused.conflict_metric,
                "missing_modalities": [m.value for m in fused.missing_modalities],
                "quality_summary": fused.quality_summary,
                "contributing_model_states": fused.contributing_model_states,
                "classification_eligible_modalities": fused.classification_eligible_modalities,
                "diagnostic_modalities": fused.diagnostic_modalities,
                "excluded_modalities": fused.excluded_modalities,
                "fusion_algorithm": fused.fusion_algorithm,
                "fusion_status": fused.fusion_status,
                "is_validated": fused.is_validated,
                "limitations": fused.limitations,
                "is_definitive_claim": fused.is_definitive_claim,
                "latency_ms": round(latency_ms, 2),
            }
        except ERSPrivacyConsentError as exc:
            return {
                "status": "consent_rejected",
                "session_id": session_id,
                "error": str(exc),
                "latency_ms": round((time.perf_counter() - start_time) * 1000.0, 2),
            }
        except Exception as exc:
            return {
                "status": "processing_error",
                "session_id": session_id,
                "error": str(exc),
                "latency_ms": round((time.perf_counter() - start_time) * 1000.0, 2),
            }
        finally:
            if face_inp is not None:
                face_inp.scrub_media_payload()
            if speech_inp is not None:
                speech_inp.scrub_media_payload()
            if text_inp is not None:
                text_inp.scrub_media_payload()

    async def submit_video_job(
        self,
        session_id: str,
        video_base64: str,
        consent_reference: str,
    ) -> VideoAnalysisJobResult:
        """Decode bounded video payload and execute bounded analysis job."""
        job_id = f"vjob-{uuid.uuid4().hex[:10]}"
        cancel_evt = threading.Event()
        self._video_cancel_events[job_id] = cancel_evt
        raw_bytes = decode_bounded_base64(video_base64, self.engine.config.video_max_bytes)
        inp = ERSInput(
            session_id=session_id,
            modality=Modality.VIDEO,
            consent_reference=consent_reference,
            video_payload=raw_bytes,
        )
        res = await self.engine.process_video(job_id, inp, cancel_event=cancel_evt)
        self._video_jobs[job_id] = res
        return res

    def get_video_job(self, job_id: str) -> VideoAnalysisJobResult | None:
        return self._video_jobs.get(job_id)

    def cancel_video_job(self, job_id: str) -> bool:
        evt = self._video_cancel_events.get(job_id)
        if evt is not None:
            evt.set()
            return True
        return False
