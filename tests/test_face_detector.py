"""Tests for the face detector module."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from recognition.face_detect import FaceDetector


def test_face_detector_load_raises_if_cascade_missing(tmp_path):
    """FaceDetector.load() raises FileNotFoundError if cascade file missing."""
    missing = tmp_path / "nonexistent.xml"
    detector = FaceDetector(cascade_path=str(missing))
    try:
        detector.load()
        assert False, "expected FileNotFoundError"
    except FileNotFoundError:
        pass


def test_face_detector_detects_faces(monkeypatch, tmp_path):
    """detect() returns bounding boxes for detected faces."""
    cascade_file = tmp_path / "haarcascade.xml"
    cascade_file.write_bytes(b"\x00" * 100)

    detector = FaceDetector(cascade_path=str(cascade_file))

    # Mock the CascadeClassifier
    mock_cascade = MagicMock()
    mock_cascade.empty.return_value = False
    mock_cascade.detectMultiScale.return_value = np.array(
        [[10, 20, 50, 60], [100, 120, 40, 40]], dtype=np.int32
    )

    with patch("recognition.face_detect.cv2.CascadeClassifier", return_value=mock_cascade):
        detector.load()
        frame = np.zeros((240, 320, 3), dtype=np.uint8)
        faces = detector.detect(frame)

    assert len(faces) == 2
    assert faces[0] == {"x": 10, "y": 20, "w": 50, "h": 60, "confidence": 1.0}
    assert faces[1] == {"x": 100, "y": 120, "w": 40, "h": 40, "confidence": 1.0}


def test_face_detector_detects_no_faces(monkeypatch, tmp_path):
    """detect() returns empty list when no faces found."""
    cascade_file = tmp_path / "haarcascade.xml"
    cascade_file.write_bytes(b"\x00" * 100)

    detector = FaceDetector(cascade_path=str(cascade_file))

    mock_cascade = MagicMock()
    mock_cascade.empty.return_value = False
    mock_cascade.detectMultiScale.return_value = np.array([], dtype=np.int32).reshape(0, 4)

    with patch("recognition.face_detect.cv2.CascadeClassifier", return_value=mock_cascade):
        detector.load()
        frame = np.zeros((240, 320, 3), dtype=np.uint8)
        faces = detector.detect(frame)

    assert faces == []


def test_face_detector_loaded_property(tmp_path):
    """loaded property reflects whether cascade is loaded."""
    cascade_file = tmp_path / "haarcascade.xml"
    cascade_file.write_bytes(b"\x00" * 100)

    detector = FaceDetector(cascade_path=str(cascade_file))
    assert detector.loaded is False

    mock_cascade = MagicMock()
    mock_cascade.empty.return_value = False
    with patch("recognition.face_detect.cv2.CascadeClassifier", return_value=mock_cascade):
        detector.load()
        assert detector.loaded is True
