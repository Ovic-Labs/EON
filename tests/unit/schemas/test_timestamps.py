"""Unit tests for UTC timestamp contracts and timezone normalization."""

import datetime

import pytest
from pydantic import BaseModel, ValidationError

from eon.schemas.timestamps import (
    UtcTimestamp,
    ensure_utc_datetime,
    format_iso8601,
    utc_now,
)


class DummyTimestampModel(BaseModel):
    timestamp: UtcTimestamp


def test_utc_now_is_timezone_aware() -> None:
    """AC-1.2-03: Verify utc_now returns timezone-aware UTC datetime."""
    now = utc_now()
    assert now.tzinfo is not None
    assert now.tzinfo == datetime.timezone.utc


def test_naive_datetime_strictly_rejected() -> None:
    """AC-1.2-03: Verify naive datetimes are rejected with an explicit error."""
    naive_dt = datetime.datetime(2026, 11, 23, 12, 0, 0)
    with pytest.raises(ValueError) as exc_info:
        ensure_utc_datetime(naive_dt)
    assert "must be timezone-aware" in str(exc_info.value)

    with pytest.raises(ValidationError):
        DummyTimestampModel(timestamp=naive_dt)


def test_non_utc_timezone_normalized_to_utc() -> None:
    """AC-1.2-03: Verify non-UTC timezone offsets are converted correctly to UTC."""
    # Offset: +05:30 (e.g. IST)
    tz_ist = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
    dt_ist = datetime.datetime(2026, 11, 23, 17, 30, 0, tzinfo=tz_ist)

    normalized = ensure_utc_datetime(dt_ist)
    assert normalized.tzinfo == datetime.timezone.utc
    assert normalized.hour == 12
    assert normalized.minute == 0
    assert normalized.day == 23


def test_iso8601_string_parsing() -> None:
    """Verify ISO 8601 string inputs are parsed and normalized."""
    iso_str = "2026-11-23T12:00:00+00:00"
    m = DummyTimestampModel(timestamp=iso_str)  # type: ignore[arg-type]
    assert m.timestamp.tzinfo == datetime.timezone.utc
    assert m.timestamp.hour == 12


def test_format_iso8601_output() -> None:
    """Verify ISO 8601 formatting includes trailing Z."""
    dt = datetime.datetime(2026, 11, 23, 12, 0, 0, 123000, tzinfo=datetime.timezone.utc)
    formatted = format_iso8601(dt)
    assert formatted.endswith("Z")
    assert "2026-11-23T12:00:00" in formatted


def test_timestamp_serialization_in_model() -> None:
    """Verify timestamp serializes to ISO 8601 in JSON dump."""
    now = utc_now()
    m = DummyTimestampModel(timestamp=now)
    json_out = m.model_dump_json()
    assert "Z" in json_out or "+00:00" in json_out


def test_ensure_utc_invalid_type_raises() -> None:
    """Verify passing non-datetime non-string raises ValueError."""
    with pytest.raises(ValueError) as exc:
        ensure_utc_datetime(12345)  # type: ignore[arg-type]
    assert "Expected datetime or ISO 8601 string" in str(exc.value)
