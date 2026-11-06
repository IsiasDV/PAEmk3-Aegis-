"""Tests for the identity store module."""

from __future__ import annotations

import json
import os
from pathlib import Path

import numpy as np
import pytest

from recognition.identity_store import IdentityStore


def test_identity_store_load_and_save(tmp_path):
    """IdentityStore can load from and save to disk."""
    store_path = tmp_path / "identities.json"
    store = IdentityStore(str(store_path))
    store.load()
    assert store.person_count() == 0

    store.add_embedding("alice", [0.1, 0.2, 0.3])
    store.set_consent("alice", True)
    store.save()

    # Reload and verify persistence
    store2 = IdentityStore(str(store_path))
    store2.load()
    assert store2.is_enrolled("alice")
    assert store2.has_consent("alice")
    assert store2.get_embeddings("alice") == [[0.1, 0.2, 0.3]]


def test_identity_store_list_people(tmp_path):
    """list_people returns sorted enrolled person IDs."""
    store_path = tmp_path / "identities.json"
    store = IdentityStore(str(store_path))
    store.load()

    store.add_embedding("bob", [0.1, 0.2])
    store.add_embedding("alice", [0.3, 0.4])
    store.add_embedding("charlie", [0.5, 0.6])
    store.save()

    people = store.list_people()
    assert people == ["alice", "bob", "charlie"]


def test_identity_store_delete_person(tmp_path):
    """delete_person removes a person and returns True; returns False if not found."""
    store_path = tmp_path / "identities.json"
    store = IdentityStore(str(store_path))
    store.load()

    store.add_embedding("alice", [0.1, 0.2])
    store.save()

    assert store.delete_person("alice") is True
    assert store.is_enrolled("alice") is False
    assert store.delete_person("alice") is False  # already deleted


def test_identity_store_wipe_all(tmp_path):
    """wipe_all removes all people and returns the count."""
    store_path = tmp_path / "identities.json"
    store = IdentityStore(str(store_path))
    store.load()

    store.add_embedding("alice", [0.1])
    store.add_embedding("bob", [0.2])
    store.add_embedding("charlie", [0.3])
    store.save()

    count = store.wipe_all()
    assert count == 3
    assert store.person_count() == 0
    assert store.list_people() == []


def test_identity_store_consent(tmp_path):
    """has_consent and set_consent work correctly."""
    store_path = tmp_path / "identities.json"
    store = IdentityStore(str(store_path))
    store.load()

    assert store.has_consent("alice") is False
    store.add_embedding("alice", [0.1])
    store.set_consent("alice", True)
    assert store.has_consent("alice") is True
    store.set_consent("alice", False)
    assert store.has_consent("alice") is False


def test_identity_store_get_embeddings_empty_for_unknown(tmp_path):
    """get_embeddings returns empty list for unknown person."""
    store_path = tmp_path / "identities.json"
    store = IdentityStore(str(store_path))
    store.load()

    assert store.get_embeddings("unknown") == []


def test_identity_store_json_format(tmp_path):
    """The saved JSON file has the expected structure."""
    store_path = tmp_path / "identities.json"
    store = IdentityStore(str(store_path))
    store.load()
    store.add_embedding("alice", [0.1, 0.2, 0.3])
    store.set_consent("alice", True)
    store.save()

    raw = json.loads(Path(store_path).read_text(encoding="utf-8"))
    assert "alice" in raw
    assert raw["alice"]["embeddings"] == [[0.1, 0.2, 0.3]]
    assert raw["alice"]["consent"] is True
