"""Bounded decoding and mathematical validation helpers for ERS."""

from __future__ import annotations

import base64
import binascii

import numpy as np


def decode_bounded_base64(encoded: str, max_bytes: int) -> bytes:
    """Decode a base64 payload (with optional data URI prefix) under strict byte limits."""
    if not isinstance(encoded, str) or not encoded.strip():
        raise ValueError("Encoded payload must be a non-empty base64 string.")

    payload = encoded.split(",", 1)[1] if "," in encoded else encoded
    payload = payload.strip()
    if not payload:
        raise ValueError("Encoded payload body is empty.")

    # Quick upper-bound check before allocating decoded buffer
    estimated_bytes = (len(payload) * 3) // 4 + 3
    if estimated_bytes > max_bytes + 4:
        raise ValueError(f"Encoded payload exceeds maximum allowed size of {max_bytes} bytes.")

    try:
        raw = base64.b64decode(payload, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ValueError(f"Invalid base64 payload: {exc}") from exc

    if not raw:
        raise ValueError("Decoded binary payload is empty.")
    if len(raw) > max_bytes:
        raise ValueError(
            f"Decoded binary payload size {len(raw)} exceeds limit of {max_bytes} bytes."
        )
    return raw


def normalize_probabilities(probs: dict[str, float]) -> dict[str, float]:
    """Ensure finite non-negative probabilities summing cleanly to 1.0."""
    if not probs:
        raise ValueError("Probability dictionary must not be empty.")
    arr = np.array(list(probs.values()), dtype=np.float64)
    if not np.isfinite(arr).all():
        raise ValueError("Probability distribution contains non-finite values.")
    if (arr < 0.0).any():
        raise ValueError("Probability distribution contains negative values.")
    total = float(arr.sum())
    if total <= 1e-12:
        uniform = 1.0 / len(probs)
        return {k: uniform for k in probs}
    return {k: float(v / total) for k, v in probs.items()}
