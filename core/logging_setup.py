"""Runtime logging setup for Aegis.

Writes:
- logs/runtime.log  — structured, rotating runtime log
- logs/changes.jsonl — one JSON object per line per change (Section 2)

All loggers are configured here so every module uses the same format.
"""

from __future__ import annotations

import json
import logging
import os
import sys
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from typing import Any

LOG_DIR = os.path.join(os.path.dirname(__file__), "..", "logs")
RUNTIME_LOG = os.path.join(LOG_DIR, "runtime.log")
CHANGES_JSONL = os.path.join(LOG_DIR, "changes.jsonl")

_MAX_BYTES = 5 * 1024 * 1024  # 5 MB
_BACKUP_COUNT = 3

_logger: logging.Logger | None = None


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def setup_runtime_logging(
    log_dir: str = LOG_DIR,
    runtime_log: str = RUNTIME_LOG,
    level: int = logging.INFO,
) -> logging.Logger:
    """Configure the rotating runtime logger and return it.

    Safe to call multiple times; returns the same configured logger.
    """
    global _logger
    if _logger is not None:
        return _logger

    os.makedirs(log_dir, exist_ok=True)

    logger = logging.getLogger("aegis")
    logger.setLevel(level)
    logger.propagate = False

    # Clear any pre-existing handlers (idempotent setup)
    logger.handlers.clear()

    fmt = logging.Formatter(
        "%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )

    fh = RotatingFileHandler(
        runtime_log, maxBytes=_MAX_BYTES, backupCount=_BACKUP_COUNT, encoding="utf-8"
    )
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(fmt)
    logger.addHandler(sh)

    _logger = logger
    logger.info("Aegis runtime logging initialized")
    return logger


def get_logger() -> logging.Logger:
    """Return the runtime logger, initializing it if necessary."""
    if _logger is None:
        return setup_runtime_logging()
    return _logger


def log_change(
    entry: dict[str, Any],
    changes_jsonl: str = CHANGES_JSONL,
) -> None:
    """Append one JSON object per line to `changes.jsonl`.

    This is the append-only change log referenced by Section 2. Each entry
    should include keys: id, timestamp, phase, files, summary, commands,
    verification, commit, status.
    """
    os.makedirs(os.path.dirname(changes_jsonl), exist_ok=True)
    record = dict(entry)
    record.setdefault("timestamp", _utc_now())
    line = json.dumps(record, sort_keys=True)
    with open(changes_jsonl, "a", encoding="utf-8") as fh:
        fh.write(line + "\n")
    get_logger().info("Change logged: %s", record.get("id", "unknown"))
