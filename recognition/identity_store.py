"""Identity store for face recognition.

Stores face embeddings only (no raw face images), per privacy rules.
Each enrolled person has a unique ID and a list of embedding vectors.
All data stays local — nothing is transmitted over the network.
"""

from __future__ import annotations

import json
import os
from typing import Optional

import numpy as np


class IdentityStore:
    """Stores enrolled identities as embeddings only.

    Parameters
    ----------
    store_path:
        Path to the JSON file where identities are persisted.
    """

    def __init__(self, store_path: str) -> None:
        self.store_path = os.path.abspath(store_path)
        self._identities: dict[str, dict] = {}
        self._loaded = False

    def load(self) -> None:
        """Load identities from disk. Creates an empty store if the file
        does not exist."""
        if self._loaded:
            return
        if os.path.exists(self.store_path):
            with open(self.store_path, "r", encoding="utf-8") as fh:
                self._identities = json.load(fh)
        else:
            self._identities = {}
        self._loaded = True

    def save(self) -> None:
        """Persist identities to disk."""
        os.makedirs(os.path.dirname(self.store_path), exist_ok=True)
        with open(self.store_path, "w", encoding="utf-8") as fh:
            json.dump(self._identities, fh, indent=2)

    def list_people(self) -> list[str]:
        """Return the list of enrolled person IDs."""
        self.load()
        return sorted(self._identities.keys())

    def get_embeddings(self, person_id: str) -> list[list[float]]:
        """Return the stored embeddings for *person_id*, or an empty list
        if the person is not enrolled."""
        self.load()
        return self._identities.get(person_id, {}).get("embeddings", [])

    def add_embedding(self, person_id: str, embedding: list[float]) -> None:
        """Add an embedding for *person_id*. Creates the person if needed."""
        self.load()
        if person_id not in self._identities:
            self._identities[person_id] = {"embeddings": [], "consent": False}
        self._identities[person_id]["embeddings"].append(embedding)

    def set_consent(self, person_id: str, consent: bool) -> None:
        """Record whether *person_id* has given consent for recognition."""
        self.load()
        if person_id not in self._identities:
            self._identities[person_id] = {"embeddings": [], "consent": False}
        self._identities[person_id]["consent"] = consent

    def has_consent(self, person_id: str) -> bool:
        """Return True if *person_id* has given consent."""
        self.load()
        return self._identities.get(person_id, {}).get("consent", False)

    def is_enrolled(self, person_id: str) -> bool:
        """Return True if *person_id* exists in the store (even without
        embeddings yet)."""
        self.load()
        return person_id in self._identities

    def delete_person(self, person_id: str) -> bool:
        """Delete *person_id* and all their data. Returns True if deleted,
        False if not found."""
        self.load()
        if person_id in self._identities:
            del self._identities[person_id]
            self.save()
            return True
        return False

    def wipe_all(self) -> int:
        """Remove all enrolled people and their data. Returns the number
        of people removed."""
        self.load()
        count = len(self._identities)
        self._identities = {}
        self.save()
        return count

    def person_count(self) -> int:
        """Return the number of enrolled people."""
        self.load()
        return len(self._identities)

    @property
    def path(self) -> str:
        return self.store_path
