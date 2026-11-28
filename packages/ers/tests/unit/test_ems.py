from concurrent.futures import ThreadPoolExecutor

import pytest

from ovic_eon.ems import EmotionalMemory


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
