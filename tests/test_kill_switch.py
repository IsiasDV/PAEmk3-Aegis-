"""Tests for kill switch behavior (q key and Ctrl+C)."""

from __future__ import annotations

import threading
import time

from core.event_bus import EventBus
from perception.keyboard import KeyboardInput


def test_q_key_stops_keyboard(monkeypatch):
    """Typing 'q' stops the keyboard input loop."""
    bus = EventBus()
    kb = KeyboardInput(bus, kill_switch_key="q")
    monkeypatch.setattr("builtins.input", lambda _="": "q")

    kb.start()
    deadline = time.time() + 5.0
    while kb.running and time.time() < deadline:
        time.sleep(0.05)

    assert not kb.running


def test_kill_switch_key_is_case_insensitive(monkeypatch):
    """The kill switch key matches regardless of case."""
    bus = EventBus()
    kb = KeyboardInput(bus, kill_switch_key="Q")
    monkeypatch.setattr("builtins.input", lambda _="": "q")

    kb.start()
    deadline = time.time() + 5.0
    while kb.running and time.time() < deadline:
        time.sleep(0.05)

    assert not kb.running


def test_kill_switch_runs_multiple_callbacks(monkeypatch):
    """All registered kill callbacks are invoked."""
    bus = EventBus()
    kb = KeyboardInput(bus, kill_switch_key="q")

    calls = []
    kb.register_kill_callback(lambda: calls.append("first"))
    kb.register_kill_callback(lambda: calls.append("second"))

    monkeypatch.setattr("builtins.input", lambda _="": "q")

    kb.start()
    deadline = time.time() + 5.0
    while kb.running and time.time() < deadline:
        time.sleep(0.05)

    assert calls == ["first", "second"]
