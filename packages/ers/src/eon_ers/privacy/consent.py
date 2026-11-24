"""Consent verification and revocation management for ERS."""

from __future__ import annotations

import threading

from eon_ers.exceptions import ERSPrivacyConsentError


class ConsentManager:
    """Enforces explicit user consent before accepting sensory observation data."""

    def __init__(self, enforce_consent: bool = True) -> None:
        self.enforce_consent = enforce_consent
        self._lock = threading.Lock()
        self._consents: dict[str, str] = {}
        self._revoked_sessions: set[str] = set()

    def register_consent(self, session_id: str, consent_reference: str) -> None:
        """Register active user consent for an interaction session."""
        with self._lock:
            self._consents[session_id] = consent_reference
            self._revoked_sessions.discard(session_id)

    def revoke_consent(self, session_id: str) -> None:
        """Revoke user consent for a session immediately."""
        with self._lock:
            if session_id in self._consents:
                del self._consents[session_id]
            self._revoked_sessions.add(session_id)

    def validate_consent(self, session_id: str, consent_reference: str) -> None:
        """Verify that valid consent exists for this session."""
        if not self.enforce_consent:
            return

        with self._lock:
            if session_id in self._revoked_sessions:
                raise ERSPrivacyConsentError(
                    f"Processing rejected: Consent for session '{session_id}' has been explicitly revoked."
                )

            if not consent_reference or len(consent_reference.strip()) < 3:
                raise ERSPrivacyConsentError(
                    f"Processing rejected: Missing or invalid consent reference for session '{session_id}'."
                )

            active_consent = self._consents.get(session_id)
            if active_consent is not None and active_consent != consent_reference:
                raise ERSPrivacyConsentError(
                    f"Processing rejected: Consent reference mismatch for session '{session_id}'."
                )
