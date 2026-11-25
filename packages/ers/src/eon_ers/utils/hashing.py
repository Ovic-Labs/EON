"""Cryptographic hashing helpers for ERS artifact and secret integrity."""

from __future__ import annotations

import hashlib
import hmac
from pathlib import Path


def sha256_bytes(data: bytes) -> str:
    """Compute lowercase hexadecimal SHA-256 digest of a byte buffer."""
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: str | Path, chunk_size: int = 1024 * 1024) -> str:
    """Compute SHA-256 digest of a file using bounded streaming chunks."""
    file_path = Path(path)
    hasher = hashlib.sha256()
    with file_path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            hasher.update(chunk)
    return hasher.hexdigest()


def constant_time_compare(actual: str, expected: str) -> bool:
    """Compare two hexadecimal digest strings in constant time."""
    return hmac.compare_digest(actual.strip().lower(), expected.strip().lower())
