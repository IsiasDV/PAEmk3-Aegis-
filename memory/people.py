"""People memory — enrolled people and their info.

Stores information about enrolled people (name, consent, enrollment time,
metadata) in SQLite. Independent of the face recognition identity store;
this is the semantic memory about people, while identity_store holds the
face embeddings.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from memory.db import MemoryDB


class PeopleMemory:
    """Manages enrolled people records.

    Parameters
    ----------
    db:
        A MemoryDB instance (shared across memory modules).
    """

    def __init__(self, db: MemoryDB) -> None:
        self.db = db

    def _utc_now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def add_or_update(
        self,
        person_id: str,
        name: str | None = None,
        consent: bool = False,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Add a new person or update an existing one."""
        import json

        now = self._utc_now()
        cur = self.db.execute(
            "SELECT id FROM people WHERE person_id = ?", (person_id,)
        )
        row = cur.fetchone()
        if row is None:
            self.db.execute(
                """
                INSERT INTO people (person_id, name, enrolled_at, consent, metadata)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    person_id,
                    name,
                    now,
                    1 if consent else 0,
                    json.dumps(metadata) if metadata else None,
                ),
            )
        else:
            self.db.execute(
                """
                UPDATE people
                SET name = COALESCE(?, name),
                    enrolled_at = CASE WHEN ? IS NOT NULL THEN enrolled_at ELSE enrolled_at END,
                    consent = ?,
                    metadata = COALESCE(?, metadata)
                WHERE person_id = ?
                """,
                (name, now, 1 if consent else 0, json.dumps(metadata) if metadata else None, person_id),
            )
        self.db.commit()

    def get(self, person_id: str) -> dict[str, Any] | None:
        """Return a person's record, or None if not found."""
        import json

        row = self.db.execute(
            "SELECT person_id, name, enrolled_at, consent, metadata FROM people WHERE person_id = ?",
            (person_id,),
        ).fetchone()
        if row is None:
            return None
        return {
            "person_id": row["person_id"],
            "name": row["name"],
            "enrolled_at": row["enrolled_at"],
            "consent": bool(row["consent"]),
            "metadata": json.loads(row["metadata"]) if row["metadata"] else None,
        }

    def list_people(self) -> list[dict[str, Any]]:
        """Return all people records, sorted by enrollment time."""
        import json

        rows = self.db.execute(
            "SELECT person_id, name, enrolled_at, consent, metadata FROM people ORDER BY enrolled_at"
        ).fetchall()
        return [
            {
                "person_id": row["person_id"],
                "name": row["name"],
                "enrolled_at": row["enrolled_at"],
                "consent": bool(row["consent"]),
                "metadata": json.loads(row["metadata"]) if row["metadata"] else None,
            }
            for row in rows
        ]

    def delete(self, person_id: str) -> bool:
        """Delete a person record. Returns True if deleted."""
        cur = self.db.execute("DELETE FROM people WHERE person_id = ?", (person_id,))
        self.db.commit()
        return cur.rowcount > 0

    def count(self) -> int:
        """Return the number of enrolled people."""
        row = self.db.execute("SELECT COUNT(*) AS c FROM people").fetchone()
        return row["c"]
