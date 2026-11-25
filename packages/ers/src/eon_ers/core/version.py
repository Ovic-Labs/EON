"""Version and product capability metadata for OVIC EON ERS."""

from __future__ import annotations

import platform
from typing import Any

ERS_VERSION = "0.2.0"
ERS_API_VERSION = "v1"
ERS_SCHEMA_VERSION = "1.0"
ERS_WS_PROTOCOL_VERSION = "1.0"


def get_version_info() -> dict[str, Any]:
    """Return engine, API, schema, and host runtime version metadata."""
    return {
        "component": "eon.ers",
        "version": ERS_VERSION,
        "api_version": ERS_API_VERSION,
        "schema_version": ERS_SCHEMA_VERSION,
        "ws_protocol_version": ERS_WS_PROTOCOL_VERSION,
        "python_version": platform.python_version(),
        "architecture": platform.machine() or "unknown",
        "execution_mode": "cpu_first_local",
    }
