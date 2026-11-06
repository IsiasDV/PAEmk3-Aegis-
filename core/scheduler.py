"""Simple cooperative scheduler for Aegis.

Used by the main loop to run periodic tasks (frame capture, VAD, etc.)
at a controlled rate. Stub for Phase 0; fleshed out in Phase 1.
"""

from __future__ import annotations

import time
from typing import Callable


class Scheduler:
    """Runs callbacks at a minimum interval.

    Not a real-time scheduler; intended for coarse cadence control
    (e.g. capture a frame at most every N seconds).
    """

    def __init__(self) -> None:
        self._last_run: dict[str, float] = {}

    def should_run(self, name: str, min_interval: float) -> bool:
        """Return True if *name* is due to run (at least *min_interval*
        seconds since it last ran)."""
        now = time.monotonic()
        last = self._last_run.get(name, 0.0)
        if now - last >= min_interval:
            self._last_run[name] = now
            return True
        return False

    def run_if_due(self, name: str, min_interval: float, callback: Callable[[], None]) -> bool:
        """Call *callback* if *name* is due; return whether it ran."""
        if self.should_run(name, min_interval):
            callback()
            return True
        return False
