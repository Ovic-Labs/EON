"""Consent verification and revocation management for ERS.

Enforces strict authorization: sensory data is only processed when an active,
explicit consent reference has been pre-registered for the session.
Arbitrary, unregistered, mismatched, or revoked references are strictly rejected.
Plaintext consent tokens are hashed via SHA-256 before storage and compared in constant time.
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import threading

from eon_ers.exceptions import ERSPrivacyConsentError

logger = logging.getLogger("eon.ers.privacy.consent")


def _mask_reference(ref: str) -> str:
    """Generate a one-way pseudonymous identifier for logging without leaking the token."""
    return f"ref_sha256:{hashlib.sha256(ref.encode('utf-8')).hexdigest()[:8]}"


def _hash_reference(ref: str) -> str:
    """Hash a consent token cleanly so raw credentials are never retained in memory."""
    return hashlib.sha256(ref.encode("utf-8")).hexdigest()


def _format_display_mask(ref: str) -> str:
    """Produce a safe UI display mask without exposing full credentials."""
    if len(ref) > 8:
        return f"{ref[:5]}***{ref[-3:]}"
    if len(ref) >= 6:
        return f"{ref[:4]}***{ref[-2:]}"
    return "***"


class ConsentManager:
    """Enforces explicit user consent before accepting sensory observation data."""

    def __init__(self, enforce_consent: bool = True) -> None:
        self.enforce_consent = enforce_consent
        self._lock = threading.RLock()
        # Maps session_id -> SHA-256 digest of consent_reference (no plaintext token storage)
        self._consents: dict[str, str] = {}
        self._display_masks: dict[str, str] = {}
        self._revoked_sessions: set[str] = set()

    def register_consent(self, session_id: str, consent_reference: str) -> None:
        """Register active user consent for an interaction session.

        Raises:
            ERSPrivacyConsentError: If session_id or consent_reference is empty or whitespace.
        """
        if not session_id or not session_id.strip():
            raise ERSPrivacyConsentError(
                "Consent registration failed: Session ID cannot be empty or whitespace."
            )
        if not consent_reference or not consent_reference.strip():
            raise ERSPrivacyConsentError(
                "Consent registration failed: Consent reference cannot be empty or whitespace."
            )

        clean_session = session_id.strip()
        clean_ref = consent_reference.strip()

        with self._lock:
            if clean_session in self._revoked_sessions:
                raise ERSPrivacyConsentError(
                    f"Consent registration rejected: Session '{clean_session}' has been explicitly revoked "
                    "and cannot be reactivated. Start a new session ID to grant fresh consent."
                )
            self._consents[clean_session] = _hash_reference(clean_ref)
            self._display_masks[clean_session] = _format_display_mask(clean_ref)
            masked = _mask_reference(clean_ref)
            logger.info("Registered active consent for session '%s' [%s].", clean_session, masked)

    def revoke_consent(self, session_id: str) -> None:
        """Revoke user consent for a session immediately.

        Any subsequent processing attempts for this session will be blocked.
        """
        if not session_id or not session_id.strip():
            return

        clean_session = session_id.strip()
        with self._lock:
            self._consents.pop(clean_session, None)
            self._display_masks.pop(clean_session, None)
            self._revoked_sessions.add(clean_session)
            logger.info("Revoked consent for session '%s'.", clean_session)

    def has_active_consent(self, session_id: str) -> bool:
        """Check whether a session has active registered consent."""
        clean_session = session_id.strip()
        if not clean_session:
            return False
        with self._lock:
            return clean_session in self._consents and clean_session not in self._revoked_sessions

    def get_status(self, session_id: str) -> dict[str, object]:
        """Return safe non-secret consent status metadata for a session."""
        clean_session = session_id.strip()
        with self._lock:
            has_active = (
                clean_session in self._consents and clean_session not in self._revoked_sessions
            )
            is_revoked = clean_session in self._revoked_sessions
            masked = self._display_masks.get(clean_session) if has_active else None
            return {
                "session_id": clean_session,
                "has_active_consent": has_active,
                "is_revoked": is_revoked,
                "masked_reference": masked,
            }

    def validate_consent(self, session_id: str, consent_reference: str | None) -> None:
        """Verify that valid, pre-registered active consent exists for this session.

        Security invariants:
        - Missing session consent is always rejected.
        - Missing or whitespace reference is always rejected.
        - Arbitrary unregistered references are always rejected.
        - Reference mismatch is always rejected.
        - Revoked consent is always rejected.
        - Constant-time digest comparison is used.
        - Consent references are never exposed in log output or retained in plaintext.

        Raises:
            ERSPrivacyConsentError: On any consent failure.
        """
        if not self.enforce_consent:
            return

        if not session_id or not session_id.strip():
            raise ERSPrivacyConsentError("Processing rejected: Empty or missing session ID.")

        clean_session = session_id.strip()

        if consent_reference is None or not consent_reference.strip():
            raise ERSPrivacyConsentError(
                f"Processing rejected: Missing or empty consent reference for session '{clean_session}'."
            )

        clean_ref = consent_reference.strip()
        candidate_digest = _hash_reference(clean_ref)

        with self._lock:
            if clean_session in self._revoked_sessions:
                raise ERSPrivacyConsentError(
                    f"Processing rejected: Consent for session '{clean_session}' has been explicitly revoked."
                )

            stored_digest = self._consents.get(clean_session)
            if stored_digest is None:
                raise ERSPrivacyConsentError(
                    f"Processing rejected: No active registered consent found for session '{clean_session}'. "
                    f"Unregistered arbitrary references are prohibited."
                )

            if not hmac.compare_digest(stored_digest, candidate_digest):
                raise ERSPrivacyConsentError(
                    f"Processing rejected: Consent reference mismatch for session '{clean_session}'."
                )
