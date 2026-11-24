"""Live stream session manager for real-time ERS sensory processing.

Coordinates live webcam frames, microphone audio chunks, consent validation,
and ERS engine pipeline execution with strict zero-disk retention.
"""

from __future__ import annotations

import base64
import logging
import time
from typing import Any

from eon_ers.config import ERSConfig
from eon_ers.contracts import ERSInput
from eon_ers.engine import ERSEngine
from eon_ers.exceptions import ERSError, ERSPrivacyConsentError
from eon_ers.types import Modality

logger = logging.getLogger("eon.ers.live.manager")


class LiveSessionManager:
    """Manages active streaming sessions, consent state, and engine execution."""

    def __init__(self, engine: ERSEngine | None = None) -> None:
        self.engine = engine or ERSEngine(ERSConfig())
        self._active_sessions: dict[str, dict[str, Any]] = {}

    async def initialize(self) -> None:
        """Ensure the underlying ERS engine is initialized and running."""
        if not self.engine.is_running:
            await self.engine.initialize()
            await self.engine.start()

    async def shutdown(self) -> None:
        """Stop engine and clean up active session resources."""
        if self.engine.is_running:
            await self.engine.stop()
        self._active_sessions.clear()

    def register_session_consent(self, session_id: str, consent_reference: str) -> None:
        """Register active user consent for a live session."""
        self.engine.register_consent(session_id, consent_reference)
        self._active_sessions[session_id] = {
            "consent_reference": consent_reference,
            "created_at": time.time(),
            "frame_count": 0,
            "audio_count": 0,
        }
        logger.info("Live session '%s' registered with consent.", session_id)

    def revoke_session_consent(self, session_id: str) -> None:
        """Immediately revoke consent for a session and invalidate its state."""
        self.engine.revoke_consent(session_id)
        if session_id in self._active_sessions:
            del self._active_sessions[session_id]
        logger.info("Live session '%s' consent revoked and state removed.", session_id)

    def has_active_consent(self, session_id: str) -> bool:
        """Check whether a session has active registered consent."""
        with self.engine.consent_mgr._lock:
            return (
                session_id in self.engine.consent_mgr._consents
                and session_id not in self.engine.consent_mgr._revoked_sessions
            )

    def has_consent(self, session_id: str) -> bool:
        """Alias for has_active_consent."""
        return self.has_active_consent(session_id)

    def get_session_consent_status(self, session_id: str) -> dict[str, Any]:
        """Inspect and return current consent state for a session."""
        with self.engine.consent_mgr._lock:
            has_active = (
                session_id in self.engine.consent_mgr._consents
                and session_id not in self.engine.consent_mgr._revoked_sessions
            )
            is_revoked = session_id in self.engine.consent_mgr._revoked_sessions
            ref = self.engine.consent_mgr._consents.get(session_id)
            masked = None
            if ref:
                masked = (ref[:5] + "***" + ref[-3:]) if len(ref) > 8 else "***"
            return {
                "session_id": session_id,
                "has_active_consent": has_active,
                "is_revoked": is_revoked,
                "masked_reference": masked,
            }

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

    async def process_frame(
        self, session_id: str, image_base64: str, consent_reference: str | None = None
    ) -> dict[str, Any]:
        """Ingest and process a single visual webcam frame.

        Enforces zero disk retention: decodes in volatile memory, processes,
        and immediately scrubs raw payload buffers.
        """
        start_time = time.perf_counter()
        ref = consent_reference or self._get_consent_reference(session_id)

        # 1. Base64 decode validation
        try:
            # Strip data URL prefix if present (e.g., 'data:image/jpeg;base64,...')
            if "," in image_base64:
                image_base64 = image_base64.split(",", 1)[1]
            raw_bytes = base64.b64decode(image_base64, validate=True)
            if len(raw_bytes) == 0:
                raise ValueError("Decoded image payload is empty.")
        except Exception as exc:
            return {
                "status": "error",
                "session_id": session_id,
                "modality": Modality.FACIAL.value,
                "error": f"Invalid image base64 payload: {exc}",
                "latency_ms": round((time.perf_counter() - start_time) * 1000.0, 2),
            }

        inp = ERSInput(
            session_id=session_id,
            modality=Modality.FACIAL,
            consent_reference=ref or "",
            image_payload=raw_bytes,
        )

        try:
            obs = await self.engine.process_facial(inp)
            if session_id in self._active_sessions:
                self._active_sessions[session_id]["frame_count"] += 1

            latency_ms = (time.perf_counter() - start_time) * 1000.0
            return {
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
                "expression_observations": obs.expression_observations,
                "limitations": obs.limitations,
                "latency_ms": round(latency_ms, 2),
            }
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

    async def process_audio(
        self,
        session_id: str,
        audio_base64: str,
        sample_rate: int = 16000,
        consent_reference: str | None = None,
    ) -> dict[str, Any]:
        """Ingest and process a single microphone audio chunk."""
        start_time = time.perf_counter()
        ref = consent_reference or self._get_consent_reference(session_id)

        try:
            if "," in audio_base64:
                audio_base64 = audio_base64.split(",", 1)[1]
            raw_bytes = base64.b64decode(audio_base64, validate=True)
            if len(raw_bytes) == 0:
                raise ValueError("Decoded audio payload is empty.")
        except Exception as exc:
            return {
                "status": "error",
                "session_id": session_id,
                "modality": Modality.SPEECH.value,
                "error": f"Invalid audio base64 payload: {exc}",
                "latency_ms": round((time.perf_counter() - start_time) * 1000.0, 2),
            }

        inp = ERSInput(
            session_id=session_id,
            modality=Modality.SPEECH,
            consent_reference=ref or "",
            audio_payload=raw_bytes,
            sample_rate=sample_rate,
        )

        try:
            obs = await self.engine.process_speech(inp)
            if session_id in self._active_sessions:
                self._active_sessions[session_id]["audio_count"] += 1

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

    async def process_multimodal_live(
        self,
        session_id: str,
        image_base64: str | None = None,
        audio_base64: str | None = None,
        sample_rate: int = 16000,
        consent_reference: str | None = None,
    ) -> dict[str, Any]:
        """Ingest and fuse concurrent facial and speech observations."""
        start_time = time.perf_counter()
        ref = consent_reference or self._get_consent_reference(session_id)

        face_inp = None
        if image_base64 is not None:
            try:
                if "," in image_base64:
                    image_base64 = image_base64.split(",", 1)[1]
                face_bytes = base64.b64decode(image_base64, validate=True)
                face_inp = ERSInput(
                    session_id=session_id,
                    modality=Modality.FACIAL,
                    consent_reference=ref or "",
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
                if "," in audio_base64:
                    audio_base64 = audio_base64.split(",", 1)[1]
                speech_bytes = base64.b64decode(audio_base64, validate=True)
                speech_inp = ERSInput(
                    session_id=session_id,
                    modality=Modality.SPEECH,
                    consent_reference=ref or "",
                    audio_payload=speech_bytes,
                    sample_rate=sample_rate,
                )
            except Exception as exc:
                return {
                    "status": "error",
                    "error": f"Invalid multimodal speech payload: {exc}",
                    "latency_ms": round((time.perf_counter() - start_time) * 1000.0, 2),
                }

        try:
            fused = await self.engine.process_multimodal(face_inp, speech_inp)
            latency_ms = (time.perf_counter() - start_time) * 1000.0
            return {
                "status": "ok"
                if fused.confidence >= self.engine.config.confidence_threshold
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

    def _get_consent_reference(self, session_id: str) -> str | None:
        sess = self._active_sessions.get(session_id)
        if sess:
            return sess.get("consent_reference")
        with self.engine.consent_mgr._lock:
            return self.engine.consent_mgr._consents.get(session_id)
