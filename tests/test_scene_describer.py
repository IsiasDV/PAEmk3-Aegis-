"""Tests for the scene describer module."""

from __future__ import annotations

import numpy as np
import pytest

from core.event_bus import EventBus
from vision.scene_describer import SceneDescriber


def test_simple_describer_produces_description():
    """Simple describer returns a nonempty, sensible description."""
    bus = EventBus()
    captured: list[dict] = []
    bus.subscribe("vision.scene_description", captured.append)

    describer = SceneDescriber(bus, use_vlm=False)

    # Bright red image
    frame = np.zeros((100, 100, 3), dtype=np.uint8)
    frame[:] = [0, 0, 255]  # BGR red

    desc = describer.describe(frame)

    assert isinstance(desc, str)
    assert len(desc) > 0
    assert "red" in desc.lower() or "bright" in desc.lower()
    assert "100x100" in desc
    assert len(captured) == 1
    assert captured[0]["source"] == "simple"
    assert "description" in captured[0]


def test_simple_describer_handles_dark_image():
    """Simple describer handles a dark image."""
    bus = EventBus()
    describer = SceneDescriber(bus, use_vlm=False)

    frame = np.zeros((50, 50, 3), dtype=np.uint8)  # all black
    desc = describer.describe(frame)

    assert isinstance(desc, str)
    assert len(desc) > 0
    assert "dim" in desc.lower() or "50x50" in desc


def test_simple_describer_handles_colorful_image():
    """Simple describer handles a colorful image."""
    bus = EventBus()
    describer = SceneDescriber(bus, use_vlm=False)

    # Gradient image with multiple colors
    frame = np.zeros((100, 100, 3), dtype=np.uint8)
    frame[:, :, 0] = np.linspace(0, 255, 100).reshape(100, 1)  # blue gradient
    frame[:, :, 1] = 128
    frame[:, :, 2] = 64

    desc = describer.describe(frame)
    assert isinstance(desc, str)
    assert len(desc) > 0


def test_describer_counts_descriptions():
    """description_count increments on each describe() call."""
    bus = EventBus()
    describer = SceneDescriber(bus, use_vlm=False)

    frame = np.zeros((50, 50, 3), dtype=np.uint8)
    describer.describe(frame)
    describer.describe(frame)
    assert describer.description_count == 2


def test_vlm_not_available():
    """VLM path reports unavailable on this device."""
    bus = EventBus()
    describer = SceneDescriber(bus, use_vlm=True)
    assert describer.vlm_available is False
    assert describer.vlm_reason is not None
    assert "UNVERIFIED" in describer.vlm_reason or "VLM" in describer.vlm_reason


def test_describer_falls_back_to_simple_when_vlm_unavailable():
    """With use_vlm=True but no VLM, describe() still works via simple fallback."""
    bus = EventBus()
    describer = SceneDescriber(bus, use_vlm=True)

    frame = np.zeros((100, 100, 3), dtype=np.uint8)
    frame[:] = [0, 128, 0]  # green
    desc = describer.describe(frame)

    assert isinstance(desc, str)
    assert len(desc) > 0
    assert describer.description_count == 1
