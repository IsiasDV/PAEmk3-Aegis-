"""Memory brain for Phase 6.

Answers recall queries from episodic memory. Subscribes to perception
events (keyboard input, STT transcription, scene descriptions) and
records them into on-disk SQLite episodic memory so the agent can recall
what happened during past sessions, even after a restart.

This is the integration point between perception (camera, mic, keyboard)
and memory (episodic, people, environment model).
"""

from __future__ import annotations

from typing import Any, Optional

from core.event_bus import EventBus
from memory.db import MemoryDB
from memory.episodic import EpisodicMemory
from memory.people import PeopleMemory


class MemoryBrain:
    """A brain backed by persistent episodic and people memory.

    Parameters
    ----------
    event_bus:
        Event bus to subscribe to for recording events.
    db:
        Shared MemoryDB instance for persistent storage.
    """

    def __init__(
        self,
        event_bus: EventBus,
        db: MemoryDB,
    ) -> None:
        self.event_bus = event_bus
        self.db = db
        self.episodic = EpisodicMemory(db)
        self.people = PeopleMemory(db)
        self._started = False
        self._last_query: Optional[str] = None
        self._last_answer: Optional[str] = None

    def start(self) -> None:
        """Subscribe to perception events and record them into episodic memory."""
        if self._started:
            return
        self.event_bus.subscribe("keyboard.input", self._on_keyboard_input)
        self.event_bus.subscribe("stt.transcription", self._on_stt_transcription)
        self.event_bus.subscribe("vision.scene_description", self._on_scene_description)
        self._started = True

    def stop(self) -> None:
        """Unsubscribe and flush memory to disk."""
        self._started = False
        self.db.commit()

    def _on_keyboard_input(self, event: dict[str, Any]) -> None:
        text = event.get("text", "")
        source = event.get("source", "user")
        self.episodic.record(
            event_type="keyboard.input",
            description=text,
            actor=source,
            metadata={"source": source},
        )

    def _on_stt_transcription(self, event: dict[str, Any]) -> None:
        text = event.get("text", "")
        source = event.get("source", "microphone")
        self.episodic.record(
            event_type="stt.transcription",
            description=text,
            actor=source,
            metadata={"source": source},
        )

    def _on_scene_description(self, event: dict[str, Any]) -> None:
        description = event.get("description", "")
        frame_size = event.get("frame_size")
        metadata: dict[str, Any] = {}
        if frame_size is not None:
            metadata["frame_size"] = frame_size
        self.episodic.record(
            event_type="vision.scene_description",
            description=description,
            actor="system",
            metadata=metadata if metadata else None,
        )

    def recall(self, query: str, limit: int = 10) -> str:
        """Answer a recall query from episodic memory.

        Parameters
        ----------
        query:
            A natural-language query about past events.
        limit:
            Maximum number of episodes to consider.

        Returns
        -------
        A text answer summarizing relevant episodes.
        """
        self._last_query = query
        episodes = self.episodic.recall(limit=limit)

        if not episodes:
            self._last_answer = "I don't remember anything yet."
            return self._last_answer

        q = query.lower()
        matches: list[dict[str, Any]] = []
        for ep in episodes:
            text = (ep.get("description", "") + " " + ep.get("event_type", "")).lower()
            if q in text or any(word in text for word in q.split() if len(word) > 3):
                matches.append(ep)

        if not matches:
            # Fall back to most recent episodes
            matches = episodes[:limit]

        lines: list[str] = [f"Found {len(matches)} relevant memory(ies):"]
        for ep in matches:
            ts = ep.get("timestamp", "unknown time")
            actor = ep.get("actor", "unknown")
            desc = ep.get("description", "")
            etype = ep.get("event_type", "unknown")
            lines.append(f"  [{ts}] {actor} ({etype}): {desc}")

        answer = "\n".join(lines)
        self._last_answer = answer
        return answer

    def recall_people(self) -> str:
        """Recall all enrolled people from people memory."""
        people = self.people.list_people()
        if not people:
            return "No enrolled people in memory."
        lines = ["Enrolled people in memory:"]
        for p in people:
            consent = "consent given" if p.get("consent") else "no consent"
            name = p.get("name") or "unnamed"
            lines.append(f"  {p['person_id']} ({name}, {consent})")
        return "\n".join(lines)

    def enroll_person(
        self,
        person_id: str,
        name: str | None = None,
        consent: bool = False,
    ) -> None:
        """Record a person in people memory."""
        self.people.add_or_update(person_id, name=name, consent=consent)

    @property
    def last_query(self) -> Optional[str]:
        return self._last_query

    @property
    def last_answer(self) -> Optional[str]:
        return self._last_answer
