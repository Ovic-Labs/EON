"""Regression coverage for the distributed SDK entry point and standalone audio."""

from functools import partial

import httpx
import pytest
from eon_ers.exceptions import ERSPrivacyConsentError
from eon_ers.live.server import create_live_app
from eon_ers.sdk import ERSClient as LegacyERSClient

from ovic_eon.ers import EmotionObservation, ERSClient, ERSConfig, ERSEngine

# Half a second of silent, mono PCM16.
SILENCE = bytes(16_000)


async def test_local_sdk_audio_requires_consent() -> None:
    assert ERSClient is LegacyERSClient
    async with ERSClient() as sdk:
        with pytest.raises(ERSPrivacyConsentError):
            await sdk.analyze_audio("sdk-local", "token", SILENCE)
        await sdk.register_consent("sdk-local", "token")
        result = await sdk.analyze_audio("sdk-local", "token", SILENCE)
        assert isinstance(result, EmotionObservation)
        assert result.modality.value == "speech"
        assert result.dominant_estimate == "insufficient_evidence"
        assert result.is_definitive_claim is False


async def test_remote_sdk_audio_uses_versioned_api(monkeypatch: pytest.MonkeyPatch) -> None:
    engine = ERSEngine(ERSConfig())
    app = create_live_app(engine=engine)
    transport = httpx.ASGITransport(app=app)
    monkeypatch.setattr(
        "eon_ers.sdk.client.httpx.AsyncClient", partial(httpx.AsyncClient, transport=transport)
    )

    async with app.router.lifespan_context(app), ERSClient(base_url="http://test") as sdk:
        await sdk.register_consent("sdk-remote", "token")
        result = await sdk.analyze_audio("sdk-remote", "token", SILENCE, sample_rate=16000)
        assert isinstance(result, dict)
        assert result["modality"] == "speech"
        assert result["dominant_estimate"] == "insufficient_evidence"
        assert result["is_definitive_claim"] is False
        await sdk.revoke_consent("sdk-remote")
        rejected = await sdk.analyze_audio("sdk-remote", "token", SILENCE)
        assert isinstance(rejected, dict)
        assert rejected["status"] == "consent_rejected"
