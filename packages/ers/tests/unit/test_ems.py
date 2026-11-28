import sqlite3
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from datetime import timedelta

import pytest

from ovic_eon.ems import EmotionalMemory, EMSError


def test_recall_persists_and_ranks_matching_terms(tmp_path):
    database = tmp_path / "memory.sqlite3"
    memory = EmotionalMemory(database, user_id="a")
    strongest = memory.remember_interaction("Camera calibration completed.")
    partial = memory.remember_interaction("Camera battery replaced.")
    memory.remember_interaction("Scheduled a maintenance visit.")

    reopened = EmotionalMemory(database, user_id="a")
    assert reopened.recall("CAMERA camera calibration") == [strongest, partial]
    assert reopened.recall("cam") == []
    assert reopened.recall("!!!") == []
    assert reopened.recall(limit=1)[0].text == "Scheduled a maintenance visit."


def test_preferences_require_confirmation_and_replace_in_place(tmp_path):
    memory = EmotionalMemory(tmp_path / "memory.sqlite3", user_id="a")
    with pytest.raises(ValueError, match="confirmation"):
        memory.confirm_preference("pace", "Fast", confirmed=False)
    assert memory.get_preference("pace") is None

    first = memory.confirm_preference("pace", "Fast", confirmed=True)
    updated = memory.confirm_preference("pace", "One step at a time", confirmed=True)
    assert first.id == updated.id
    assert first.created_at == updated.created_at
    assert memory.get_preference("pace") == updated
    assert memory.recall("pace", kind="preference") == [updated]
    assert memory.recall("fast") == []
    assert memory.recall(kind="interaction") == []


def test_users_cannot_recall_or_delete_each_others_memories(tmp_path):
    database = tmp_path / "memory.sqlite3"
    a = EmotionalMemory(database, user_id="a")
    b = EmotionalMemory(database, user_id="b")
    record = a.remember_interaction("Camera setup")
    a.confirm_preference("pace", "Slow", confirmed=True)
    b.confirm_preference("pace", "Fast", confirmed=True)

    assert b.recall("camera") == []
    assert b.get_preference("pace").text == "Fast"
    assert b.forget(record.id) is False
    assert a.forget(record.id) is True
    assert a.clear() == 1
    assert a.recall() == []
    assert len(b.recall()) == 1


def test_concurrent_writes_keep_one_preference(tmp_path):
    memory = EmotionalMemory(tmp_path / "memory.sqlite3", user_id="a")

    def save(value):
        return memory.confirm_preference("pace", value, confirmed=True)

    with ThreadPoolExecutor(max_workers=4) as executor:
        results = list(executor.map(save, ["Slow", "Fast", "Normal", "Steady"]))

    assert len({item.id for item in results}) == 1
    assert len(memory.recall(kind="preference")) == 1


def test_encrypted_store_reopens_and_rejects_missing_or_wrong_keys(tmp_path):
    database = tmp_path / "protected.sqlite3"
    key = bytes(range(32))
    a = EmotionalMemory(database, user_id="operator", encryption_key=key)
    token = "private-calibration-finding"
    note = a.remember_interaction(token)
    setting = a.confirm_preference("private-reply-style", "private setting", confirmed=True)
    replacement = a.confirm_preference("private-reply-style", "new private setting", confirmed=True)
    assert replacement.id == setting.id

    raw = database.read_bytes()
    assert token.encode() not in raw
    assert b"private-reply-style" not in raw
    assert b"new private setting" not in raw
    with pytest.raises(EMSError, match="encryption mode"):
        EmotionalMemory(database, user_id="operator")
    with pytest.raises(EMSError, match="Incorrect"):
        EmotionalMemory(database, user_id="operator", encryption_key=bytes(32))

    reopened = EmotionalMemory(database, user_id="operator", encryption_key=key)
    assert reopened.recall("calibration") == [note]
    assert reopened.get_preference("private-reply-style") == replacement
    other = EmotionalMemory(database, user_id="other", encryption_key=key)
    assert other.export_memories() == []
    assert other.forget(note.id) is False


def test_encrypted_storage_rejects_plaintext_and_modified_ciphertext(tmp_path):
    database = tmp_path / "protected.sqlite3"
    memory = EmotionalMemory(database, user_id="a", encryption_key=bytes(range(32)))
    record = memory.remember_interaction("Calibration completed")
    with closing(sqlite3.connect(database)) as connection, connection:
        with pytest.raises(sqlite3.IntegrityError, match="encrypted payloads"):
            connection.execute("UPDATE ems_memories SET text = 'plaintext'")
        connection.execute("UPDATE ems_memories SET text = ? WHERE id = ?", (bytes(64), record.id))
    with pytest.raises(EMSError, match="authenticated decryption"):
        memory.recall()


def test_expiry_and_interaction_cap_preserve_preferences(tmp_path):
    database = tmp_path / "memory.sqlite3"
    a = EmotionalMemory(
        database, user_id="a", interaction_ttl=timedelta(days=1), max_interactions=2
    )
    b = EmotionalMemory(database, user_id="b")
    other = b.remember_interaction("other operator")
    pref = a.confirm_preference("pace", "Slow", confirmed=True)
    old = a.remember_interaction("old")
    mid = a.remember_interaction("middle")
    new = a.remember_interaction("new")
    assert new.expires_at == new.created_at + timedelta(days=1)
    assert a.forget(old.id) is False
    assert a.export_memories() == [new, mid, pref]

    with closing(sqlite3.connect(database)) as connection, connection:
        connection.execute(
            "UPDATE ems_memories SET expires_at = '2000-01-01T00:00:00+00:00' WHERE id = ?",
            (mid.id,),
        )
    assert a.recall("middle") == []
    assert a.export_memories() == [new, pref]
    assert a.purge_expired() == 1
    assert a.purge_expired() == 0
    assert b.export_memories() == [other]


def test_preexisting_sqlite_schema_is_upgraded_without_data_loss(tmp_path):
    database = tmp_path / "legacy.sqlite3"
    with closing(sqlite3.connect(database)) as connection, connection:
        connection.executescript("""
            CREATE TABLE ems_memories (
                id TEXT PRIMARY KEY, user_id TEXT NOT NULL, kind TEXT NOT NULL,
                preference_key TEXT, text TEXT NOT NULL, search_text TEXT NOT NULL,
                created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
                UNIQUE (user_id, preference_key)
            );
            INSERT INTO ems_memories VALUES ('a1', 'a', 'preference', 'pace', 'Slow',
                 ' pace slow ', '2026-01-01T00:00:00+00:00', '2026-01-01T00:00:00+00:00');
        """)
    with pytest.raises(EMSError, match="new database"):
        EmotionalMemory(database, user_id="a", encryption_key=bytes(32))
    memory = EmotionalMemory(database, user_id="a")
    assert memory.get_preference("pace").id == "a1"
    assert memory.recall("slow")[0].expires_at is None
    assert memory.confirm_preference("pace", "Fast", confirmed=True).id == "a1"


def test_preference_cap_allows_updates_and_is_per_user(tmp_path):
    database = tmp_path / "capped.sqlite3"
    a = EmotionalMemory(database, user_id="a", max_preferences=1)
    b = EmotionalMemory(database, user_id="b", max_preferences=1)

    a.confirm_preference("pace", "Slow", confirmed=True)
    with pytest.raises(EMSError, match="preference limit"):
        a.confirm_preference("language", "English", confirmed=True)
    assert a.confirm_preference("pace", "Fast", confirmed=True).text == "Fast"
    assert b.confirm_preference("language", "English", confirmed=True).text == "English"


def test_sqlite_backup_restores_encrypted_records_with_original_key(tmp_path):
    database = tmp_path / "memory.sqlite3"
    backup = tmp_path / "backup.sqlite3"
    key = bytes(range(32))
    memory = EmotionalMemory(database, user_id="operator", encryption_key=key)
    saved = memory.remember_interaction("Calibration result")
    with closing(sqlite3.connect(database)) as src, closing(sqlite3.connect(backup)) as dst:
        src.backup(dst)

    restored = EmotionalMemory(backup, user_id="operator", encryption_key=key)
    assert restored.recall("calibration") == [saved]
