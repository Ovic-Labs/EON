"""Privacy requirement tests for ERS."""

import pytest
from eon_ers.config import ERSConfig
from eon_ers.contracts import ERSInput
from eon_ers.engine import ERSEngine
from eon_ers.exceptions import ERSPrivacyConsentError
from eon_ers.privacy.media_handling import SensitiveDataRedactor
from eon_ers.privacy.retention import MediaRetentionGuard
from eon_ers.types import Modality


@pytest.mark.asyncio
async def test_consent_validation_enforcement() -> None:
    config = ERSConfig(require_explicit_consent=True)
    engine = ERSEngine(config)
    await engine.initialize()
    await engine.start()

    # Input with empty consent token must be rejected
    inp_invalid = ERSInput(
        session_id="session-p1",
        modality=Modality.FACIAL,
        consent_reference="  ",  # Whitespace / empty
        image_payload=b"test-bytes",
    )

    with pytest.raises(ERSPrivacyConsentError):
        await engine.process(inp_invalid)

    await engine.stop()


@pytest.mark.asyncio
async def test_consent_revocation_prevents_subsequent_processing() -> None:
    config = ERSConfig(require_explicit_consent=True)
    engine = ERSEngine(config)
    await engine.initialize()
    await engine.start()

    session_id = "session-p2"
    consent_ref = "valid-consent-token-2026"
    engine.consent_mgr.register_consent(session_id, consent_ref)

    # Revoke consent
    engine.consent_mgr.revoke_consent(session_id)

    inp = ERSInput(
        session_id=session_id,
        modality=Modality.FACIAL,
        consent_reference=consent_ref,
        image_payload=b"test-bytes",
    )

    with pytest.raises(ERSPrivacyConsentError) as exc_info:
        await engine.process(inp)

    assert "explicitly revoked" in str(exc_info.value)
    await engine.stop()


def test_zero_disk_retention_scrub() -> None:
    guard = MediaRetentionGuard(zero_disk_retention=True)
    inp = ERSInput(
        session_id="session-p3",
        modality=Modality.SPEECH,
        consent_reference="valid-token",
        audio_payload=b"binary-speech-waveform",
    )
    assert inp.audio_payload is not None
    guard.scrub(inp)
    assert inp.audio_payload is None

    # Disk leak check
    with pytest.raises(RuntimeError):
        guard.assert_zero_disk_leak("/tmp/persisted_audio_recording.wav")


def test_sensitive_data_redactor() -> None:
    raw_text = "Diagnostic error with base64 data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAADIAAAAyCAYAAAAeP4ixAAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAAJcEhZcwAADsMAAA7DAcdvqGQ="
    redacted = SensitiveDataRedactor.redact_string(raw_text)
    assert "[REDACTED_BINARY_PAYLOAD]" in redacted
    assert "iVBORw0KGgoAAA" not in redacted

    raw_dict = {
        "user_id": "test_user",
        "image_bytes": b"binary_data",
        "payload": "secret_data",
        "details": {"nested_embedding": [0.1, 0.2]},
    }
    sanitized = SensitiveDataRedactor.sanitize_dict(raw_dict)
    assert sanitized["user_id"] == "test_user"
    assert sanitized["image_bytes"] == "[REDACTED]"
    assert sanitized["payload"] == "[REDACTED]"
    assert sanitized["details"]["nested_embedding"] == "[REDACTED]"
