"""FastAPI application factory and WebSocket streaming server for ERS live input."""

from __future__ import annotations

import json
import logging
import time
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from eon_ers.api.schemas import (
    ConsentRegisterRequest,
    ConsentRevokeRequest,
    ConsentStatusResponse,
    HealthResponse,
    LiveMultimodalMessage,
    ProcessObservationRequest,
    ProcessObservationResponse,
    ResetSessionRequest,
)
from eon_ers.config import ERSConfig
from eon_ers.contracts import EmotionObservation
from eon_ers.engine import ERSEngine
from eon_ers.exceptions import ERSPrivacyConsentError
from eon_ers.live.dashboard import get_dashboard_html
from eon_ers.live.manager import LiveSessionManager
from eon_ers.types import Modality

logger = logging.getLogger("eon.ers.live.server")


def create_live_app(
    engine: ERSEngine | None = None,
    session_manager: LiveSessionManager | None = None,
) -> FastAPI:
    """Create and configure the FastAPI live streaming application."""
    ers_engine = engine or ERSEngine(
        ERSConfig(
            facial_model_path="packages/ers/models/facial_emotion_model.onnx",
            speech_model_path="packages/ers/models/speech_emotion_model.onnx",
        )
    )
    manager = session_manager or LiveSessionManager(ers_engine)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
        await manager.initialize()
        yield
        await manager.shutdown()

    app = FastAPI(
        title="OVIC EON ERS Live Stream Server",
        description="Real-time sensory webcam and microphone affective processing server.",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/", response_class=HTMLResponse)
    async def get_dashboard() -> str:
        """Serve the live interactive dashboard UI."""
        return get_dashboard_html()

    @app.get("/api/health", response_model=HealthResponse)
    async def get_health() -> HealthResponse:
        """Report component lifecycle state and integration boundary status."""
        core_health = ers_engine.event_bus.check_health()
        return HealthResponse(
            component="eon.ers",
            status="HEALTHY" if ers_engine.is_running else "DEGRADED",
            state=ers_engine.state.value,
            is_running=ers_engine.is_running,
            core_integration_status=core_health["status"],
            missing_dependencies=core_health["missing_dependencies"],
            failure_reason=None,
        )

    @app.post("/api/consent/register")
    async def register_consent(req: ConsentRegisterRequest) -> dict[str, Any]:
        """Pre-register user consent for a live session."""
        try:
            manager.register_session_consent(req.session_id, req.consent_reference)
            return {
                "status": "registered",
                "session_id": req.session_id,
                "has_active_consent": True,
                "is_revoked": False,
            }
        except ERSPrivacyConsentError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/consent/revoke")
    async def revoke_consent(req: ConsentRevokeRequest) -> dict[str, Any]:
        """Revoke active consent for a session immediately."""
        manager.revoke_session_consent(req.session_id)
        return {
            "status": "revoked",
            "session_id": req.session_id,
            "has_active_consent": False,
            "is_revoked": True,
        }

    @app.get("/api/consent/status/{session_id}", response_model=ConsentStatusResponse)
    async def get_consent_status(session_id: str) -> ConsentStatusResponse:
        """Inspect active consent status for a session."""
        is_active = manager.has_active_consent(session_id)
        with ers_engine.consent_mgr._lock:
            is_revoked = session_id in ers_engine.consent_mgr._revoked_sessions
            ref = ers_engine.consent_mgr._consents.get(session_id)
            masked = (ref[:4] + "***" + ref[-2:]) if ref and len(ref) >= 6 else None

        return ConsentStatusResponse(
            session_id=session_id,
            has_active_consent=is_active,
            is_revoked=is_revoked,
            masked_reference=masked,
        )

    @app.post("/api/process/unimodal", response_model=ProcessObservationResponse)
    async def process_unimodal(req: ProcessObservationRequest) -> ProcessObservationResponse:
        """Process a single sensory observation via REST."""
        start_time = time.perf_counter()
        if req.modality == Modality.FACIAL:
            if not req.image_base64:
                raise HTTPException(
                    status_code=400, detail="Missing image_base64 for facial modality."
                )
            res = await manager.process_frame(
                req.session_id, req.image_base64, req.consent_reference
            )
        elif req.modality == Modality.SPEECH:
            if not req.audio_base64:
                raise HTTPException(
                    status_code=400, detail="Missing audio_base64 for speech modality."
                )
            res = await manager.process_audio(
                req.session_id, req.audio_base64, req.sample_rate or 16000, req.consent_reference
            )
        else:
            raise HTTPException(
                status_code=400, detail="Use /api/process/multimodal for multimodal requests."
            )

        if res.get("status") in ("error", "consent_rejected", "processing_error"):
            return ProcessObservationResponse(
                status=res["status"],
                observation=None,
                processing_latency_ms=round((time.perf_counter() - start_time) * 1000.0, 2),
                error_message=res.get("error"),
            )

        # Convert dictionary to EmotionObservation schema
        obs = EmotionObservation(
            observation_id=f"obs-{time.time()}",
            timestamp=time.time(),
            modality=Modality(res["modality"]),
            expression_observations=res.get("expression_observations", {}),
            emotion_probabilities=res["emotion_probabilities"],
            dominant_estimate=res["dominant_estimate"],
            confidence=res["confidence"],
            uncertainty=res["uncertainty"],
            quality_score=res["quality_score"],
            model_id=res["model_id"],
            model_version=res["model_version"],
            processing_latency_ms=res["latency_ms"],
            limitations=res.get("limitations", []),
            status=res["status"],
            is_definitive_claim=False,
        )

        return ProcessObservationResponse(
            status=obs.status.value,
            observation=obs,
            processing_latency_ms=round((time.perf_counter() - start_time) * 1000.0, 2),
            error_message=None,
        )

    @app.post("/api/process/frame")
    async def process_frame_endpoint(req: dict[str, Any]) -> dict[str, Any]:
        """Convenience REST endpoint for processing a single visual frame."""
        session_id = req.get("session_id", "default")
        image_b64 = req.get("image_base64", "")
        consent_ref = req.get("consent_reference")
        return await manager.process_frame(session_id, image_b64, consent_ref)

    @app.post("/api/process/audio")
    async def process_audio_endpoint(req: dict[str, Any]) -> dict[str, Any]:
        """Convenience REST endpoint for processing an audio chunk."""
        session_id = req.get("session_id", "default")
        audio_b64 = req.get("audio_base64", "")
        sample_rate = int(req.get("sample_rate", 16000))
        consent_ref = req.get("consent_reference")
        return await manager.process_audio(session_id, audio_b64, sample_rate, consent_ref)

    @app.post("/api/process/multimodal")
    async def process_multimodal(req: LiveMultimodalMessage) -> dict[str, Any]:
        """Process concurrent facial and audio signals via REST."""
        res = await manager.process_multimodal_live(
            session_id=req.session_id,
            image_base64=req.image_base64,
            audio_base64=req.audio_base64,
            sample_rate=req.sample_rate,
            consent_reference=req.consent_reference,
        )
        return res

    @app.post("/api/session/reset")
    async def reset_session(req: ResetSessionRequest) -> dict[str, Any]:
        """Flush session temporal ring buffer."""
        ers_engine.tracker.reset_session(req.session_id)
        return {"status": "reset", "session_id": req.session_id}

    @app.websocket("/ws/live/{session_id}")
    async def websocket_live_stream(websocket: WebSocket, session_id: str) -> None:
        """Bi-directional WebSocket for streaming live webcam and microphone inputs."""
        await websocket.accept()
        latest_face_res: dict[str, Any] | None = None
        latest_speech_res: dict[str, Any] | None = None

        try:
            while True:
                data_text = await websocket.receive_text()
                try:
                    payload = json.loads(data_text)
                except Exception:
                    await websocket.send_text(
                        json.dumps({"type": "error", "error": "Invalid JSON format."})
                    )
                    continue

                msg_type = payload.get("type")
                ref = payload.get("consent_reference")

                if msg_type == "init":
                    if ref:
                        manager.register_session_consent(session_id, ref)
                    await websocket.send_text(
                        json.dumps(
                            {
                                "type": "status",
                                "status": "session_initialized",
                                "session_id": session_id,
                            }
                        )
                    )

                elif msg_type == "frame":
                    img_b64 = payload.get("image_base64")
                    if not img_b64:
                        continue
                    res = await manager.process_frame(session_id, img_b64, ref)
                    latest_face_res = res
                    await websocket.send_text(
                        json.dumps(
                            {
                                "type": "observation",
                                "session_id": session_id,
                                "timestamp": time.time(),
                                "modality": "facial",
                                "data": res,
                                "latency_ms": res.get("latency_ms", 0.0),
                            }
                        )
                    )

                    # Trigger multimodal update if we have observations
                    if latest_face_res and latest_face_res.get("status") not in (
                        "error",
                        "consent_rejected",
                    ):
                        fused_update = _synthesize_live_fusion(latest_face_res, latest_speech_res)
                        await websocket.send_text(
                            json.dumps(
                                {
                                    "type": "fusion",
                                    "session_id": session_id,
                                    "timestamp": time.time(),
                                    "data": fused_update,
                                    "latency_ms": res.get("latency_ms", 0.0),
                                }
                            )
                        )

                elif msg_type == "audio":
                    aud_b64 = payload.get("audio_base64")
                    sr = payload.get("sample_rate", 16000)
                    if not aud_b64:
                        continue
                    res = await manager.process_audio(session_id, aud_b64, sr, ref)
                    latest_speech_res = res
                    await websocket.send_text(
                        json.dumps(
                            {
                                "type": "observation",
                                "session_id": session_id,
                                "timestamp": time.time(),
                                "modality": "speech",
                                "data": res,
                                "latency_ms": res.get("latency_ms", 0.0),
                            }
                        )
                    )

                    if latest_speech_res and latest_speech_res.get("status") not in (
                        "error",
                        "consent_rejected",
                    ):
                        fused_update = _synthesize_live_fusion(latest_face_res, latest_speech_res)
                        await websocket.send_text(
                            json.dumps(
                                {
                                    "type": "fusion",
                                    "session_id": session_id,
                                    "timestamp": time.time(),
                                    "data": fused_update,
                                    "latency_ms": res.get("latency_ms", 0.0),
                                }
                            )
                        )

                elif msg_type == "multimodal":
                    img_b64 = payload.get("image_base64")
                    aud_b64 = payload.get("audio_base64")
                    sr = payload.get("sample_rate", 16000)
                    fused = await manager.process_multimodal_live(
                        session_id=session_id,
                        image_base64=img_b64,
                        audio_base64=aud_b64,
                        sample_rate=sr,
                        consent_reference=ref,
                    )
                    await websocket.send_text(
                        json.dumps(
                            {
                                "type": "fusion",
                                "session_id": session_id,
                                "timestamp": time.time(),
                                "data": fused,
                                "latency_ms": fused.get("latency_ms", 0.0),
                            }
                        )
                    )

                elif msg_type == "revoke":
                    manager.revoke_session_consent(session_id)
                    await websocket.send_text(
                        json.dumps(
                            {
                                "type": "status",
                                "status": "consent_revoked",
                                "session_id": session_id,
                            }
                        )
                    )

                elif msg_type == "stop":
                    await websocket.send_text(
                        json.dumps(
                            {"type": "status", "status": "stopped", "session_id": session_id}
                        )
                    )
                    break

        except WebSocketDisconnect:
            logger.info("WebSocket disconnected for session '%s'.", session_id)
        except Exception as exc:
            logger.error("WebSocket exception on session '%s': %s", session_id, exc, exc_info=True)

    return app


def _synthesize_live_fusion(
    face_res: dict[str, Any] | None, speech_res: dict[str, Any] | None
) -> dict[str, Any]:
    """Combine latest available stream observations for live UI telemetry."""
    if face_res is None and speech_res is None:
        return {
            "dominant_estimate": "INSUFFICIENT_EVIDENCE",
            "confidence": 0.0,
            "uncertainty": 1.0,
            "fused_probabilities": {},
            "modality_weights": {"facial": 0.5, "speech": 0.5},
            "conflicting_evidence": False,
            "conflict_metric": 0.0,
            "is_definitive_claim": False,
        }

    # Weighting based on confidence and quality
    q_face = face_res.get("quality_score", 0.5) if face_res else 0.0
    c_face = face_res.get("confidence", 0.0) if face_res else 0.0
    q_speech = speech_res.get("quality_score", 0.5) if speech_res else 0.0
    c_speech = speech_res.get("confidence", 0.0) if speech_res else 0.0

    raw_w_f = q_face * c_face
    raw_w_s = q_speech * c_speech
    total_w = raw_w_f + raw_w_s

    w_f = round(raw_w_f / total_w, 4) if total_w > 1e-6 else 0.5
    w_s = round(raw_w_s / total_w, 4) if total_w > 1e-6 else 0.5

    # Fuse probabilities
    emotions = ["neutral", "happiness", "sadness", "anger", "fear", "surprise", "disgust"]
    p_f = face_res.get("emotion_probabilities", {}) if face_res else {}
    p_s = speech_res.get("emotion_probabilities", {}) if speech_res else {}

    fused_probs: dict[str, float] = {}
    for em in emotions:
        val = w_f * p_f.get(em, 0.0) + w_s * p_s.get(em, 0.0)
        fused_probs[em] = round(val, 4)

    total_prob = sum(fused_probs.values())
    if total_prob > 1e-6:
        fused_probs = {k: round(v / total_prob, 4) for k, v in fused_probs.items()}

    dominant = (
        max(fused_probs.items(), key=lambda it: it[1])[0]
        if fused_probs
        else "INSUFFICIENT_EVIDENCE"
    )
    conf = round(float(fused_probs.get(dominant, 0.0)), 4) if fused_probs else 0.0
    uncertainty = round(1.0 - conf, 4)

    return {
        "dominant_estimate": dominant,
        "confidence": conf,
        "uncertainty": uncertainty,
        "fused_probabilities": fused_probs,
        "modality_weights": {"facial": w_f, "speech": w_s},
        "conflicting_evidence": False,
        "conflict_metric": 0.0,
        "is_definitive_claim": False,
    }
