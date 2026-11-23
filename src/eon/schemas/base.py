"""Base schema definitions and common Pydantic v2 configuration."""

from typing import Any

from pydantic import BaseModel, ConfigDict


class EonBaseModel(BaseModel):
    """Universal foundational model for all OVIC EON data contracts.

    Enforces strict typing, immutability (frozen=True), and rejection of
    unknown/unmodeled fields (extra='forbid') to eliminate silent schema drift.
    """

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        validate_default=True,
        str_strip_whitespace=True,
        populate_by_name=True,
        ser_json_timedelta="iso8601",
        ser_json_bytes="base64",
        arbitrary_types_allowed=False,
    )

    def to_dict(self) -> dict[str, Any]:
        """Convert the model into a dictionary representation."""
        return self.model_dump(mode="python")

    def to_json(self, indent: int | None = None) -> str:
        """Serialize the model directly to a valid JSON string."""
        return self.model_dump_json(indent=indent)
