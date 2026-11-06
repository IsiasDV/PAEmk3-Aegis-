"""Tests for the camera perception module.

Tests use a monkeypatched cv2.VideoCapture so they run without a real camera.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from core.event_bus import EventBus
from perception.camera import Camera


class _FakeCap:
    """Fake cv2.VideoCapture that yields synthetic frames."""

    def __init__(self, device_index: int) -> None:
        self.opened = True
        self.device_index = device_index
        self._frames = 0

    def isOpened(self) -> bool:
        return self.opened

    def set(self, prop: int, value: float) -> bool:
        return True

    def read(self):
        self._frames += 1
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        frame[:] = [self._frames % 256, 128, 64]
        return True, frame

    def release(self) -> None:
        self.opened = False


def test_camera_starts_and_publishes_frames(monkeypatch):
    """Camera.start() opens capture and publishes camera.frame events."""
    bus = EventBus()
    captured: list[dict] = []
    bus.subscribe("camera.frame", captured.append)

    fake_cap = _FakeCap(0)

    with patch("perception.camera.cv2.VideoCapture", return_value=fake_cap):
        cam = Camera(bus, device_index=0, fps=60)
        cam.start()

        # Wait for at least one frame
        deadline = __import__("time").time() + 3.0
        while len(captured) == 0 and __import__("time").time() < deadline:
            __import__("time").sleep(0.01)

        cam.stop()

    assert len(captured) >= 1, "no camera.frame events published"
    ev = captured[0]
    assert "frame" in ev
    assert "meta" in ev
    assert ev["meta"]["device_index"] == 0
    assert ev["meta"]["frame_index"] >= 1
    assert ev["frame"].shape == (480, 640, 3)
    assert not cam.running


def test_camera_stop_without_start_is_safe():
    """Camera.stop() before start() is safe."""
    bus = EventBus()
    cam = Camera(bus, device_index=0)
    cam.stop()  # should not raise
    assert not cam.running


def test_camera_open_failure_raises(monkeypatch):
    """Camera.start() raises RuntimeError if the camera cannot be opened."""
    bus = EventBus()

    class DeadCap:
        def isOpened(self) -> bool:
            return False

        def set(self, prop: int, value: float) -> bool:
            return True

        def read(self):
            return False, None

        def release(self) -> None:
            pass

    with patch("perception.camera.cv2.VideoCapture", return_value=DeadCap()):
        cam = Camera(bus, device_index=99)
        try:
            cam.start()
            assert False, "expected RuntimeError"
        except RuntimeError:
            pass


def test_camera_capture_frame_without_start():
    """capture_frame() returns None when camera not started."""
    bus = EventBus()
    cam = Camera(bus, device_index=0)
    assert cam.capture_frame() is None


def test_camera_register_frame_callback(monkeypatch):
    """register_frame_callback receives (frame, meta) tuples."""
    bus = EventBus()
    calls: list[tuple] = []
    fake_cap = _FakeCap(0)

    with patch("perception.camera.cv2.VideoCapture", return_value=fake_cap):
        cam = Camera(bus, device_index=0, fps=60)
        cam.register_frame_callback(lambda frame, meta: calls.append((frame, meta)))
        cam.start()

        deadline = __import__("time").time() + 3.0
        while len(calls) == 0 and __import__("time").time() < deadline:
            __import__("time").sleep(0.01)

        cam.stop()

    assert len(calls) >= 1
    frame, meta = calls[0]
    assert isinstance(frame, np.ndarray)
    assert "frame_index" in meta
