"""Local, user-scoped Emotional Memory System for the OVIC EON SDK."""

from __future__ import annotations

import hmac
import json
import os
import secrets
import sqlite3
import unicodedata
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Literal, cast
from uuid import uuid4

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

MemoryKind = Literal["interaction", "preference"]

__all__ = ["EMSError", "EmotionalMemory", "Memory", "MemoryKind"]

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
    expires_at TEXT,
    CHECK ((kind = 'interaction') = (preference_key IS NULL)),
    UNIQUE (user_id, preference_key)
);
CREATE INDEX IF NOT EXISTS ems_memories_by_user
ON ems_memories (user_id, updated_at DESC, id);
CREATE TABLE IF NOT EXISTS ems_store_config (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    salt BLOB,
    key_check BLOB
);
"""

_PROTECTED_TRIGGERS = (
    """CREATE TRIGGER IF NOT EXISTS ems_require_ciphertext_insert
       BEFORE INSERT ON ems_memories WHEN typeof(NEW.text) != 'blob'
       BEGIN SELECT RAISE(ABORT, 'EMS store requires encrypted payloads'); END""",
    """CREATE TRIGGER IF NOT EXISTS ems_require_ciphertext_update
       BEFORE UPDATE ON ems_memories WHEN typeof(NEW.text) != 'blob'
       BEGIN SELECT RAISE(ABORT, 'EMS store requires encrypted payloads'); END""",
)


class EMSError(RuntimeError):
    """EMS storage or data-integrity failure."""


@dataclass(frozen=True, slots=True)
class Memory:
    """An interaction summary or explicitly confirmed preference."""

    id: str
    kind: MemoryKind
    text: str
    preference_key: str | None
    created_at: datetime
    updated_at: datetime
    expires_at: datetime | None = None


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


def _timestamp(value: datetime) -> str:
    return value.isoformat(timespec="microseconds")


class EmotionalMemory:
    """Store and retrieve text memories for one application-resolved user.

    The caller supplies an authorized user ID and chooses which interaction
    summaries may be saved. This class performs no automatic collection.
    """

    def __init__(
        self,
        database: str | Path,
        *,
        user_id: str,
        encryption_key: bytes | None = None,
        interaction_ttl: timedelta | None = None,
        max_interactions: int | None = None,
        max_preferences: int | None = None,
    ) -> None:
        self._user_id = _required_text(user_id, "user_id", 128)
        if user_id != self._user_id:
            raise ValueError("user_id must not start or end with whitespace")
        if encryption_key is not None and (
            not isinstance(encryption_key, bytes) or len(encryption_key) != 32
        ):
            raise ValueError("encryption_key must be exactly 32 bytes")
        if interaction_ttl is not None and (
            not isinstance(interaction_ttl, timedelta)
            or not timedelta(0) < interaction_ttl <= timedelta(days=36500)
        ):
            raise ValueError("interaction_ttl must be positive and at most 36,500 days")
        for name, cap in (
            ("max_interactions", max_interactions),
            ("max_preferences", max_preferences),
        ):
            if cap is not None and (type(cap) is not int or cap < 1):
                raise ValueError(f"{name} must be a positive integer")
        self._database = Path(database).resolve()
        self._interaction_ttl = interaction_ttl
        self._max_interactions = max_interactions
        self._max_preferences = max_preferences
        self._cipher: AESGCM | None = None
        self._index_key: bytes | None = None
        try:
            descriptor = os.open(self._database, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError:
            pass
        else:
            os.close(descriptor)
        self._initialize(encryption_key)

    def _initialize(self, key: bytes | None) -> None:
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            legacy_table = connection.execute(
                "SELECT 1 FROM sqlite_schema WHERE type = 'table' AND name = 'ems_memories'"
            ).fetchone()
            for statement in _SCHEMA.strip().rstrip(";").split(";"):
                connection.execute(statement)
            columns = {row["name"] for row in connection.execute("PRAGMA table_info(ems_memories)")}
            if "expires_at" not in columns:
                connection.execute("ALTER TABLE ems_memories ADD COLUMN expires_at TEXT")
            config = connection.execute("SELECT * FROM ems_store_config WHERE id = 1").fetchone()
            if config is None:
                if key is not None and legacy_table is not None:
                    raise EMSError("Use a new database file for encrypted EMS storage.")
                salt = secrets.token_bytes(32) if key is not None else None
                check = self._configure_key(key, salt)
                connection.execute(
                    "INSERT INTO ems_store_config (id, salt, key_check) VALUES (1, ?, ?)",
                    (salt, check),
                )
                if key is not None:
                    for trigger in _PROTECTED_TRIGGERS:
                        connection.execute(trigger)
            else:
                check = self._configure_key(key, config["salt"])
                if check is not None and not hmac.compare_digest(check, config["key_check"]):
                    raise EMSError("Incorrect EMS encryption key.")

    def _configure_key(self, key: bytes | None, salt: bytes | None) -> bytes | None:
        if (key is None) != (salt is None):
            raise EMSError("EMS database encryption mode does not match the supplied key.")
        if key is None or salt is None:
            return None
        root = hmac.digest(salt, key, "sha256")
        self._cipher = AESGCM(hmac.digest(root, b"eon-ems-payload-v1", "sha256"))
        self._index_key = hmac.digest(root, b"eon-ems-index-v1", "sha256")
        return hmac.digest(root, b"eon-ems-key-check-v1", "sha256")

    def _index(self, namespace: str, value: str) -> str:
        if self._index_key is None:
            return value
        data = f"{namespace}\x00{self._user_id}\x00{value}".encode()
        return hmac.digest(self._index_key, data, "sha256").hex()

    def _aad(self, memory_id: str, kind: str, key: str | None) -> bytes:
        return json.dumps([self._user_id, memory_id, kind, key]).encode()

    def _protect(
        self, memory_id: str, kind: str, stored_key: str | None, key: str | None, text: str
    ) -> str | bytes:
        if self._cipher is None:
            return text
        nonce = secrets.token_bytes(12)
        return nonce + self._cipher.encrypt(
            nonce, json.dumps([key, text]).encode(), self._aad(memory_id, kind, stored_key)
        )

    def _read_memory(self, row: sqlite3.Row) -> Memory:
        key, text = row["preference_key"], row["text"]
        if self._cipher is not None:
            try:
                key, text = json.loads(
                    self._cipher.decrypt(
                        text[:12], text[12:], self._aad(row["id"], row["kind"], key)
                    )
                )
            except (InvalidTag, ValueError, TypeError) as exc:
                raise EMSError("EMS record failed authenticated decryption.") from exc
        expiry = row["expires_at"]
        return Memory(
            id=row["id"],
            kind=cast(MemoryKind, row["kind"]),
            text=text,
            preference_key=key,
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
            expires_at=datetime.fromisoformat(expiry) if expiry else None,
        )

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
        tokens = dict.fromkeys(_terms(f"{key or ''} {value}"))
        search_text = " " + " ".join(self._index("term", token) for token in tokens) + " "
        stored_key = self._index("preference", key) if key is not None else None
        memory_id = uuid4().hex
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            now = datetime.now(UTC)
            timestamp = _timestamp(now)
            expiry = (
                _timestamp(now + self._interaction_ttl)
                if kind == "interaction" and self._interaction_ttl is not None
                else None
            )
            if stored_key is not None:
                existing = connection.execute(
                    "SELECT id FROM ems_memories WHERE user_id = ? AND preference_key = ?",
                    (self._user_id, stored_key),
                ).fetchone()
                if existing is not None:
                    memory_id = existing["id"]
                elif self._max_preferences is not None:
                    count = connection.execute(
                        "SELECT count(*) FROM ems_memories WHERE user_id = ? AND kind = 'preference'",
                        (self._user_id,),
                    ).fetchone()[0]
                    if count >= self._max_preferences:
                        raise EMSError("EMS preference limit reached for this user.")
            payload = self._protect(memory_id, kind, stored_key, key, value)
            connection.execute(
                """
                INSERT INTO ems_memories
                (id, user_id, kind, preference_key, text, search_text, created_at, updated_at,
                 expires_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT (user_id, preference_key) DO UPDATE SET
                    text = excluded.text,
                    search_text = excluded.search_text,
                    updated_at = excluded.updated_at
                """,
                (
                    memory_id,
                    self._user_id,
                    kind,
                    stored_key,
                    payload,
                    search_text,
                    timestamp,
                    timestamp,
                    expiry,
                ),
            )
            if kind == "interaction":
                self._purge_expired(connection, timestamp)
                if self._max_interactions is not None:
                    connection.execute(
                        """
                        DELETE FROM ems_memories WHERE user_id = ? AND id IN (
                            SELECT id FROM ems_memories
                            WHERE user_id = ? AND kind = 'interaction' AND id <> ?
                            ORDER BY updated_at DESC, id LIMIT -1 OFFSET ?
                        )
                        """,
                        (self._user_id, self._user_id, memory_id, self._max_interactions - 1),
                    )
            row = connection.execute(
                "SELECT * FROM ems_memories WHERE user_id = ? AND id = ?",
                (self._user_id, memory_id),
            ).fetchone()
            return self._read_memory(row)

    def get_preference(self, key: str) -> Memory | None:
        """Fetch the current confirmed value for a preference key."""
        key = _required_text(key, "key", 128)
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM ems_memories WHERE user_id = ? AND preference_key = ?",
                (self._user_id, self._index("preference", key)),
            ).fetchone()
        return None if row is None else self._read_memory(row)

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
                      AND (expires_at IS NULL OR expires_at > ?)
                )
                WHERE relevance >= ?
                ORDER BY relevance DESC, updated_at DESC, id
                LIMIT ?
                """,
                (
                    *(f" {self._index('term', term)} " for term in terms),
                    self._user_id,
                    kind,
                    kind,
                    _timestamp(datetime.now(UTC)),
                    int(bool(terms)),
                    limit,
                ),
            ).fetchall()
        return [self._read_memory(row) for row in rows]

    def export_memories(self) -> list[Memory]:
        """Return the current user's unexpired memories for a data export."""
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM ems_memories WHERE user_id = ?
                AND (expires_at IS NULL OR expires_at > ?)
                ORDER BY updated_at DESC, id
                """,
                (self._user_id, _timestamp(datetime.now(UTC))),
            )
            return [self._read_memory(row) for row in rows]

    def _purge_expired(self, connection: sqlite3.Connection, cutoff: str) -> int:
        return connection.execute(
            "DELETE FROM ems_memories WHERE user_id = ? AND expires_at <= ?",
            (self._user_id, cutoff),
        ).rowcount

    def purge_expired(self) -> int:
        """Delete expired rows for the current user."""
        with self._connect() as connection:
            return self._purge_expired(connection, _timestamp(datetime.now(UTC)))

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
