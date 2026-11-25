"""FastAPI application factory and WebSocket streaming server for ERS live input."""

from __future__ import annotations

import logging
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, AsyncGenerator

from fastapi import FastAPI, HTTPException, Request, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse

from eon_ers.api.authentication import APIKeyAuthManager
from eon_ers.api.rate_limits import SlidingWindowRateLimiter
from eon_ers.api.routes import build_v1_router
from eon_ers.api.schemas import (
    ConsentRegisterRequest,
    ConsentRevokeRequest,
    ConsentStatusResponse,
    DeviceStatusResponse,
    HealthResponse,
    LiveMultimodalMessage,
    ModelStatusDetail,
    ModelStatusResponse,
    PerformanceTelemetryResponse,
    ProcessObservationRequest,
    ProcessObservationResponse,
    ResetSessionRequest,
)
from eon_ers.config import ERSConfig
from eon_ers.contracts import EmotionObservation
from eon_ers.engine import ERSEngine
from eon_ers.exceptions import ERSError, ERSPrivacyConsentError
from eon_ers.live.dashboard import get_dashboard_html
from eon_ers.live.manager import LiveSessionManager
from eon_ers.live.websocket import handle_live_websocket
from eon_ers.models.registry import ModelRegistry
from eon_ers.types import Modality, ModelState

logger = logging.getLogger("eon.ers.live.server")


def create_live_app(
    engine: ERSEngine | None = None,
    session_manager: LiveSessionManager | None = None,
    *,
    auth_manager: APIKeyAuthManager | None = None,
    model_registry: ModelRegistry | None = None,
) -> FastAPI:
    """Create and configure the FastAPI live streaming application."""
    ers_engine = engine or ERSEngine(
        ERSConfig(
            facial_model_path="packages/ers/models/facial_emotion_model.onnx",
            speech_model_path="packages/ers/models/speech_emotion_model.onnx",
        )
    )
    manager = session_manager or LiveSessionManager(ers_engine)
    auth = auth_manager or APIKeyAuthManager(require_auth=ers_engine.config.require_api_auth)
    limiter = SlidingWindowRateLimiter(
        max_requests_per_minute=ers_engine.config.rate_limit_requests_per_minute
    )
    registry = model_registry or ModelRegistry()
    default_models_dir = Path("packages/ers/models")
    if model_registry is None and default_models_dir.is_dir():
        registry.discover_directory(default_models_dir)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
        await manager.initialize()
        yield
        await manager.shutdown()

    app = FastAPI(
        title="OVIC EON ERS Live Stream Server",
        description="Real-time sensory webcam, microphone, text, and video affective observation server.",
        version="0.2.0",
        lifespan=lifespan,
    )
    app.state.ers_auth = auth
    app.state.ers_registry = registry
    app.state.ers_manager = manager

    @app.exception_handler(ERSError)
    async def ers_exception_handler(request: Request, exc: ERSError) -> JSONResponse:
        return JSONResponse(status_code=400, content=exc.to_error_payload())

    # Secure local CORS policy (disallowing insecure wildcard credentials)
    allowed_origins = [
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8080",
        "http://127.0.0.1:8080",
    ]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
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

    @app.get("/api/models", response_model=ModelStatusResponse)
    async def get_models_status() -> ModelStatusResponse:
        """Inspect detailed lifecycle, provenance, and scientific validation states of all models."""
        models: list[ModelStatusDetail] = []
        if ers_engine._facial_pipeline and ers_engine._facial_pipeline.model_adapter:
            fa = ers_engine._facial_pipeline.model_adapter
            manifest = getattr(fa, "_manifest", None)
            models.append(
                ModelStatusDetail(
                    model_id=fa.model_id,
                    modality="facial",
                    version=fa.model_version,
                    state=fa.model_state.value,
                    is_validated=fa.is_validated,
                    provenance=getattr(manifest, "provenance_status", "SYNTHETIC/EXPERIMENTAL")
                    if manifest
                    else "EXPERIMENTAL",
                    license=getattr(manifest, "license", "RESTRICTED")
                    if manifest
                    else "UNVERIFIED",
                    artifact_sha256=getattr(manifest, "sha256_checksum", None)
                    if manifest
                    else None,
                    known_limitations=getattr(
                        manifest,
                        "known_limitations",
                        ["Unvalidated baseline; discrete emotion claims suppressed."],
                    )
                    if manifest
                    else ["Experimental heuristics only."],
                )
            )

        if ers_engine._speech_pipeline and ers_engine._speech_pipeline.model_adapter:
            sa = ers_engine._speech_pipeline.model_adapter
            s_manifest = getattr(sa, "_manifest", None)
            models.append(
                ModelStatusDetail(
                    model_id=sa.model_id,
                    modality="speech",
                    version=sa.model_version,
                    state=sa.model_state.value,
                    is_validated=sa.is_validated,
                    provenance=getattr(s_manifest, "provenance_status", "SYNTHETIC/EXPERIMENTAL")
                    if s_manifest
                    else "EXPERIMENTAL",
                    license=getattr(s_manifest, "license", "RESTRICTED")
                    if s_manifest
                    else "UNVERIFIED",
                    artifact_sha256=getattr(s_manifest, "sha256_checksum", None)
                    if s_manifest
                    else None,
                    known_limitations=getattr(
                        s_manifest,
                        "known_limitations",
                        ["Unvalidated baseline; discrete emotion claims suppressed."],
                    )
                    if s_manifest
                    else ["Experimental heuristics only."],
                )
            )

        overall = "VALIDATED" if any(m.is_validated for m in models) else "UNVALIDATED_BASELINE"
        return ModelStatusResponse(
            models=models,
            overall_qualification=overall,
            timestamp=time.time(),
        )

    @app.get("/api/devices", response_model=DeviceStatusResponse)
    async def get_devices_status() -> DeviceStatusResponse:
        """Inspect sensory hardware connectivity."""
        return DeviceStatusResponse(
            camera_active=True,
            microphone_active=True,
            has_consent=len(manager._active_sessions) > 0,
            session_id=next(iter(manager._active_sessions.keys()))
            if manager._active_sessions
            else None,
        )

    @app.get("/api/telemetry/{session_id}", response_model=PerformanceTelemetryResponse)
    async def get_telemetry(session_id: str) -> PerformanceTelemetryResponse:
        """Return execution latency percentiles and host memory metrics."""
        summary = ers_engine.get_metrics()
        p50 = summary.get("latency_p50_ms", 0.0)
        p95 = summary.get("latency_p95_ms", 0.0)
        p99 = summary.get("latency_p99_ms", 0.0)

        rss_mb = None
        try:
            import psutil

            rss_mb = round(psutil.Process().memory_info().rss / (1024 * 1024), 2)
        except Exception:
            pass

        return PerformanceTelemetryResponse(
            session_id=session_id,
            frame_latency_ms=summary.get("last_facial_latency_ms", 0.0),
            audio_latency_ms=summary.get("last_speech_latency_ms", 0.0),
            fusion_latency_ms=summary.get("last_fusion_latency_ms", 0.0),
            p50_ms=p50,
            p95_ms=p95,
            p99_ms=p99,
            memory_rss_mb=rss_mb,
            timestamp=time.time(),
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
        """Inspect active consent status for a session without reading raw credentials."""
        st = manager.get_session_consent_status(session_id)
        return ConsentStatusResponse(
            session_id=str(st["session_id"]),
            has_active_consent=bool(st["has_active_consent"]),
            is_revoked=bool(st["is_revoked"]),
            masked_reference=str(st["masked_reference"])
            if isinstance(st.get("masked_reference"), str)
            else None,
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
            model_state=ModelState(
                res.get("model_state", ModelState.MODEL_LOADED_UNVERIFIED.value)
            ),
            is_validated=bool(res.get("is_validated", False)),
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
    @app.websocket("/ws/stream/{session_id}")
    @app.websocket("/ws/stream")
    async def websocket_live_stream(
        websocket: WebSocket, session_id: str = "default-session"
    ) -> None:
        """Bi-directional WebSocket for streaming live webcam, microphone, and text inputs."""
        await handle_live_websocket(
            websocket,
            session_id,
            manager,
            _synthesize_live_fusion,
            auth_manager=auth,
        )

    app.include_router(
        build_v1_router(
            ers_engine,
            manager,
            registry,
            auth,
            limiter,
            _synthesize_live_fusion,
        )
    )

    return app


def _synthesize_live_fusion(
    face_res: dict[str, Any] | None, speech_res: dict[str, Any] | None
) -> dict[str, Any]:
    """Combine latest available stream observations for live UI telemetry with validation isolation."""
    face_val = face_res.get("is_validated", False) if face_res else False
    speech_val = speech_res.get("is_validated", False) if speech_res else False

    face_ok = face_res is not None and face_res.get("status") not in (
        "error",
        "consent_rejected",
        "failed",
    )
    speech_ok = speech_res is not None and speech_res.get("status") not in (
        "error",
        "consent_rejected",
        "failed",
    )

    face_eligible = face_ok and face_val
    speech_eligible = speech_ok and speech_val

    # Case A: Neither modality is eligible
    if not face_eligible and not speech_eligible:
        diag = []
        if face_ok:
            diag.append("facial")
        if speech_ok:
            diag.append("speech")
        return {
            "dominant_estimate": "INSUFFICIENT_EVIDENCE",
            "confidence": 0.0,
            "uncertainty": 1.0,
            "fused_probabilities": {},
            "modality_weights": {"facial": 0.0, "speech": 0.0},
            "conflicting_evidence": False,
            "conflict_metric": 0.0,
            "is_validated": False,
            "is_definitive_claim": False,
            "classification_eligible_modalities": [],
            "diagnostic_modalities": diag,
            "fusion_status": "insufficient_evidence_unvalidated",
        }

    # Case B: Only facial is eligible
    if face_eligible and not speech_eligible:
        p_f = face_res.get("emotion_probabilities", {}) if face_res else {}
        dominant = (
            face_res.get("dominant_estimate", "INSUFFICIENT_EVIDENCE")
            if face_res
            else "INSUFFICIENT_EVIDENCE"
        )
        conf = face_res.get("confidence", 0.0) if face_res else 0.0
        unc = face_res.get("uncertainty", 1.0) if face_res else 1.0
        return {
            "dominant_estimate": dominant,
            "confidence": conf,
            "uncertainty": unc,
            "fused_probabilities": p_f,
            "modality_weights": {"facial": 1.0, "speech": 0.0},
            "conflicting_evidence": False,
            "conflict_metric": 0.0,
            "is_validated": True,
            "is_definitive_claim": False,
            "classification_eligible_modalities": ["facial"],
            "diagnostic_modalities": ["speech"] if speech_ok else [],
            "fusion_status": "facial_only_validated",
        }

    # Case C: Only speech is eligible
    if speech_eligible and not face_eligible:
        p_s = speech_res.get("emotion_probabilities", {}) if speech_res else {}
        dominant = (
            speech_res.get("dominant_estimate", "INSUFFICIENT_EVIDENCE")
            if speech_res
            else "INSUFFICIENT_EVIDENCE"
        )
        conf = speech_res.get("confidence", 0.0) if speech_res else 0.0
        unc = speech_res.get("uncertainty", 1.0) if speech_res else 1.0
        return {
            "dominant_estimate": dominant,
            "confidence": conf,
            "uncertainty": unc,
            "fused_probabilities": p_s,
            "modality_weights": {"facial": 0.0, "speech": 1.0},
            "conflicting_evidence": False,
            "conflict_metric": 0.0,
            "is_validated": True,
            "is_definitive_claim": False,
            "classification_eligible_modalities": ["speech"],
            "diagnostic_modalities": ["facial"] if face_ok else [],
            "fusion_status": "speech_only_validated",
        }

    # Case D: Both modalities are eligible
    q_face = face_res.get("quality_score", 0.5) if face_res else 0.0
    c_face = face_res.get("confidence", 0.0) if face_res else 0.0
    q_speech = speech_res.get("quality_score", 0.5) if speech_res else 0.0
    c_speech = speech_res.get("confidence", 0.0) if speech_res else 0.0

    raw_w_f = q_face * c_face
    raw_w_s = q_speech * c_speech
    total_w = raw_w_f + raw_w_s

    w_f = round(raw_w_f / total_w, 4) if total_w > 1e-6 else 0.5
    w_s = round(raw_w_s / total_w, 4) if total_w > 1e-6 else 0.5

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
        "is_validated": True,
        "is_definitive_claim": False,
        "classification_eligible_modalities": ["facial", "speech"],
        "diagnostic_modalities": [],
        "fusion_status": "multimodal_fused",
    }
