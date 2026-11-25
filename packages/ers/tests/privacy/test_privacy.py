"""Privacy requirement tests for ERS."""

from concurrent.futures import ThreadPoolExecutor

import pytest
from eon_ers.config import ERSConfig
from eon_ers.contracts import ERSInput
from eon_ers.engine import ERSEngine
from eon_ers.exceptions import ERSPrivacyConsentError
from eon_ers.privacy.consent import ConsentManager
from eon_ers.privacy.media_handling import SensitiveDataRedactor
from eon_ers.privacy.retention import MediaRetentionGuard
from eon_ers.types import Modality


def test_consent_registration_rejects_empty_and_whitespace() -> None:
    cm = ConsentManager(enforce_consent=True)
    with pytest.raises(ERSPrivacyConsentError):
        cm.register_consent("", "valid-token-123")

    with pytest.raises(ERSPrivacyConsentError):
        cm.register_consent("session-1", "")

    with pytest.raises(ERSPrivacyConsentError):
        cm.register_consent("session-1", "   \t\n")


def test_consent_unknown_session_rejected() -> None:
    cm = ConsentManager(enforce_consent=True)
    with pytest.raises(ERSPrivacyConsentError) as exc_info:
        cm.validate_consent("unknown-session-999", "some-arbitrary-token")
    assert "No active registered consent" in str(exc_info.value)


def test_consent_unregistered_arbitrary_reference_rejected() -> None:
    cm = ConsentManager(enforce_consent=True)
    # Register session 1 with token A
    cm.register_consent("session-1", "token-A-123456")

    # Present arbitrary token to session 2
    with pytest.raises(ERSPrivacyConsentError) as exc_info:
        cm.validate_consent("session-2", "arbitrary-forged-token-789")
    assert "No active registered consent" in str(exc_info.value)


def test_consent_empty_reference_rejected() -> None:
    cm = ConsentManager(enforce_consent=True)
    cm.register_consent("session-1", "valid-token-123")

    with pytest.raises(ERSPrivacyConsentError) as exc_info:
        cm.validate_consent("session-1", "")
    assert "Missing or empty consent reference" in str(exc_info.value)

    with pytest.raises(ERSPrivacyConsentError) as exc_info:
        cm.validate_consent("session-1", None)
    assert "Missing or empty consent reference" in str(exc_info.value)


def test_consent_whitespace_reference_rejected() -> None:
    cm = ConsentManager(enforce_consent=True)
    cm.register_consent("session-1", "valid-token-123")

    with pytest.raises(ERSPrivacyConsentError) as exc_info:
        cm.validate_consent("session-1", "   \t  ")
    assert "Missing or empty consent reference" in str(exc_info.value)


def test_consent_wrong_reference_rejected() -> None:
    cm = ConsentManager(enforce_consent=True)
    cm.register_consent("session-1", "valid-token-123")

    with pytest.raises(ERSPrivacyConsentError) as exc_info:
        cm.validate_consent("session-1", "wrong-token-999")
    assert "Consent reference mismatch" in str(exc_info.value)


def test_consent_correct_registered_reference_accepted() -> None:
    cm = ConsentManager(enforce_consent=True)
    cm.register_consent("session-1", "valid-token-123")
    # Must not raise
    cm.validate_consent("session-1", "valid-token-123")


def test_consent_revoked_reference_rejected() -> None:
    cm = ConsentManager(enforce_consent=True)
    cm.register_consent("session-1", "valid-token-123")
    cm.revoke_consent("session-1")

    with pytest.raises(ERSPrivacyConsentError) as exc_info:
        cm.validate_consent("session-1", "valid-token-123")
    assert "explicitly revoked" in str(exc_info.value)


def test_consent_independent_session_isolation() -> None:
    cm = ConsentManager(enforce_consent=True)
    cm.register_consent("session-alice", "alice-token-xyz")
    cm.register_consent("session-bob", "bob-token-abc")

    # Alice's token on Bob's session must fail
    with pytest.raises(ERSPrivacyConsentError) as exc_info:
        cm.validate_consent("session-bob", "alice-token-xyz")
    assert "Consent reference mismatch" in str(exc_info.value)

    # Bob's token on Bob's session succeeds
    cm.validate_consent("session-bob", "bob-token-abc")

    # Revoking Alice does not affect Bob
    cm.revoke_consent("session-alice")
    with pytest.raises(ERSPrivacyConsentError):
        cm.validate_consent("session-alice", "alice-token-xyz")
    cm.validate_consent("session-bob", "bob-token-abc")


def test_consent_revocation_racing_with_processing() -> None:
    cm = ConsentManager(enforce_consent=True)
    session_id = "concurrent-race-session"
    token = "race-token-998877"
    cm.register_consent(session_id, token)

    iterations = 200
    validation_outcomes: list[bool] = []

    def validator_worker() -> None:
        for _ in range(iterations):
            try:
                cm.validate_consent(session_id, token)
                validation_outcomes.append(True)
            except ERSPrivacyConsentError:
                validation_outcomes.append(False)

    def revoker_worker() -> None:
        for i in range(iterations):
            if i % 10 == 0:
                cm.revoke_consent(session_id)
            elif i % 10 == 5:
                # Revoked sessions are terminal and cannot be reactivated; register fresh sub-sessions concurrently
                try:
                    cm.register_consent(session_id, token)
                except ERSPrivacyConsentError:
                    cm.register_consent(f"{session_id}-fresh-{i}", token)

    with ThreadPoolExecutor(max_workers=4) as executor:
        f1 = executor.submit(validator_worker)
        f2 = executor.submit(revoker_worker)
        f3 = executor.submit(validator_worker)
        f1.result()
        f2.result()
        f3.result()

    # The manager must remain completely coherent and thread-safe without crashes or corrupted state
    assert len(validation_outcomes) == iterations * 2


@pytest.mark.asyncio
async def test_engine_consent_validation_enforcement() -> None:
    config = ERSConfig(require_explicit_consent=True)
    engine = ERSEngine(config)
    await engine.initialize()
    await engine.start()

    # Unregistered session input must be rejected
    inp_unregistered = ERSInput(
        session_id="unregistered-sess",
        modality=Modality.FACIAL,
        consent_reference="arbitrary-token",
        image_payload=b"test-bytes",
    )
    with pytest.raises(ERSPrivacyConsentError):
        await engine.process(inp_unregistered)

    # Register session and process
    engine.register_consent("registered-sess", "valid-token-777")
    inp_valid = ERSInput(
        session_id="registered-sess",
        modality=Modality.FACIAL,
        consent_reference="valid-token-777",
        image_payload=None,
    )
    # Payload is None so it returns INSUFFICIENT_EVIDENCE, but passes consent
    obs = await engine.process(inp_valid)
    assert obs.observation_id == inp_valid.observation_id

    await engine.stop()


@pytest.mark.asyncio
async def test_engine_consent_revocation_prevents_subsequent_processing() -> None:
    config = ERSConfig(require_explicit_consent=True)
    engine = ERSEngine(config)
    await engine.initialize()
    await engine.start()

    session_id = "session-p2"
    consent_ref = "valid-consent-token-2026"
    engine.register_consent(session_id, consent_ref)

    # Revoke consent
    engine.revoke_consent(session_id)

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
    raw_text = (
        "Diagnostic error with base64 "
        "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAADIAAAAyCAYAAAAeP4ixAAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAAJcEhZcwAADsMAAA7DAcdvqGQ="
    )
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
