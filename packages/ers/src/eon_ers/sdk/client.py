"""Developer Python SDK for local or remote OVIC EON ERS integration."""

from __future__ import annotations

import base64
from typing import Any

import httpx

from eon_ers.config import ERSConfig
from eon_ers.contracts import EmotionObservation, ERSInput, FusionResult
from eon_ers.engine import ERSEngine
from eon_ers.types import Modality


class ERSClient:
    """Unified developer client supporting both local `ERSEngine` and HTTP `/api/v1/*` servers."""

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        *,
        engine: ERSEngine | None = None,
        config: ERSConfig | None = None,
        timeout: float = 15.0,
    ) -> None:
        self.base_url = base_url.rstrip("/") if base_url else None
        self.api_key = api_key
        self._timeout = timeout
        self._engine = engine or (ERSEngine(config) if self.base_url is None else None)
        self._http: httpx.AsyncClient | None = None

    async def __aenter__(self) -> ERSClient:
        if self._engine is not None and not self._engine.is_running:
            await self._engine.start()
        if self.base_url is not None and self._http is None:
            headers = {"X-API-Key": self.api_key} if self.api_key else {}
            self._http = httpx.AsyncClient(
                base_url=self.base_url, headers=headers, timeout=self._timeout
            )
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if self._http is not None:
            await self._http.aclose()
            self._http = None
        if self._engine is not None and self._engine.is_running:
            await self._engine.close()

    async def register_consent(self, session_id: str, consent_reference: str) -> dict[str, Any]:
        if self._engine is not None:
            self._engine.register_consent(session_id, consent_reference)
            return {"status": "registered", "session_id": session_id}
        assert self._http is not None
        resp = await self._http.post(
            "/api/v1/consent",
            json={"session_id": session_id, "consent_reference": consent_reference},
        )
        resp.raise_for_status()
        return dict(resp.json())

    async def revoke_consent(self, session_id: str) -> dict[str, Any]:
        if self._engine is not None:
            self._engine.revoke_consent(session_id)
            return {"status": "revoked", "session_id": session_id}
        assert self._http is not None
        resp = await self._http.delete(f"/api/v1/consent/{session_id}")
        resp.raise_for_status()
        return dict(resp.json())

    async def analyze_image(
        self, session_id: str, consent_reference: str, image_bytes: bytes
    ) -> EmotionObservation | dict[str, Any]:
        if self._engine is not None:
            return await self._engine.process_facial(
                ERSInput(
                    session_id=session_id,
                    modality=Modality.FACIAL,
                    consent_reference=consent_reference,
                    image_payload=image_bytes,
                )
            )
        assert self._http is not None
        b64 = base64.b64encode(image_bytes).decode("ascii")
        resp = await self._http.post(
            "/api/v1/analyze/image",
            json={
                "session_id": session_id,
                "consent_reference": consent_reference,
                "modality": "facial",
                "image_base64": b64,
            },
        )
        resp.raise_for_status()
        return dict(resp.json())

    async def analyze_audio(
        self,
        session_id: str,
        consent_reference: str,
        audio_bytes: bytes,
        *,
        sample_rate: int = 16000,
    ) -> EmotionObservation | dict[str, Any]:
        """Analyze a mono signed 16-bit little-endian PCM chunk."""
        if self._engine is not None:
            return await self._engine.process_speech(
                ERSInput(
                    session_id=session_id,
                    modality=Modality.SPEECH,
                    consent_reference=consent_reference,
                    audio_payload=audio_bytes,
                    sample_rate=sample_rate,
                )
            )
        assert self._http is not None
        resp = await self._http.post(
            "/api/v1/analyze/audio",
            json={
                "session_id": session_id,
                "consent_reference": consent_reference,
                "modality": Modality.SPEECH.value,
                "audio_base64": base64.b64encode(audio_bytes).decode("ascii"),
                "sample_rate": sample_rate,
            },
        )
        resp.raise_for_status()
        return dict(resp.json())

    async def analyze_text(
        self, session_id: str, consent_reference: str, text: str
    ) -> EmotionObservation | dict[str, Any]:
        if self._engine is not None:
            return await self._engine.process_text(
                ERSInput(
                    session_id=session_id,
                    modality=Modality.TEXT,
                    consent_reference=consent_reference,
                    text_payload=text,
                )
            )
        assert self._http is not None
        resp = await self._http.post(
            "/api/v1/analyze/text",
            json={
                "session_id": session_id,
                "consent_reference": consent_reference,
                "text": text,
            },
        )
        resp.raise_for_status()
        return dict(resp.json())

    async def analyze_multimodal(
        self,
        session_id: str,
        consent_reference: str,
        *,
        image_bytes: bytes | None = None,
        audio_bytes: bytes | None = None,
        sample_rate: int = 16000,
        text: str | None = None,
    ) -> FusionResult | dict[str, Any]:
        if self._engine is not None:
            f_in = (
                ERSInput(
                    session_id=session_id,
                    modality=Modality.FACIAL,
                    consent_reference=consent_reference,
                    image_payload=image_bytes,
                )
                if image_bytes is not None
                else None
            )
            s_in = (
                ERSInput(
                    session_id=session_id,
                    modality=Modality.SPEECH,
                    consent_reference=consent_reference,
                    audio_payload=audio_bytes,
                    sample_rate=sample_rate,
                )
                if audio_bytes is not None
                else None
            )
            t_in = (
                ERSInput(
                    session_id=session_id,
                    modality=Modality.TEXT,
                    consent_reference=consent_reference,
                    text_payload=text,
                )
                if text is not None
                else None
            )
            return await self._engine.process_multimodal(f_in, s_in, text_input=t_in)

        assert self._http is not None
        payload: dict[str, Any] = {
            "session_id": session_id,
            "consent_reference": consent_reference,
            "sample_rate": sample_rate,
        }
        if image_bytes is not None:
            payload["image_base64"] = base64.b64encode(image_bytes).decode("ascii")
        if audio_bytes is not None:
            payload["audio_base64"] = base64.b64encode(audio_bytes).decode("ascii")
        if text is not None:
            payload["text"] = text
        resp = await self._http.post("/api/v1/analyze/multimodal", json=payload)
        resp.raise_for_status()
        return dict(resp.json())
