"""Versioned WebSocket streaming handler with bounded queue backpressure, auth, and heartbeats."""

from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import Any

from fastapi import WebSocket, WebSocketDisconnect

from eon_ers.api.authentication import APIKeyAuthManager, AuthenticatedPrincipal
from eon_ers.api.rate_limits import SlidingWindowRateLimiter
from eon_ers.core.version import ERS_WS_PROTOCOL_VERSION
from eon_ers.exceptions import ERSError, ERSPrivacyConsentError
from eon_ers.live.manager import LiveSessionManager
from eon_ers.live.session import LiveSessionState

logger = logging.getLogger("eon.ers.live.websocket")

MAX_WS_PAYLOAD_BYTES = 5 * 1024 * 1024
ALLOWED_WS_MESSAGE_TYPES: frozenset[str] = frozenset(
    {
        "auth",
        "init",
        "capabilities",
        "heartbeat",
        "ping",
        "media_state",
        "frame",
        "audio",
        "text",
        "multimodal",
        "pause",
        "resume",
        "revoke",
        "stop",
        "cancel",
    }
)


async def handle_live_websocket(
    websocket: WebSocket,
    session_id: str,
    manager: LiveSessionManager,
    fusion_synthesizer: Any,
    auth_manager: APIKeyAuthManager | None = None,
) -> None:
    """Handle versioned live streaming with explicit schemas, auth, rate limits, and backpressure."""
    principal: AuthenticatedPrincipal | None = None
    requires_auth = bool(auth_manager is not None and auth_manager.require_auth)

    if requires_auth and auth_manager is not None:
        api_key = websocket.headers.get("x-api-key")
        auth_hdr = websocket.headers.get("authorization")
        if api_key or auth_hdr:
            try:
                principal = auth_manager.authenticate(api_key=api_key, authorization=auth_hdr)
                auth_manager.authorize(principal, "analyze:run")
                rec = manager.get_live_session(session_id)
                if rec is not None:
                    auth_manager.authorize_session_owner(principal, rec.owner_id)
            except ERSError as exc:
                await websocket.close(code=4401, reason=exc.message[:100])
                return

    await websocket.accept()
    metrics = manager.engine.metrics
    metrics.record_ws_connect()

    max_q = manager.engine.config.max_ws_queue_size
    rate_limit = int(max(1.0, manager.engine.config.ws_max_messages_per_second * 60.0))
    limiter = SlidingWindowRateLimiter(max_requests_per_minute=rate_limit, window_seconds=60.0)
    queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=max_q)

    latest_face_res: dict[str, Any] | None = None
    latest_speech_res: dict[str, Any] | None = None
    paused = False

    async def worker() -> None:
        nonlocal latest_face_res, latest_speech_res
        while True:
            item = await queue.get()
            enqueued_at = float(item.get("_enqueued_at", time.perf_counter()))
            metrics.record_queue_delay((time.perf_counter() - enqueued_at) * 1000.0)
            msg_type = item["type"]
            payload = item["payload"]
            ref = payload.get("consent_reference")
            try:
                if msg_type == "frame":
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
                    if res.get("status") not in ("error", "consent_rejected"):
                        fused_update = fusion_synthesizer(latest_face_res, latest_speech_res)
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
                    sr = int(payload.get("sample_rate", 16000))
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
                    if res.get("status") not in ("error", "consent_rejected"):
                        fused_update = fusion_synthesizer(latest_face_res, latest_speech_res)
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
                elif msg_type == "text":
                    txt = payload.get("text", "")
                    if not txt:
                        continue
                    res = await manager.process_text(session_id, str(txt), ref)
                    await websocket.send_text(
                        json.dumps(
                            {
                                "type": "observation",
                                "session_id": session_id,
                                "timestamp": time.time(),
                                "modality": "text",
                                "data": res,
                                "latency_ms": res.get("latency_ms", 0.0),
                            }
                        )
                    )
                elif msg_type == "multimodal":
                    fused = await manager.process_multimodal_live(
                        session_id=session_id,
                        image_base64=payload.get("image_base64"),
                        audio_base64=payload.get("audio_base64"),
                        sample_rate=int(payload.get("sample_rate", 16000)),
                        consent_reference=ref,
                        text=payload.get("text"),
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
            except (WebSocketDisconnect, RuntimeError):
                break
            finally:
                queue.task_done()

    worker_task = asyncio.create_task(worker())
    try:
        while True:
            data_text = await websocket.receive_text()
            metrics.record_ws_message()

            if len(data_text.encode("utf-8")) > MAX_WS_PAYLOAD_BYTES:
                await websocket.send_text(
                    json.dumps(
                        {
                            "type": "error",
                            "error": f"Payload exceeds maximum allowed size of {MAX_WS_PAYLOAD_BYTES} bytes.",
                        }
                    )
                )
                continue

            try:
                limiter.check_and_record(session_id)
            except ERSError as exc:
                await websocket.send_text(json.dumps({"type": "error", "error": exc.message}))
                continue

            try:
                payload = json.loads(data_text)
                if not isinstance(payload, dict):
                    raise ValueError("Payload must be a JSON object.")
            except Exception:
                await websocket.send_text(
                    json.dumps({"type": "error", "error": "Invalid JSON format."})
                )
                continue

            msg_type = payload.get("type")
            if msg_type not in ALLOWED_WS_MESSAGE_TYPES:
                await websocket.send_text(
                    json.dumps(
                        {
                            "type": "error",
                            "error": f"Unsupported message type '{msg_type}'. Expected one of: {sorted(ALLOWED_WS_MESSAGE_TYPES)}.",
                        }
                    )
                )
                continue

            if msg_type == "auth":
                if auth_manager is not None:
                    try:
                        principal = auth_manager.authenticate(
                            api_key=payload.get("api_key"),
                            authorization=payload.get("authorization"),
                        )
                        auth_manager.authorize(principal, "analyze:run")
                        rec = manager.get_live_session(session_id)
                        if rec is not None:
                            auth_manager.authorize_session_owner(principal, rec.owner_id)
                    except ERSError as exc:
                        await websocket.send_text(
                            json.dumps({"type": "error", "error": exc.message})
                        )
                        await websocket.close(code=4401, reason=exc.message[:100])
                        break
                await websocket.send_text(
                    json.dumps(
                        {
                            "type": "status",
                            "status": "authenticated",
                            "session_id": session_id,
                        }
                    )
                )
                continue

            if requires_auth and principal is None:
                await websocket.send_text(
                    json.dumps(
                        {
                            "type": "error",
                            "error": "WebSocket authentication required. Send {'type': 'auth', 'api_key': ...} or provide X-API-Key header.",
                        }
                    )
                )
                await websocket.close(code=4401, reason="Authentication required")
                break

            ref = payload.get("consent_reference")
            owner_id = principal.principal_id if principal is not None else "anonymous"

            if msg_type == "init":
                if ref:
                    try:
                        manager.register_session_consent(session_id, str(ref), owner_id=owner_id)
                    except ERSPrivacyConsentError as exc:
                        await websocket.send_text(
                            json.dumps({"type": "error", "error": exc.message})
                        )
                        continue
                await websocket.send_text(
                    json.dumps(
                        {
                            "type": "status",
                            "status": "session_initialized",
                            "protocol_version": ERS_WS_PROTOCOL_VERSION,
                            "session_id": session_id,
                            "has_active_consent": manager.has_active_consent(session_id),
                        }
                    )
                )
            elif msg_type == "capabilities":
                await websocket.send_text(
                    json.dumps(
                        {
                            "type": "capabilities",
                            "protocol_version": ERS_WS_PROTOCOL_VERSION,
                            "max_payload_bytes": MAX_WS_PAYLOAD_BYTES,
                            "max_queue_size": max_q,
                            "modalities": ["facial", "speech", "text", "multimodal"],
                            "session_id": session_id,
                        }
                    )
                )
            elif msg_type in ("heartbeat", "ping"):
                await websocket.send_text(
                    json.dumps(
                        {
                            "type": "pong",
                            "session_id": session_id,
                            "timestamp": time.time(),
                        }
                    )
                )
            elif msg_type == "media_state":
                manager.set_session_device_state(
                    session_id,
                    camera_active=payload.get("camera_active"),
                    microphone_active=payload.get("microphone_active"),
                )
                await websocket.send_text(
                    json.dumps(
                        {
                            "type": "status",
                            "status": "media_state_updated",
                            "session_id": session_id,
                        }
                    )
                )
            elif msg_type == "pause":
                paused = True
                rec = manager.get_live_session(session_id)
                if rec is not None and rec.state == LiveSessionState.STREAMING:
                    rec.transition_to(LiveSessionState.PAUSED)
                manager.set_session_device_state(
                    session_id, camera_active=False, microphone_active=False
                )
                await websocket.send_text(
                    json.dumps({"type": "status", "status": "paused", "session_id": session_id})
                )
            elif msg_type == "resume":
                paused = False
                rec = manager.get_live_session(session_id)
                if rec is not None and rec.state == LiveSessionState.PAUSED:
                    rec.transition_to(LiveSessionState.STREAMING)
                await websocket.send_text(
                    json.dumps({"type": "status", "status": "resumed", "session_id": session_id})
                )
            elif msg_type == "revoke":
                manager.revoke_session_consent(session_id)
                latest_face_res = None
                latest_speech_res = None
                while not queue.empty():
                    try:
                        queue.get_nowait()
                        queue.task_done()
                    except asyncio.QueueEmpty:
                        break
                await websocket.send_text(
                    json.dumps(
                        {
                            "type": "status",
                            "status": "consent_revoked",
                            "session_id": session_id,
                        }
                    )
                )
            elif msg_type in ("stop", "cancel"):
                manager.set_session_device_state(
                    session_id, camera_active=False, microphone_active=False
                )
                await websocket.send_text(
                    json.dumps({"type": "status", "status": "stopped", "session_id": session_id})
                )
                break
            else:
                if paused:
                    metrics.record_dropped_frame()
                    continue
                if queue.full():
                    metrics.record_dropped_frame()
                    rec = manager.get_live_session(session_id)
                    if rec is not None:
                        rec.dropped_frames += 1
                    try:
                        queue.get_nowait()
                        queue.task_done()
                    except asyncio.QueueEmpty:
                        pass
                await queue.put(
                    {"type": msg_type, "payload": payload, "_enqueued_at": time.perf_counter()}
                )
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected for session '%s'.", session_id)
    except Exception as exc:
        logger.error("WebSocket exception on session '%s': %s", session_id, exc, exc_info=True)
    finally:
        worker_task.cancel()
        manager.set_session_device_state(session_id, camera_active=False, microphone_active=False)
        metrics.record_ws_disconnect()
