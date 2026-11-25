"""Versioned REST & WebSocket API router for OVIC EON ERS (`/api/v1/*` and system endpoints)."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, WebSocket
from fastapi.responses import JSONResponse, PlainTextResponse

from eon_ers.api.authentication import APIKeyAuthManager, AuthenticatedPrincipal
from eon_ers.api.rate_limits import SlidingWindowRateLimiter
from eon_ers.api.schemas import (
    ConsentRegisterRequest,
    CreateLiveSessionRequest,
    MultimodalAnalyzeRequest,
    ProcessObservationRequest,
    TextAnalyzeRequest,
    VideoAnalyzeRequest,
)
from eon_ers.core.health import get_liveness_status, get_readiness_status
from eon_ers.core.version import get_version_info
from eon_ers.engine import ERSEngine
from eon_ers.evaluation.dataset import KNOWN_DATASET_PROVENANCE
from eon_ers.exceptions import ERSError
from eon_ers.live.manager import LiveSessionManager
from eon_ers.live.session import LiveSessionState
from eon_ers.live.websocket import handle_live_websocket
from eon_ers.models.registry import ModelRegistry
from eon_ers.monitoring.diagnostics import collect_system_diagnostics


def build_v1_router(
    engine: ERSEngine,
    manager: LiveSessionManager,
    registry: ModelRegistry,
    auth_manager: APIKeyAuthManager,
    rate_limiter: SlidingWindowRateLimiter,
    fusion_synthesizer: Any,
) -> APIRouter:
    """Construct complete system and `/api/v1` router enforcing auth, RBAC, and rate limits."""
    router = APIRouter()

    def get_principal(
        request: Request,
        x_api_key: str | None = Header(default=None, alias="X-API-Key"),
        authorization: str | None = Header(default=None, alias="Authorization"),
    ) -> AuthenticatedPrincipal:
        try:
            principal = auth_manager.authenticate(api_key=x_api_key, authorization=authorization)
            client_id = (
                principal.key_id
                if principal.authenticated
                else (request.client.host if request.client else "anonymous")
            )
            rate_limiter.check_and_record(client_id)
            return principal
        except ERSError as exc:
            status = 429 if "RATE_LIMIT" in exc.error_code else 401
            raise HTTPException(status_code=status, detail=exc.to_error_payload()["error"]) from exc

    def _require_perm(principal: AuthenticatedPrincipal, perm: str) -> None:
        try:
            auth_manager.authorize(principal, perm)
        except ERSError as exc:
            raise HTTPException(status_code=403, detail=exc.to_error_payload()["error"]) from exc

    # ---- System Endpoints ----

    @router.get("/health")
    async def system_health() -> dict[str, Any]:
        return get_liveness_status(engine)

    @router.get("/ready")
    async def system_ready() -> dict[str, Any]:
        return get_readiness_status(engine)

    @router.get("/version")
    async def system_version() -> dict[str, Any]:
        return get_version_info()

    @router.get("/capabilities")
    async def system_capabilities() -> dict[str, Any]:
        return {
            "modalities": {
                "facial": engine.config.enable_facial,
                "speech": engine.config.enable_speech,
                "text": engine.config.enable_text,
                "video": engine.config.enable_video,
                "multimodal": engine.config.enable_multimodal_fusion,
            },
            "execution_mode": "cpu_first_local",
            "auth_required": auth_manager.require_auth,
            "limits": {
                "max_image_bytes": engine.config.max_image_bytes,
                "max_audio_bytes": engine.config.max_audio_bytes,
                "max_text_length": engine.config.max_text_length,
                "video_max_bytes": engine.config.video_max_bytes,
                "video_max_frames": engine.config.video_max_frames,
            },
            "readiness": get_readiness_status(engine),
        }

    @router.get("/metrics", response_model=None)
    async def system_metrics(
        format: str = Query(default="json", pattern="^(json|prometheus)$"),
    ) -> JSONResponse | PlainTextResponse:
        if format == "prometheus":
            return PlainTextResponse(
                engine.metrics.render_prometheus(), media_type="text/plain; version=0.0.4"
            )
        return JSONResponse(engine.metrics.get_summary())

    # ---- Models ----

    @router.get("/api/v1/models")
    async def list_v1_models(
        principal: AuthenticatedPrincipal = Depends(get_principal),
    ) -> dict[str, Any]:
        _require_perm(principal, "models:read")
        entries = [e.to_dict() for e in registry.list_entries()]
        return {
            "models": entries,
            "total": len(entries),
            "validated_count": sum(1 for e in entries if e["is_validated"]),
        }

    @router.get("/api/v1/models/{model_id}")
    async def get_v1_model(
        model_id: str,
        principal: AuthenticatedPrincipal = Depends(get_principal),
    ) -> dict[str, Any]:
        _require_perm(principal, "models:read")
        entry = registry.get_entry(model_id)
        if entry is None:
            raise HTTPException(status_code=404, detail=f"Model '{model_id}' not found.")
        return entry.to_dict()

    @router.get("/api/v1/models/{model_id}/status")
    async def get_v1_model_status(
        model_id: str,
        principal: AuthenticatedPrincipal = Depends(get_principal),
    ) -> dict[str, Any]:
        _require_perm(principal, "models:read")
        entry = registry.get_entry(model_id)
        if entry is None:
            raise HTTPException(status_code=404, detail=f"Model '{model_id}' not found.")
        return {
            "model_id": entry.manifest.model_id,
            "qualification_state": entry.qualification_state.value,
            "is_validated": entry.qualification_state.value == "MODEL_VALIDATED",
            "activated": entry.activated,
            "activation_eligible": entry.qualification_state.value == "MODEL_VALIDATED",
            "rejection_reasons": entry.rejection_reasons,
            "revocation_reason": entry.revocation_reason,
        }

    @router.post("/api/v1/models/{model_id}/activate")
    async def activate_v1_model(
        model_id: str,
        principal: AuthenticatedPrincipal = Depends(get_principal),
    ) -> dict[str, Any]:
        _require_perm(principal, "models:manage")
        try:
            entry = registry.activate_model(model_id)
            return {"status": "activated", "model": entry.to_dict()}
        except ERSError as exc:
            raise HTTPException(status_code=409, detail=exc.to_error_payload()["error"]) from exc

    # ---- Analysis Endpoints ----

    async def _analyze_facial_impl(
        req: ProcessObservationRequest, principal: AuthenticatedPrincipal
    ) -> dict[str, Any]:
        _require_perm(principal, "analyze:run")
        rec = manager.get_live_session(req.session_id)
        if rec is not None:
            try:
                auth_manager.authorize_session_owner(principal, rec.owner_id)
            except ERSError as exc:
                raise HTTPException(
                    status_code=403, detail=exc.to_error_payload()["error"]
                ) from exc
        if not req.image_base64:
            raise HTTPException(status_code=400, detail="Missing image_base64 payload.")
        return await manager.process_frame(req.session_id, req.image_base64, req.consent_reference)

    @router.post("/api/v1/analyze/image")
    async def analyze_image_v1(
        req: ProcessObservationRequest,
        principal: AuthenticatedPrincipal = Depends(get_principal),
    ) -> dict[str, Any]:
        return await _analyze_facial_impl(req, principal)

    @router.post("/api/v1/analyze/facial")
    async def analyze_facial_v1(
        req: ProcessObservationRequest,
        principal: AuthenticatedPrincipal = Depends(get_principal),
    ) -> dict[str, Any]:
        return await _analyze_facial_impl(req, principal)

    async def _analyze_vocal_impl(
        req: ProcessObservationRequest, principal: AuthenticatedPrincipal
    ) -> dict[str, Any]:
        _require_perm(principal, "analyze:run")
        rec = manager.get_live_session(req.session_id)
        if rec is not None:
            try:
                auth_manager.authorize_session_owner(principal, rec.owner_id)
            except ERSError as exc:
                raise HTTPException(
                    status_code=403, detail=exc.to_error_payload()["error"]
                ) from exc
        if not req.audio_base64:
            raise HTTPException(status_code=400, detail="Missing audio_base64 payload.")
        return await manager.process_audio(
            req.session_id, req.audio_base64, req.sample_rate or 16000, req.consent_reference
        )

    @router.post("/api/v1/analyze/audio")
    async def analyze_audio_v1(
        req: ProcessObservationRequest,
        principal: AuthenticatedPrincipal = Depends(get_principal),
    ) -> dict[str, Any]:
        return await _analyze_vocal_impl(req, principal)

    @router.post("/api/v1/analyze/vocal")
    async def analyze_vocal_v1(
        req: ProcessObservationRequest,
        principal: AuthenticatedPrincipal = Depends(get_principal),
    ) -> dict[str, Any]:
        return await _analyze_vocal_impl(req, principal)

    @router.post("/api/v1/analyze/text")
    async def analyze_text_v1(
        req: TextAnalyzeRequest,
        principal: AuthenticatedPrincipal = Depends(get_principal),
    ) -> dict[str, Any]:
        _require_perm(principal, "analyze:run")
        rec = manager.get_live_session(req.session_id)
        if rec is not None:
            try:
                auth_manager.authorize_session_owner(principal, rec.owner_id)
            except ERSError as exc:
                raise HTTPException(
                    status_code=403, detail=exc.to_error_payload()["error"]
                ) from exc
        return await manager.process_text(req.session_id, req.text, req.consent_reference)

    @router.post("/api/v1/analyze/video")
    async def analyze_video_v1(
        req: VideoAnalyzeRequest,
        principal: AuthenticatedPrincipal = Depends(get_principal),
    ) -> dict[str, Any]:
        _require_perm(principal, "analyze:run")
        try:
            res = await manager.submit_video_job(
                req.session_id, req.video_base64, req.consent_reference
            )
            return res.model_dump()
        except ERSError as exc:
            status_code = 403 if "CONSENT" in exc.error_code else 400
            raise HTTPException(
                status_code=status_code, detail=exc.to_error_payload()["error"]
            ) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.get("/api/v1/analyze/video/{job_id}")
    async def get_video_job_v1(
        job_id: str,
        principal: AuthenticatedPrincipal = Depends(get_principal),
    ) -> dict[str, Any]:
        _require_perm(principal, "analyze:run")
        job = manager.get_video_job(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail=f"Video job '{job_id}' not found.")
        return job.model_dump()

    @router.delete("/api/v1/analyze/video/{job_id}")
    async def cancel_video_job_v1(
        job_id: str,
        principal: AuthenticatedPrincipal = Depends(get_principal),
    ) -> dict[str, Any]:
        _require_perm(principal, "analyze:run")
        cancelled = manager.cancel_video_job(job_id)
        if not cancelled:
            raise HTTPException(status_code=404, detail=f"Video job '{job_id}' not found.")
        return {"job_id": job_id, "cancelled": True}

    @router.post("/api/v1/analyze/multimodal")
    async def analyze_multimodal_v1(
        req: MultimodalAnalyzeRequest,
        principal: AuthenticatedPrincipal = Depends(get_principal),
    ) -> dict[str, Any]:
        _require_perm(principal, "analyze:run")
        if req.image_base64 is None and req.audio_base64 is None and req.text is None:
            raise HTTPException(
                status_code=400,
                detail="At least one modality payload (image_base64, audio_base64, text) is required.",
            )
        return await manager.process_multimodal_live(
            session_id=req.session_id,
            image_base64=req.image_base64,
            audio_base64=req.audio_base64,
            sample_rate=req.sample_rate,
            consent_reference=req.consent_reference,
            text=req.text,
        )

    # ---- Live Sessions ----

    @router.post("/api/v1/live/sessions")
    async def create_live_session_v1(
        req: CreateLiveSessionRequest,
        principal: AuthenticatedPrincipal = Depends(get_principal),
    ) -> dict[str, Any]:
        _require_perm(principal, "sessions:manage")
        rec = manager.create_live_session(
            session_id=req.session_id or f"live-{uuid.uuid4().hex[:10]}",
            owner_id=principal.principal_id,
            consent_reference=req.consent_reference,
            consent_scope=req.consent_scope,
            history_opt_in=req.history_opt_in,
            ttl_seconds=req.ttl_seconds,
        )
        return rec.to_public_dict()

    @router.get("/api/v1/live/sessions")
    async def list_live_sessions_v1(
        principal: AuthenticatedPrincipal = Depends(get_principal),
    ) -> dict[str, Any]:
        _require_perm(principal, "sessions:manage")
        owner_filter = None if principal.role.value == "admin" else principal.principal_id
        sessions = [s.to_public_dict() for s in manager.list_live_sessions(owner_id=owner_filter)]
        return {"sessions": sessions, "total": len(sessions)}

    @router.get("/api/v1/live/sessions/{session_id}")
    async def get_live_session_v1(
        session_id: str,
        principal: AuthenticatedPrincipal = Depends(get_principal),
    ) -> dict[str, Any]:
        _require_perm(principal, "sessions:manage")
        rec = manager.get_live_session(session_id)
        if rec is None:
            raise HTTPException(status_code=404, detail=f"Live session '{session_id}' not found.")
        try:
            auth_manager.authorize_session_owner(principal, rec.owner_id)
        except ERSError as exc:
            raise HTTPException(status_code=403, detail=exc.to_error_payload()["error"]) from exc
        data = rec.to_public_dict()
        if rec.history_opt_in:
            data["history"] = list(rec.history)
        return data

    @router.post("/api/v1/live/sessions/{session_id}/pause")
    async def pause_live_session_v1(
        session_id: str,
        principal: AuthenticatedPrincipal = Depends(get_principal),
    ) -> dict[str, Any]:
        _require_perm(principal, "sessions:manage")
        rec = manager.get_live_session(session_id)
        if rec is None:
            raise HTTPException(status_code=404, detail=f"Live session '{session_id}' not found.")
        try:
            auth_manager.authorize_session_owner(principal, rec.owner_id)
            rec.transition_to(LiveSessionState.PAUSED)
        except ERSError as exc:
            status = 403 if "AUTHORIZATION" in exc.error_code else 409
            raise HTTPException(status_code=status, detail=exc.to_error_payload()["error"]) from exc
        return rec.to_public_dict()

    @router.post("/api/v1/live/sessions/{session_id}/resume")
    async def resume_live_session_v1(
        session_id: str,
        principal: AuthenticatedPrincipal = Depends(get_principal),
    ) -> dict[str, Any]:
        _require_perm(principal, "sessions:manage")
        rec = manager.get_live_session(session_id)
        if rec is None:
            raise HTTPException(status_code=404, detail=f"Live session '{session_id}' not found.")
        try:
            auth_manager.authorize_session_owner(principal, rec.owner_id)
            target = LiveSessionState.READY if rec.state == LiveSessionState.PAUSED else rec.state
            rec.transition_to(target)
        except ERSError as exc:
            status = 403 if "AUTHORIZATION" in exc.error_code else 409
            raise HTTPException(status_code=status, detail=exc.to_error_payload()["error"]) from exc
        return rec.to_public_dict()

    @router.delete("/api/v1/live/sessions/{session_id}")
    async def delete_live_session_v1(
        session_id: str,
        principal: AuthenticatedPrincipal = Depends(get_principal),
    ) -> dict[str, Any]:
        _require_perm(principal, "sessions:manage")
        rec = manager.get_live_session(session_id)
        if rec is not None:
            try:
                auth_manager.authorize_session_owner(principal, rec.owner_id)
            except ERSError as exc:
                raise HTTPException(
                    status_code=403, detail=exc.to_error_payload()["error"]
                ) from exc
        existed = manager.delete_live_session(session_id)
        if not existed:
            raise HTTPException(status_code=404, detail=f"Live session '{session_id}' not found.")
        return {"session_id": session_id, "status": "closed"}

    @router.websocket("/api/v1/live/sessions/{session_id}/stream")
    async def websocket_v1_stream(websocket: WebSocket, session_id: str) -> None:
        await handle_live_websocket(
            websocket,
            session_id,
            manager,
            fusion_synthesizer,
            auth_manager=auth_manager,
        )

    # ---- Consent ----

    @router.post("/api/v1/consent")
    async def register_consent_v1(
        req: ConsentRegisterRequest,
        principal: AuthenticatedPrincipal = Depends(get_principal),
    ) -> dict[str, Any]:
        _require_perm(principal, "consent:manage")
        rec = manager.get_live_session(req.session_id)
        if rec is not None:
            try:
                auth_manager.authorize_session_owner(principal, rec.owner_id)
            except ERSError as exc:
                raise HTTPException(
                    status_code=403, detail=exc.to_error_payload()["error"]
                ) from exc
        try:
            manager.register_session_consent(
                req.session_id, req.consent_reference, owner_id=principal.principal_id
            )
            return {
                "status": "registered",
                "session_id": req.session_id,
                "has_active_consent": True,
                "is_revoked": False,
            }
        except ERSError as exc:
            raise HTTPException(status_code=400, detail=exc.to_error_payload()["error"]) from exc

    @router.get("/api/v1/consent/{session_id}")
    async def get_consent_v1(
        session_id: str,
        principal: AuthenticatedPrincipal = Depends(get_principal),
    ) -> dict[str, Any]:
        _require_perm(principal, "consent:manage")
        rec = manager.get_live_session(session_id)
        if rec is not None:
            try:
                auth_manager.authorize_session_owner(principal, rec.owner_id)
            except ERSError as exc:
                raise HTTPException(
                    status_code=403, detail=exc.to_error_payload()["error"]
                ) from exc
        return manager.get_session_consent_status(session_id)

    @router.delete("/api/v1/consent/{session_id}")
    async def revoke_consent_v1(
        session_id: str,
        principal: AuthenticatedPrincipal = Depends(get_principal),
    ) -> dict[str, Any]:
        _require_perm(principal, "consent:manage")
        rec = manager.get_live_session(session_id)
        if rec is not None:
            try:
                auth_manager.authorize_session_owner(principal, rec.owner_id)
            except ERSError as exc:
                raise HTTPException(
                    status_code=403, detail=exc.to_error_payload()["error"]
                ) from exc
        manager.revoke_session_consent(session_id)
        return {
            "status": "revoked",
            "session_id": session_id,
            "has_active_consent": False,
            "is_revoked": True,
        }

    # ---- Diagnostics, Datasets & Evaluation Reports (UI & Ops integration) ----

    @router.get("/api/v1/diagnostics")
    async def get_v1_diagnostics(
        principal: AuthenticatedPrincipal = Depends(get_principal),
    ) -> dict[str, Any]:
        _require_perm(principal, "health:read")
        return {
            "system": collect_system_diagnostics(),
            "metrics": engine.metrics.get_summary(),
            "readiness": get_readiness_status(engine),
            "version": get_version_info(),
        }

    @router.get("/api/v1/datasets")
    async def get_v1_datasets(
        principal: AuthenticatedPrincipal = Depends(get_principal),
    ) -> dict[str, Any]:
        _require_perm(principal, "models:read")
        return {
            "datasets": [
                {
                    "dataset_id": k,
                    **v.model_dump(),
                    "repository_status": "UNACQUIRED_BLOCKED" if not v.checksum else "REGISTERED",
                }
                for k, v in KNOWN_DATASET_PROVENANCE.items()
            ]
        }

    @router.get("/api/v1/evaluation/reports")
    async def get_v1_evaluation_reports(
        principal: AuthenticatedPrincipal = Depends(get_principal),
    ) -> dict[str, Any]:
        _require_perm(principal, "models:read")
        reports = []
        for entry in registry.list_entries():
            if entry.validation_record is not None:
                reports.append(
                    {
                        "model_id": entry.manifest.model_id,
                        "qualification_state": entry.qualification_state.value,
                        "record": entry.validation_record.model_dump(),
                    }
                )
        return {"reports": reports, "total": len(reports)}

    return router
