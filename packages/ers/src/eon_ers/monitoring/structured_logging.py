"""Structured JSON logger with automatic correlation IDs and sensitive-data redaction."""

from __future__ import annotations

import contextvars
import json
import logging
from datetime import datetime, timezone
from typing import Any

from eon_ers.privacy.media_handling import SensitiveDataRedactor

_request_id_ctx: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "eon_ers_request_id", default=None
)
_session_id_ctx: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "eon_ers_session_id", default=None
)


def set_correlation_id(
    request_id: str | None = None,
    session_id: str | None = None,
) -> tuple[contextvars.Token[str | None], contextvars.Token[str | None]]:
    """Bind request and session correlation IDs to the active execution context."""
    t_req = _request_id_ctx.set(request_id)
    t_ses = _session_id_ctx.set(session_id)
    return t_req, t_ses


def get_correlation_id() -> tuple[str | None, str | None]:
    """Return the active (request_id, session_id) correlation pair."""
    return _request_id_ctx.get(), _session_id_ctx.get()


class StructuredJSONFormatter(logging.Formatter):
    """Formats Python log records as single-line redacted JSON objects."""

    def format(self, record: logging.LogRecord) -> str:
        req_id, sess_id = get_correlation_id()
        payload: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": SensitiveDataRedactor.redact_string(record.getMessage()),
            "request_id": getattr(record, "request_id", None) or req_id,
            "session_id": getattr(record, "session_id", None) or sess_id,
        }
        if record.exc_info and record.exc_info[0] is not None:
            payload["exception_type"] = record.exc_info[0].__name__
            payload["exception"] = SensitiveDataRedactor.redact_string(
                str(record.exc_info[1] or "")
            )
        return json.dumps(payload, separators=(",", ":"))


def configure_structured_logging(level: int = logging.INFO) -> logging.Logger:
    """Attach structured redacted JSON handler to the root `eon.ers` logger."""
    target = logging.getLogger("eon")
    target.setLevel(level)
    if not any(isinstance(h.formatter, StructuredJSONFormatter) for h in target.handlers):
        handler = logging.StreamHandler()
        handler.setFormatter(StructuredJSONFormatter())
        target.addHandler(handler)
    return target
