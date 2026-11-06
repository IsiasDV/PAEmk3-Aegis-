"""Tests for the keyboard input perception module."""

from __future__ import annotations

import threading
import time

from core.event_bus import EventBus
from perception.keyboard import KeyboardInput


def test_keyboard_publishes_input_events(monkeypatch):
    """KeyboardInput publishes each typed line as a keyboard.input event."""
    bus = EventBus()
    captured: list[dict] = []
    bus.subscribe("keyboard.input", captured.append)

    kb = KeyboardInput(bus, kill_switch_key="q")

    # Feed input lines then 'q' to stop.
    inputs = iter(["hello", "world", "q"])
    monkeypatch.setattr("builtins.input", lambda _="": next(inputs))

    kb.start()
    # Wait for the background thread to process all three lines.
    deadline = time.time() + 5.0
    while len(captured) < 2 and time.time() < deadline:
        time.sleep(0.05)
    kb.stop()

    assert len(captured) == 2
    assert captured[0]["text"] == "hello"
    assert captured[1]["text"] == "world"
    assert not kb.running


def test_keyboard_kill_switch_triggers_callbacks(monkeypatch):
    """Pressing the kill switch key stops the loop and runs kill callbacks."""
    bus = EventBus()
    kb = KeyboardInput(bus, kill_switch_key="q")

    kill_ran = threading.Event()
    kb.register_kill_callback(lambda: kill_ran.set())

    monkeypatch.setattr("builtins.input", lambda _="": "q")

    kb.start()
    deadline = time.time() + 5.0
    while kb.running and time.time() < deadline:
        time.sleep(0.05)

    assert not kb.running
    assert kill_ran.is_set(), "kill switch callback was not invoked"


def test_keyboard_stop_idempotent():
    """Calling stop() multiple times is safe."""
    bus = EventBus()
    kb = KeyboardInput(bus, kill_switch_key="q")
    kb.stop()
    kb.stop()
    assert not kb.running
