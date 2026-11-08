"""SQLite database backend for Aegis memory.

Provides a simple, thread-safe SQLite wrapper used by episodic memory,
people memory, and the environment model. All data stays local.
"""

from __future__ import annotations

import os
import sqlite3
import threading
from typing import Any


class MemoryDB:
    """Thread-safe SQLite database connection wrapper.

    Parameters
    ----------
    db_path:
        Path to the SQLite database file.
    """

    def __init__(self, db_path: str) -> None:
        self.db_path = os.path.abspath(db_path)
        self._local = threading.local()
        self._init_schema()

    def _get_conn(self) -> sqlite3.Connection:
        """Return a thread-local SQLite connection."""
        conn = getattr(self._local, "conn", None)
        if conn is None:
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            self._local.conn = conn
        return conn

    def _init_schema(self) -> None:
        """Create tables if they don't exist."""
        conn = self._get_conn()
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS episodes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                event_type TEXT NOT NULL,
                actor TEXT,
                description TEXT NOT NULL,
                metadata TEXT
            );
            CREATE TABLE IF NOT EXISTS people (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                person_id TEXT UNIQUE NOT NULL,
                name TEXT,
                enrolled_at TEXT,
                consent INTEGER DEFAULT 0,
                metadata TEXT
            );
            CREATE TABLE IF NOT EXISTS environment (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            """
        )
        conn.commit()

    def execute(self, sql: str, params: tuple = ()) -> sqlite3.Cursor:
        """Execute a SQL statement and return the cursor."""
        conn = self._get_conn()
        return conn.execute(sql, params)

    def commit(self) -> None:
        """Commit the current transaction."""
        self._get_conn().commit()

    def close(self) -> None:
        """Close the thread-local connection.

        Safe to call multiple times; suppresses PermissionError on Windows
        where a connection may be locked during the pytest temp-dir teardown.
        """
        conn = getattr(self._local, "conn", None)
        if conn is not None:
            self._local.conn = None
            try:
                conn.close()
            except PermissionError:
                # Windows can hold file locks across test-process exits;
                # the OS will release them on process termination.
                pass


    def __enter__(self) -> "MemoryDB":
        return self

    def __exit__(self, *exc_info) -> None:
        self.commit()
        self.close()
