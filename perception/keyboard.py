"""Keyboard input perception module.

Reads lines from stdin and publishes them as ``keyboard.input`` events on the
event bus. Supports a hard kill switch via the configured key (default ``q``)
and Ctrl+C. Runs the blocking stdin read in a background thread so the kill
switch remains responsive.
"""

from __future__ import annotations

import signal
import sys
import threading
from typing import Callable, Optional

from core.event_bus import EventBus


class KeyboardInput:
    """Reads keyboard input from stdin and publishes events."""

    def __init__(
        self,
        event_bus: EventBus,
        kill_switch_key: str = "q",
    ) -> None:
        self.event_bus = event_bus
        self.kill_switch_key = kill_switch_key.strip().lower()
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._kill_callbacks: list[Callable[[], None]] = []

    def start(self) -> None:
        """Start the keyboard input loop in a background thread."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        signal.signal(signal.SIGINT, self._on_sigint)
        print(f"[keyboard] active. Type '{self.kill_switch_key}' to kill switch, Ctrl+C to exit.")

    def stop(self) -> None:
        """Stop the keyboard input loop."""
        self._running = False

    def register_kill_callback(self, cb: Callable[[], None]) -> None:
        """Register a callback to run when the kill switch is triggered."""
        self._kill_callbacks.append(cb)

    def _on_sigint(self, signum, frame) -> None:
        """Handle Ctrl+C: trigger kill switch and exit."""
        print("\n[keyboard] Ctrl+C received — kill switch engaged")
        self.stop()
        for cb in list(self._kill_callbacks):
            try:
                cb()
            except Exception:  # noqa: BLE001 - kill callbacks must not crash shutdown
                pass
        sys.exit(0)

    def _loop(self) -> None:
        """Read lines from stdin and publish ``keyboard.input`` events."""
        while self._running:
            try:
                line = input()
            except EOFError:
                self.stop()
                break
            if not self._running:
                break
            text = line.strip()
            if text.lower() == self.kill_switch_key:
                print(f"[keyboard] kill switch triggered ('{self.kill_switch_key}')")
                self.stop()
                for cb in list(self._kill_callbacks):
                    try:
                        cb()
                    except Exception:  # noqa: BLE001
                        pass
                break
            self.event_bus.publish("keyboard.input", {"text": text, "source": "stdin"})

    @property
    def running(self) -> bool:
        return self._running
