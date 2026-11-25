"""API authentication, SHA-256 hashed credentials, RBAC, and session isolation."""

from __future__ import annotations

import secrets
import threading
import time
from dataclasses import dataclass, field
from enum import Enum

from eon_ers.exceptions import ERSAuthenticationError, ERSAuthorizationError
from eon_ers.utils.hashing import constant_time_compare, sha256_bytes


class Role(str, Enum):
    """Role-based access control levels for ERS integration."""

    ADMIN = "admin"
    DEVELOPER = "developer"
    OPERATOR = "operator"
    VIEWER = "viewer"


ROLE_PERMISSIONS: dict[Role, frozenset[str]] = {
    Role.ADMIN: frozenset(
        {
            "health:read",
            "models:read",
            "models:manage",
            "analyze:run",
            "consent:manage",
            "sessions:manage",
            "audit:read",
            "keys:manage",
        }
    ),
    Role.DEVELOPER: frozenset(
        {
            "health:read",
            "models:read",
            "analyze:run",
            "consent:manage",
            "sessions:manage",
            "audit:read",
        }
    ),
    Role.OPERATOR: frozenset(
        {
            "health:read",
            "models:read",
            "analyze:run",
            "consent:manage",
            "sessions:manage",
        }
    ),
    Role.VIEWER: frozenset({"health:read", "models:read"}),
}


@dataclass(frozen=True)
class AuthenticatedPrincipal:
    """Verified caller identity and RBAC role."""

    principal_id: str
    role: Role
    key_id: str
    authenticated: bool = True

    def has_permission(self, perm: str) -> bool:
        return perm in ROLE_PERMISSIONS.get(self.role, frozenset())


@dataclass
class _StoredCredential:
    key_id: str
    principal_id: str
    role: Role
    secret_digest: str
    created_at: float = field(default_factory=time.time)
    expires_at: float | None = None
    revoked: bool = False


class APIKeyAuthManager:
    """Thread-safe API key and session token verifier with zero plaintext credential storage."""

    def __init__(self, require_auth: bool = False) -> None:
        self.require_auth = require_auth
        self._lock = threading.Lock()
        self._credentials: dict[str, _StoredCredential] = {}

    def issue_key(
        self,
        principal_id: str,
        role: Role = Role.OPERATOR,
        *,
        raw_secret: str | None = None,
        ttl_seconds: float | None = None,
    ) -> tuple[str, str]:
        """Issue and store a SHA-256 hashed API key, returning `(key_id, raw_secret)` once."""
        clean_principal = principal_id.strip()
        if not clean_principal:
            raise ValueError("principal_id must be non-empty.")

        secret = raw_secret if raw_secret is not None else f"eon_{secrets.token_urlsafe(24)}"
        if len(secret.strip()) < 8:
            raise ValueError("API secret must be at least 8 characters.")
        key_id = f"key_{secrets.token_hex(6)}"
        expires_at = (time.time() + ttl_seconds) if ttl_seconds is not None else None
        digest = sha256_bytes(secret.encode("utf-8"))

        with self._lock:
            self._credentials[key_id] = _StoredCredential(
                key_id=key_id,
                principal_id=clean_principal,
                role=role,
                secret_digest=digest,
                expires_at=expires_at,
            )
        return key_id, secret

    def revoke_key(self, key_id: str) -> bool:
        """Immediately revoke an issued credential."""
        with self._lock:
            cred = self._credentials.get(key_id)
            if cred is None:
                return False
            cred.revoked = True
            return True

    def authenticate(
        self,
        api_key: str | None = None,
        authorization: str | None = None,
    ) -> AuthenticatedPrincipal:
        """Verify presented `X-API-Key` or `Bearer` token against stored SHA-256 hashes."""
        token = api_key
        if not token and authorization and authorization.lower().startswith("bearer "):
            token = authorization[7:].strip()

        if not token:
            if not self.require_auth:
                return AuthenticatedPrincipal(
                    principal_id="local-operator",
                    role=Role.ADMIN,
                    key_id="unauthenticated-dev",
                    authenticated=False,
                )
            raise ERSAuthenticationError("Missing API key or Bearer token.")

        presented_digest = sha256_bytes(token.encode("utf-8"))
        now = time.time()
        with self._lock:
            for cred in self._credentials.values():
                if constant_time_compare(presented_digest, cred.secret_digest):
                    if cred.revoked:
                        raise ERSAuthenticationError("Presented API key has been revoked.")
                    if cred.expires_at is not None and now > cred.expires_at:
                        raise ERSAuthenticationError("Presented API key has expired.")
                    return AuthenticatedPrincipal(
                        principal_id=cred.principal_id,
                        role=cred.role,
                        key_id=cred.key_id,
                        authenticated=True,
                    )
        raise ERSAuthenticationError("Invalid API key or token.")

    @staticmethod
    def authorize(principal: AuthenticatedPrincipal, permission: str) -> None:
        """Require caller RBAC permission or raise `ERSAuthorizationError`."""
        if not principal.has_permission(permission):
            raise ERSAuthorizationError(
                f"Role '{principal.role.value}' lacks required permission '{permission}'.",
                context={"role": principal.role.value, "permission": permission},
            )

    @staticmethod
    def authorize_session_owner(
        principal: AuthenticatedPrincipal, session_owner_id: str | None
    ) -> None:
        """Enforce multi-user session isolation; non-admins may only access their own sessions."""
        if not principal.authenticated:
            return
        if principal.role == Role.ADMIN:
            return
        if session_owner_id and session_owner_id != principal.principal_id:
            raise ERSAuthorizationError(
                "Cross-user session access denied.",
                context={"principal": principal.principal_id},
            )
