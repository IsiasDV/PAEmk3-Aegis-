"""Tests for the Phase 1 echo brain."""

from __future__ import annotations

from core.event_bus import EventBus
from brain.planner import EchoBrain


def test_echo_brain_echoes_input():
    """EchoBrain stores the last text received from a keyboard.input event."""
    bus = EventBus()
    brain = EchoBrain(bus)
    brain.start()

    bus.publish("keyboard.input", {"text": "hello world", "source": "stdin"})

    assert brain.last_text == "hello world"
    brain.stop()


def test_echo_brain_ignores_empty_text():
    """EchoBrain handles events with no text field gracefully."""
    bus = EventBus()
    brain = EchoBrain(bus)
    brain.start()

    bus.publish("keyboard.input", {})

    assert brain.last_text == ""
    brain.stop()
