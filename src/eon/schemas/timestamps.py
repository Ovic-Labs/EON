"""Timezone-aware UTC timestamp contracts and normalization utilities."""

import datetime
from typing import Annotated

from pydantic import BeforeValidator, PlainSerializer


def ensure_utc_datetime(value: datetime.datetime | str) -> datetime.datetime:
    """Validate that timestamp is timezone-aware and normalize to UTC.

    Rejects naive datetimes strictly to prevent time-drift, ambiguation,
    and cross-system race conditions in robotic event routing.
    """
    if isinstance(value, str):
        # Parse ISO 8601 string
        dt = datetime.datetime.fromisoformat(value)
    elif isinstance(value, datetime.datetime):
        dt = value
    else:
        raise ValueError(f"Expected datetime or ISO 8601 string, received {type(value).__name__}.")

    if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:
        raise ValueError(
            "Timestamp must be timezone-aware (naive datetimes are strictly rejected). "
            "Please provide a timezone offset (e.g. UTC)."
        )

    return dt.astimezone(datetime.timezone.utc)


def utc_now() -> datetime.datetime:
    """Return the current time in UTC with timezone awareness."""
    return datetime.datetime.now(datetime.timezone.utc)


def format_iso8601(dt: datetime.datetime) -> str:
    """Format timezone-aware UTC datetime to ISO 8601 with trailing 'Z'."""
    utc_dt = ensure_utc_datetime(dt)
    return utc_dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ")


UtcTimestamp = Annotated[
    datetime.datetime,
    BeforeValidator(ensure_utc_datetime),
    PlainSerializer(format_iso8601, return_type=str, when_used="json"),
]
