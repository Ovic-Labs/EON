"""Unicode-safe text validation and normalization for ERS text affect analysis."""

from __future__ import annotations

import re
import unicodedata

from pydantic import BaseModel, ConfigDict, Field


class NormalizedText(BaseModel):
    """Normalized UTF-8 text envelope with non-linguistic structural statistics."""

    model_config = ConfigDict(frozen=True)

    text: str = Field(..., description="Unicode NFC normalized text string.")
    char_length: int = Field(..., ge=0)
    word_count: int = Field(..., ge=0)
    has_non_ascii: bool = Field(default=False)
    exclamation_count: int = Field(default=0, ge=0)
    question_count: int = Field(default=0, ge=0)
    uppercase_ratio: float = Field(default=0.0, ge=0.0, le=1.0)
    is_valid: bool = Field(default=True)
    rejection_reason: str | None = Field(default=None)


class TextNormalizer:
    """Validates UTF-8 inputs, normalizes Unicode, and rejects empty or oversized text."""

    _WHITESPACE_RE = re.compile(r"\s+")

    def __init__(self, max_length: int = 8192) -> None:
        self.max_length = max_length

    def normalize(self, raw_text: str | bytes | None) -> NormalizedText:
        """Validate UTF-8 encoding, length bounds, and Unicode NFC normalization."""
        if raw_text is None:
            return NormalizedText(
                text="",
                char_length=0,
                word_count=0,
                is_valid=False,
                rejection_reason="No text payload provided.",
            )

        if isinstance(raw_text, bytes):
            try:
                decoded = raw_text.decode("utf-8", errors="strict")
            except UnicodeDecodeError as exc:
                return NormalizedText(
                    text="",
                    char_length=0,
                    word_count=0,
                    is_valid=False,
                    rejection_reason=f"Invalid UTF-8 text encoding: {exc}",
                )
        else:
            decoded = str(raw_text)

        if "\x00" in decoded:
            return NormalizedText(
                text="",
                char_length=0,
                word_count=0,
                is_valid=False,
                rejection_reason="Null byte rejected in text payload.",
            )

        if len(decoded) > self.max_length:
            return NormalizedText(
                text="",
                char_length=len(decoded),
                word_count=0,
                is_valid=False,
                rejection_reason=f"Text length {len(decoded)} exceeds max allowed {self.max_length} chars.",
            )

        normalized = unicodedata.normalize("NFC", decoded)
        collapsed = self._WHITESPACE_RE.sub(" ", normalized).strip()
        if not collapsed:
            return NormalizedText(
                text="",
                char_length=0,
                word_count=0,
                is_valid=False,
                rejection_reason="Text input is empty or whitespace-only.",
            )

        words = collapsed.split(" ")
        alpha_chars = [ch for ch in collapsed if ch.isalpha()]
        upper_chars = [ch for ch in alpha_chars if ch.isupper()]
        uppercase_ratio = len(upper_chars) / len(alpha_chars) if alpha_chars else 0.0

        return NormalizedText(
            text=collapsed,
            char_length=len(collapsed),
            word_count=len(words),
            has_non_ascii=any(ord(ch) > 127 for ch in collapsed),
            exclamation_count=collapsed.count("!"),
            question_count=collapsed.count("?"),
            uppercase_ratio=round(uppercase_ratio, 4),
            is_valid=True,
        )
