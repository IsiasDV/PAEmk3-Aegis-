"""Tests for the face embedder module."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from recognition.face_embed import FaceEmbedder


def test_face_embedder_train_and_recognize():
    """train() and recognize() work with synthetic face images."""
    embedder = FaceEmbedder(confidence_threshold=50.0)

    # Create synthetic face images for two people
    alice_faces = [np.full((100, 100), 100, dtype=np.uint8) for _ in range(3)]
    bob_faces = [np.full((100, 100), 200, dtype=np.uint8) for _ in range(3)]

    embedder.train({"alice": alice_faces, "bob": bob_faces})
    assert embedder.is_trained() is True
    assert set(embedder.enrolled_people) == {"alice", "bob"}

    # Recognize a face similar to alice's
    person_id, confidence = embedder.recognize(np.full((100, 100), 100, dtype=np.uint8))
    assert person_id == "alice"
    assert confidence <= 50.0


def test_face_embedder_recognize_unknown():
    """recognize() returns None for unknown faces when threshold is strict."""
    embedder = FaceEmbedder(confidence_threshold=50.0)

    # Train with a structured face image (gradient)
    alice_img = np.tile(np.linspace(0, 255, 100, dtype=np.uint8), (100, 1))
    alice_faces = [alice_img.copy() for _ in range(3)]
    embedder.train({"alice": alice_faces})

    # Very different face (inverted gradient)
    bob_img = np.tile(np.linspace(255, 0, 100, dtype=np.uint8), (100, 1))
    person_id, confidence = embedder.recognize(bob_img)
    assert person_id is None  # confidence above threshold -> unknown


def test_face_embedder_recognize_before_train():
    """recognize() before train() returns (None, inf)."""
    embedder = FaceEmbedder()
    person_id, confidence = embedder.recognize(np.zeros((50, 50), dtype=np.uint8))
    assert person_id is None
    assert confidence == float("inf")


def test_face_embedder_empty_training():
    """train() with no images doesn't crash."""
    embedder = FaceEmbedder()
    embedder.train({"alice": [], "bob": []})
    assert embedder.is_trained() is False
