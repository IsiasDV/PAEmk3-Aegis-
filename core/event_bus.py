"""Simple in-process publish/subscribe event bus.

Perception modules publish events here; the brain subscribes and decides.
Actions go through tools/registry.py. Every module is independently testable
with recorded/mock input so tests pass without hardware.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Callable

EventHandler = Callable[[dict[str, Any]], None]


class EventBus:
    """A lightweight pub/sub event bus.

    Subscribers register callbacks for named event types. Publishers emit
    events as dicts. All delivery is synchronous and in-process.
    """

    def __init__(self) -> None:
        self._handlers: dict[str, list[EventHandler]] = defaultdict(list)

    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        """Register *handler* to receive events of *event_type*."""
        self._handlers[event_type].append(handler)

    def publish(self, event_type: str, event: dict[str, Any]) -> None:
        """Publish *event* under *event_type* to all subscribers."""
        for handler in self._handlers.get(event_type, []):
            handler(event)

    def subscribers(self, event_type: str) -> list[EventHandler]:
        """Return the handlers registered for *event_type* (mostly for tests)."""
        return list(self._handlers.get(event_type, []))
