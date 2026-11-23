"""Identifier types, validation rules, and generators for OVIC EON."""

import re
import uuid
from typing import Annotated, Final

from pydantic import Field

UUID_PATTERN: Final[str] = r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
_UUID_REGEX = re.compile(UUID_PATTERN, re.IGNORECASE)

SOURCE_ID_PATTERN: Final[str] = r"^[a-z0-9_-]+(\.[a-z0-9_-]+)*$"
_SOURCE_ID_REGEX = re.compile(SOURCE_ID_PATTERN)

SESSION_ID_PATTERN: Final[str] = r"^[a-zA-Z0-9_\-\.]{1,128}$"
_SESSION_ID_REGEX = re.compile(SESSION_ID_PATTERN)

SCHEMA_ID_PATTERN: Final[str] = r"^[a-z0-9_]+(\.[a-z0-9_]+)*(\.v[0-9]+)?$"
_SCHEMA_ID_REGEX = re.compile(SCHEMA_ID_PATTERN)


def validate_uuid_string(val: str) -> str:
    """Validate and normalize a UUID string to lowercase representation."""
    if not isinstance(val, str) or not _UUID_REGEX.match(val):
        raise ValueError(f"Value '{val}' is not a valid 36-character hyphenated UUID.")
    return val.lower()


def validate_source_id(val: str) -> str:
    """Validate hierarchical dot-separated source identifier."""
    if not isinstance(val, str) or not _SOURCE_ID_REGEX.match(val):
        raise ValueError(
            f"Source ID '{val}' must be lowercase dot-separated tokens (e.g. 'eon.ers.visual')."
        )
    return val


def validate_session_id(val: str) -> str:
    """Validate alphanumeric or hyphenated session identifier."""
    if not isinstance(val, str) or not _SESSION_ID_REGEX.match(val):
        raise ValueError(
            f"Session ID '{val}' must contain 1-128 alphanumeric, dot, or hyphen characters."
        )
    return val


def generate_event_id() -> str:
    """Generate a cryptographically random UUID4 event identifier."""
    return str(uuid.uuid4())


def generate_correlation_id() -> str:
    """Generate a UUID4 correlation identifier for cross-event tracking."""
    return str(uuid.uuid4())


def generate_causation_id() -> str:
    """Generate a UUID4 causation identifier for direct parent-event tracking."""
    return str(uuid.uuid4())


def generate_session_id() -> str:
    """Generate a UUID4 session identifier for conversation/interaction tracking."""
    return str(uuid.uuid4())


EventId = Annotated[
    str,
    Field(
        default_factory=generate_event_id,
        pattern=UUID_PATTERN,
        description="Globally unique UUID4 identifier for this individual event.",
    ),
]

CorrelationId = Annotated[
    str,
    Field(
        pattern=UUID_PATTERN,
        description="Shared UUID4 identifier linking all events across an end-to-end transaction.",
    ),
]

CausationId = Annotated[
    str,
    Field(
        pattern=UUID_PATTERN,
        description="UUID4 identifier of the direct causal parent event that triggered this event.",
    ),
]

SessionId = Annotated[
    str,
    Field(
        pattern=SESSION_ID_PATTERN,
        description="Identifier for the active interaction session or engagement context.",
    ),
]

SourceId = Annotated[
    str,
    Field(
        pattern=SOURCE_ID_PATTERN,
        description="Dot-delimited producer identifier (e.g. 'eon.ers', 'sensor.mic').",
    ),
]

SchemaId = Annotated[
    str,
    Field(
        pattern=SCHEMA_ID_PATTERN,
        description="Identifier denoting the contract type and namespace.",
    ),
]
