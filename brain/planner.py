"""Trivial echo brain for Phase 1.

Subscribes to ``keyboard.input`` events and echoes the text back to the
console. This is a placeholder for the real LLM brain (Phase 2).
"""

from __future__ import annotations

from typing import Any, Optional

from core.event_bus import EventBus


class EchoBrain:
    """A trivial brain that echoes back whatever it hears."""

    def __init__(self, event_bus: EventBus) -> None:
        self.event_bus = event_bus
        self._last_text: Optional[str] = None
        self._started = False

    def start(self) -> None:
        if self._started:
            return
        self.event_bus.subscribe("keyboard.input", self._on_input)
        self._started = True

    def stop(self) -> None:
        self._started = False

    def _on_input(self, event: dict[str, Any]) -> None:
        text = event.get("text", "")
        self._last_text = text
        print(f"[brain] echo: {text}")

    @property
    def last_text(self) -> Optional[str]:
        return self._last_text
