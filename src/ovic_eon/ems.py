"""Local, user-scoped Emotional Memory System for the OVIC EON SDK."""

from __future__ import annotations

import sqlite3
import unicodedata
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal, cast
from uuid import uuid4

MemoryKind = Literal["interaction", "preference"]

__all__ = ["EmotionalMemory", "Memory", "MemoryKind"]

_SCHEMA = """
CREATE TABLE IF NOT EXISTS ems_memories (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    kind TEXT NOT NULL CHECK (kind IN ('interaction', 'preference')),
    preference_key TEXT,
    text TEXT NOT NULL,
    search_text TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    CHECK ((kind = 'interaction') = (preference_key IS NULL)),
    UNIQUE (user_id, preference_key)
);
CREATE INDEX IF NOT EXISTS ems_memories_by_user
ON ems_memories (user_id, updated_at DESC, id);
"""


@dataclass(frozen=True, slots=True)
class Memory:
    """An interaction summary or explicitly confirmed preference."""

    id: str
    kind: MemoryKind
    text: str
    preference_key: str | None
    created_at: datetime
    updated_at: datetime


def _required_text(value: str, name: str, maximum: int) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{name} must be a string")
    value = value.strip()
    if not value or len(value) > maximum or "\x00" in value:
        raise ValueError(f"{name} must contain 1 to {maximum} characters and no NUL")
    return value


def _terms(value: str) -> list[str]:
    normalized = unicodedata.normalize("NFKC", value).casefold()
    words = (
        char if char.isalnum() or unicodedata.category(char).startswith("M") else " "
        for char in normalized
    )
    return "".join(words).split()


def _read_memory(row: sqlite3.Row) -> Memory:
    return Memory(
        id=row["id"],
        kind=cast(MemoryKind, row["kind"]),
        text=row["text"],
        preference_key=row["preference_key"],
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )


class EmotionalMemory:
    """Store and retrieve text memories for one application-resolved user.

    The caller supplies an authorized user ID and chooses which interaction
    summaries may be saved. This class performs no automatic collection.
    """

    def __init__(self, database: str | Path, *, user_id: str) -> None:
        self._user_id = _required_text(user_id, "user_id", 128)
        if user_id != self._user_id:
            raise ValueError("user_id must not start or end with whitespace")
        self._database = Path(database).resolve()
        with self._connect() as connection:
            connection.executescript(_SCHEMA)

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self._database, timeout=5)
        connection.row_factory = sqlite3.Row
        try:
            with connection:
                connection.execute("PRAGMA secure_delete = ON")
                yield connection
        finally:
            connection.close()

    def remember_interaction(self, summary: str) -> Memory:
        """Save an interaction summary selected by the calling application."""
        return self._remember("interaction", summary, None)

    def confirm_preference(self, key: str, value: str, *, confirmed: bool) -> Memory:
        """Save or replace a preference that the user explicitly confirmed."""
        if confirmed is not True:
            raise ValueError("A preference requires explicit user confirmation")
        key = _required_text(key, "key", 128)
        return self._remember("preference", value, key)

    def _remember(self, kind: MemoryKind, value: str, key: str | None) -> Memory:
        value = _required_text(value, "memory text", 4096)
        search_text = " " + " ".join(_terms(f"{key or ''} {value}")) + " "
        memory_id = uuid4().hex
        now = datetime.now(UTC).isoformat(timespec="microseconds")
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO ems_memories
                (id, user_id, kind, preference_key, text, search_text, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT (user_id, preference_key) DO UPDATE SET
                    text = excluded.text,
                    search_text = excluded.search_text,
                    updated_at = excluded.updated_at
                """,
                (memory_id, self._user_id, kind, key, value, search_text, now, now),
            )
            if key is None:
                memory = connection.execute(
                    "SELECT * FROM ems_memories WHERE user_id = ? AND id = ?",
                    (self._user_id, memory_id),
                ).fetchone()
            else:
                memory = connection.execute(
                    "SELECT * FROM ems_memories WHERE user_id = ? AND preference_key = ?",
                    (self._user_id, key),
                ).fetchone()
            return _read_memory(memory)

    def get_preference(self, key: str) -> Memory | None:
        """Fetch the current confirmed value for a preference key."""
        key = _required_text(key, "key", 128)
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM ems_memories WHERE user_id = ? AND preference_key = ?",
                (self._user_id, key),
            ).fetchone()
        return None if row is None else _read_memory(row)

    def recall(
        self, query: str | None = None, *, kind: MemoryKind | None = None, limit: int = 10
    ) -> list[Memory]:
        """Rank whole-word matches by overlap, then recency. Omit query for recent memories."""
        if type(limit) is not int or not 1 <= limit <= 100:
            raise ValueError("limit must be an integer between 1 and 100")
        if kind not in (None, "interaction", "preference"):
            raise ValueError("kind must be interaction or preference")
        terms: list[str] = []
        if query is not None:
            terms = list(dict.fromkeys(_terms(_required_text(query, "query", 512))))[:24]
            if not terms:
                return []

        score = " + ".join("CASE WHEN instr(search_text, ?) > 0 THEN 1 ELSE 0 END" for _ in terms)
        score = score or "0"
        # The expression above is built from fixed fragments. All values are bound.
        with self._connect() as connection:
            rows = connection.execute(
                f"""
                SELECT * FROM (
                    SELECT ems_memories.*, ({score}) AS relevance
                    FROM ems_memories
                    WHERE user_id = ? AND (? IS NULL OR kind = ?)
                )
                WHERE relevance >= ?
                ORDER BY relevance DESC, updated_at DESC, id
                LIMIT ?
                """,
                (
                    *(f" {term} " for term in terms),
                    self._user_id,
                    kind,
                    kind,
                    int(bool(terms)),
                    limit,
                ),
            ).fetchall()
        return [_read_memory(row) for row in rows]

    def forget(self, memory_id: str) -> bool:
        """Remove one memory owned by the current user."""
        with self._connect() as connection:
            deleted = connection.execute(
                "DELETE FROM ems_memories WHERE user_id = ? AND id = ?",
                (self._user_id, memory_id),
            )
            return deleted.rowcount > 0

    def clear(self) -> int:
        """Remove all memories owned by the current user."""
        with self._connect() as connection:
            deleted = connection.execute(
                "DELETE FROM ems_memories WHERE user_id = ?", (self._user_id,)
            )
            return deleted.rowcount
