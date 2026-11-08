"""Tests for Phase 6 — Memory & environment model.

Covers: episodic memory (who/what/when), people memory, and the
environment model built from real inspection. Verifies recall works
across a "restart" (new MemoryDB connection reading persisted data).
"""

from __future__ import annotations

import os
import tempfile

import pytest

from brain.memory_brain import MemoryBrain
from core.event_bus import EventBus
from memory.db import MemoryDB
from memory.episodic import EpisodicMemory
from memory.people import PeopleMemory
from memory.environment_model import EnvironmentModel


@pytest.fixture()
def tmp_dir():
    """A temporary directory used as the database location."""
    with tempfile.TemporaryDirectory() as td:
        yield td


@pytest.fixture()
def db(tmp_dir):
    """A MemoryDB pointing at a throwaway SQLite file."""
    db = MemoryDB(os.path.join(tmp_dir, "test.db"))
    yield db
    # Close the thread-local connection so the temp dir can be deleted
    # during pytest teardown (Windows file-lock cleanup).
    db.close()


@pytest.fixture()
def episodic(db):
    return EpisodicMemory(db)


@pytest.fixture()
def people(db):
    return PeopleMemory(db)


@pytest.fixture()
def environment_model(db):
    return EnvironmentModel(db)


class TestEpisodicMemory:
    def test_record_creates_episode(self, episodic):
        eid = episodic.record("keyboard.input", "hello", actor="user")
        assert eid > 0


    def test_cleanup_on_teardown(self, episodic, tmp_dir):
        # Ensure the MemoryDB connection is closed so the temp dir can be
        # deleted during pytest teardown (fixes Windows file-lock cleanup).
        from memory.db import MemoryDB
        db = episodic.db
        db.close()


    def test_recall_returns_newest_first(self, episodic):
        episodic.record("camera.frame", "frame captured", actor="system")
        episodic.record("user.said", "hi there", actor="user")
        episodes = episodic.recall()
        assert len(episodes) == 2
        assert episodes[0]["event_type"] == "user.said"
        assert episodes[0]["actor"] == "user"

    def test_recall_filters_by_event_type(self, episodic):
        episodic.record("camera.frame", "frame", actor="system")
        episodic.record("vision.scene_description", "a room", actor="system")
        results = episodic.recall(event_type="camera.frame")
        assert len(results) == 1
        assert results[0]["event_type"] == "camera.frame"

    def test_recall_filters_by_actor(self, episodic):
        episodic.record("camera.frame", "frame", actor="user")
        episodic.record("camera.frame", "frame", actor="system")
        results = episodic.recall(actor="user")
        assert len(results) == 1
        assert results[0]["actor"] == "user"

    def test_recall_empty_when_none_exist(self, episodic):
        assert episodic.recall() == []

    def test_clear_removes_all_episodes(self, episodic):
        episodic.record("camera.frame", "frame", actor="system")
        assert episodic.clear() == 1
        assert episodic.recall() == []


class TestPeopleMemory:
    def test_add_or_update_creates_person(self, people):
        people.add_or_update("p1", name="Alice", consent=True)
        rec = people.get("p1")
        assert rec is not None
        assert rec["name"] == "Alice"
        assert rec["consent"] is True

    def test_add_or_update_updates_existing(self, people):
        people.add_or_update("p1", name="Alice", consent=True)
        people.add_or_update("p1", name="Alicia", consent=False)
        rec = people.get("p1")
        assert rec["name"] == "Alicia"
        assert rec["consent"] is False

    def test_list_people_returns_all(self, people):
        people.add_or_update("p1", name="Alice", consent=True)
        people.add_or_update("p2", name="Bob", consent=False)
        assert sorted(p["person_id"] for p in people.list_people()) == ["p1", "p2"]

    def test_get_returns_none_for_unknown_person(self, people):
        assert people.get("nope") is None

    def test_delete_removes_person(self, people):
        people.add_or_update("p1", name="Alice", consent=True)
        assert people.delete("p1") is True
        assert people.get("p1") is None

    def test_delete_unknown_returns_false(self, people):
        assert people.delete("nope") is False

    def test_count(self, people):
        assert people.count() == 0
        people.add_or_update("p1", name="Alice", consent=True)
        assert people.count() == 1


class TestEnvironmentModel:
    def test_inspect_persists_and_retrieves(self, tmp_dir):
        path = os.path.join(tmp_dir, "env.db")
        db_a = MemoryDB(path)
        model = EnvironmentModel(db_a)
        result = model.inspect()
        assert result["system"]["os"] == "Windows"
        assert result["capabilities"]["cv2"] is True
        # Retrieve from a brand-new connection (= "restart")
        db_b = MemoryDB(path)
        retrieved = EnvironmentModel(db_b).get()
        assert retrieved is not None
        assert "inspected_at" in retrieved
        assert retrieved["system"]["ram_bytes"] >= 0
        db_a.close()
        db_b.close()

    def test_get_returns_none_when_not_persisted(self, tmp_dir):
        db = MemoryDB(os.path.join(tmp_dir, "empty.db"))
        model = EnvironmentModel(db)
        assert model.get() is None
        db.close()


class TestMemoryBrain:
    def test_memory_brain_records_keyboard_input(self, db, tmp_dir):
        from core.event_bus import EventBus
        bus = EventBus()
        mb = MemoryBrain(bus, db)
        mb.start()
        bus.publish("keyboard.input", {"text": "hello world", "source": "user"})
        mb.stop()
        episodes = mb.episodic.recall(limit=10)
        assert len(episodes) == 1
        assert episodes[0]["description"] == "hello world"
        assert episodes[0]["event_type"] == "keyboard.input"
        assert episodes[0]["actor"] == "user"
        db.close()

    def test_memory_brain_records_stt_transcription(self, db, tmp_dir):
        from core.event_bus import EventBus
        bus = EventBus()
        mb = MemoryBrain(bus, db)
        mb.start()
        bus.publish("stt.transcription", {"text": "what time is it", "source": "microphone"})
        mb.stop()
        episodes = mb.episodic.recall(event_type="stt.transcription")
        assert len(episodes) == 1
        assert episodes[0]["description"] == "what time is it"
        db.close()

    def test_memory_brain_records_scene_description(self, db, tmp_dir):
        from core.event_bus import EventBus
        bus = EventBus()
        mb = MemoryBrain(bus, db)
        mb.start()
        bus.publish("vision.scene_description", {"description": "a person at a desk", "frame_size": [640, 480]})
        mb.stop()
        episodes = mb.episodic.recall(event_type="vision.scene_description")
        assert len(episodes) == 1
        assert episodes[0]["description"] == "a person at a desk"
        assert episodes[0]["metadata"]["frame_size"] == [640, 480]
        db.close()

    def test_memory_brain_recall(self, db, tmp_dir):
        from core.event_bus import EventBus
        bus = EventBus()
        mb = MemoryBrain(bus, db)
        mb.start()
        bus.publish("keyboard.input", {"text": "remember the blue cup", "source": "user"})
        mb.stop()
        answer = mb.recall("blue cup")
        assert "blue cup" in answer
        db.close()

    def test_memory_brain_recall_empty(self, db, tmp_dir):
        from core.event_bus import EventBus
        bus = EventBus()
        mb = MemoryBrain(bus, db)
        mb.start()
        answer = mb.recall("anything at all")
        assert "don't remember" in answer.lower() or "no" in answer.lower()
        db.close()

    def test_memory_brain_enroll_and_recall_people(self, db, tmp_dir):
        from core.event_bus import EventBus
        bus = EventBus()
        mb = MemoryBrain(bus, db)
        mb.start()
        mb.enroll_person("p1", name="Alice", consent=True)
        mb.stop()
        people = mb.recall_people()
        assert "Alice" in people
        assert "p1" in people
        db.close()

    def test_memory_brain_survives_restart(self, tmp_dir):
        from core.event_bus import EventBus
        path = os.path.join(tmp_dir, "restart.db")
        # First session: record events
        db1 = MemoryDB(path)
        bus1 = EventBus()
        mb1 = MemoryBrain(bus1, db1)
        mb1.start()
        bus1.publish("keyboard.input", {"text": "this persists across restart", "source": "user"})
        mb1.enroll_person("restart_user", name="Restart User", consent=True)
        mb1.stop()
        db1.close()

        # Second session: simulate restart with new connection
        db2 = MemoryDB(path)
        bus2 = EventBus()
        mb2 = MemoryBrain(bus2, db2)
        mb2.start()
        episodes = mb2.episodic.recall(limit=10)
        assert len(episodes) == 1
        assert episodes[0]["description"] == "this persists across restart"
        people = mb2.recall_people()
        assert "Restart User" in people
        mb2.stop()
        db2.close()

    def test_memory_brain_import(self):
        from brain.memory_brain import MemoryBrain
        assert MemoryBrain is not None
