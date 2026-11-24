"""Diagnostic log sanitizer and sensitive data redactor for ERS."""

from __future__ import annotations

import re
from typing import Any


class SensitiveDataRedactor:
    """Redacts biometric identifiers, base64 data, and raw media dumps from logs."""

    BASE64_PATTERN = re.compile(r"(data:[a-zA-Z0-9/]+;base64,)?[a-zA-Z0-9+/]{40,}={0,2}")

    @classmethod
    def redact_string(cls, text: str) -> str:
        """Redact sensitive base64 and binary tokens from diagnostic strings."""
        if not text:
            return text
        sanitized = cls.BASE64_PATTERN.sub("[REDACTED_BINARY_PAYLOAD]", text)
        return sanitized

    @classmethod
    def sanitize_dict(cls, data: dict[str, Any]) -> dict[str, Any]:
        """Recursively scrub sensitive keys and large byte representations from dicts."""
        clean: dict[str, Any] = {}
        for k, v in data.items():
            k_lower = str(k).lower()
            if any(
                sensitive in k_lower
                for sensitive in [
                    "payload",
                    "image_bytes",
                    "audio_bytes",
                    "embedding",
                    "face_print",
                ]
            ):
                clean[k] = "[REDACTED]"
            elif isinstance(v, bytes):
                clean[k] = f"[BYTES_LEN_{len(v)}]"
            elif isinstance(v, str):
                clean[k] = cls.redact_string(v)
            elif isinstance(v, dict):
                clean[k] = cls.sanitize_dict(v)
            else:
                clean[k] = v
        return clean
