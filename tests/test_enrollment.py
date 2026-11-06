"""Tests for the enrollment manager module."""

from __future__ import annotations

from unittest.mock import MagicMock

import numpy as np
import pytest

from recognition.enrollment import EnrollmentManager
from recognition.identity_store import IdentityStore


def _make_store_and_embedder(tmp_path):
    store = IdentityStore(str(tmp_path / "identities.json"))
    store.load()
    embedder = MagicMock()
    return store, embedder


def test_enrollment_request_asks_for_consent(tmp_path):
    """request_enrollment returns a consent prompt."""
    store, embedder = _make_store_and_embedder(tmp_path)
    manager = EnrollmentManager(store, MagicMock(), embedder)

    prompt = manager.request_enrollment("alice")
    assert "alice" in prompt
    assert "consent" in prompt.lower()
    assert manager.is_enrolling() is True
    assert manager.pending_person() == "alice"
    assert manager.consent_given() is False


def test_enrollment_grant_and_deny_consent(tmp_path):
    """grant_consent and deny_consent work correctly."""
    store, embedder = _make_store_and_embedder(tmp_path)
    manager = EnrollmentManager(store, MagicMock(), embedder)

    manager.request_enrollment("alice")
    assert manager.consent_given() is False

    manager.grant_consent()
    assert manager.consent_given() is True

    manager.deny_consent()
    assert manager.consent_given() is False
    assert manager.is_enrolling() is False  # denied cancels enrollment


def test_enrollment_add_sample_requires_consent(tmp_path):
    """add_sample() returns False without consent."""
    store, embedder = _make_store_and_embedder(tmp_path)
    manager = EnrollmentManager(store, MagicMock(), embedder)

    manager.request_enrollment("alice")
    sample = np.zeros((50, 50), dtype=np.uint8)
    assert manager.add_sample(sample) is False

    manager.grant_consent()
    assert manager.add_sample(sample) is True
    assert manager.sample_count() == 1


def test_enrollment_complete_requires_min_samples(tmp_path):
    """complete_enrollment() fails if not enough samples."""
    store, embedder = _make_store_and_embedder(tmp_path)
    manager = EnrollmentManager(store, MagicMock(), embedder, min_enrollment_samples=3)

    manager.request_enrollment("alice")
    manager.grant_consent()
    manager.add_sample(np.zeros((50, 50), dtype=np.uint8))
    manager.add_sample(np.zeros((50, 50), dtype=np.uint8))

    result = manager.complete_enrollment()
    assert "Not enough samples" in result
    assert manager.is_enrolling() is False


def test_enrollment_complete_success(tmp_path):
    """complete_enrollment() stores embeddings and trains embedder."""
    store, embedder = _make_store_and_embedder(tmp_path)
    manager = EnrollmentManager(store, MagicMock(), embedder, min_enrollment_samples=2)

    manager.request_enrollment("alice")
    manager.grant_consent()
    sample1 = np.full((50, 50), 100, dtype=np.uint8)
    sample2 = np.full((50, 50), 100, dtype=np.uint8)
    manager.add_sample(sample1)
    manager.add_sample(sample2)

    result = manager.complete_enrollment()
    assert "Enrollment complete" in result
    assert store.is_enrolled("alice")
    assert store.has_consent("alice")
    assert len(store.get_embeddings("alice")) == 2
    embedder.train.assert_called_once()
    assert manager.is_enrolling() is False


def test_enrollment_cancel(tmp_path):
    """cancel_enrollment() clears pending state without saving."""
    store, embedder = _make_store_and_embedder(tmp_path)
    manager = EnrollmentManager(store, MagicMock(), embedder)

    manager.request_enrollment("alice")
    manager.grant_consent()
    manager.add_sample(np.zeros((50, 50), dtype=np.uint8))

    result = manager.cancel_enrollment()
    assert "cancelled" in result.lower()
    assert manager.is_enrolling() is False
    assert manager.sample_count() == 0
    assert store.is_enrolled("alice") is False  # nothing saved
