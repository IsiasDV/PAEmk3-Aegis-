"""Episodic memory — who/what/when events.

Stores timestamped events in SQLite so the agent can recall what happened
during past sessions, even after a restart.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from memory.db import MemoryDB


class EpisodicMemory:
    """Records and recalls timestamped events.

    Parameters
    ----------
    db:
        A MemoryDB instance (shared across memory modules).
    """

    def __init__(self, db: MemoryDB) -> None:
        self.db = db

    def _utc_now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def record(
        self,
        event_type: str,
        description: str,
        actor: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> int:
        """Record an episode and return its row id.

        Parameters
        ----------
        event_type:
            Category of event (e.g. "face_recognized", "person_enrolled",
            "camera_started", "user_said").
        description:
            Human-readable description of what happened.
        actor:
            Who was involved (person_id, "user", "system", etc.).
        metadata:
            Optional extra structured data, stored as JSON.
        """
        cur = self.db.execute(
            """
            INSERT INTO episodes (timestamp, event_type, actor, description, metadata)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                self._utc_now(),
                event_type,
                actor,
                description,
                json.dumps(metadata) if metadata else None,
            ),
        )
        self.db.commit()
        return cur.lastrowid

    def recall(
        self,
        limit: int = 50,
        event_type: str | None = None,
        actor: str | None = None,
    ) -> list[dict[str, Any]]:
        """Recall recent episodes, newest first.

        Parameters
        ----------
        limit:
            Maximum number of episodes to return.
        event_type:
            If set, only return episodes of this type.
        actor:
            If set, only return episodes involving this actor.
        """
        sql = "SELECT id, timestamp, event_type, actor, description, metadata FROM episodes"
        params: list[Any] = []
        conditions: list[str] = []
        if event_type is not None:
            conditions.append("event_type = ?")
            params.append(event_type)
        if actor is not None:
            conditions.append("actor = ?")
            params.append(actor)
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
        sql += " ORDER BY id DESC LIMIT ?"
        params.append(limit)

        rows = self.db.execute(sql, tuple(params)).fetchall()
        return [
            {
                "id": row["id"],
                "timestamp": row["timestamp"],
                "event_type": row["event_type"],
                "actor": row["actor"],
                "description": row["description"],
                "metadata": json.loads(row["metadata"]) if row["metadata"] else None,
            }
            for row in rows
        ]

    def clear(self) -> int:
        """Remove all episodes. Returns the number removed."""
        cur = self.db.execute("DELETE FROM episodes")
        self.db.commit()
        return cur.rowcount
