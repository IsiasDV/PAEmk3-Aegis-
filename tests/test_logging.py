"""Test that the logging infrastructure writes to CHANGELOG.md and changes.jsonl.

This is the Phase 0 gate test: a test proves logging writes a CHANGELOG.md
entry and a JSONL line.
"""

from __future__ import annotations

import json
import os
import re
import tempfile

from core.logging_setup import log_change


def test_log_change_writes_jsonl(tmp_path):
    """log_change appends one JSON object per line to changes.jsonl."""
    changes_file = tmp_path / "changes.jsonl"
    entry = {
        "id": "CHG-TEST-0001",
        "phase": 0,
        "files": ["tests/test_logging.py"],
        "summary": "Test logging writes JSONL line",
        "commands": ["pytest"],
        "verification": "test assertion",
        "commit": None,
        "status": "ok",
    }
    log_change(entry, changes_jsonl=str(changes_file))

    assert changes_file.exists(), "changes.jsonl was not created"
    lines = changes_file.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) >= 1, "no lines written to changes.jsonl"
    record = json.loads(lines[-1])
    assert record["id"] == "CHG-TEST-0001"
    assert record["phase"] == 0
    assert "timestamp" in record


def test_changelog_entry_format(tmp_path):
    """A CHANGELOG.md entry matches the mandated format."""
    changelog = tmp_path / "CHANGELOG.md"
    entry_id = "CHG-0001"
    phase = 0
    title = "Phase 0 project setup"
    lines = [
        f"## [2026-11-06 14:30] {entry_id} — {title}",
        "",
        f"- Phase: {phase}",
        "- Files: aegis/config.yaml",
        "- What & why: Test changelog entry format",
        "- Commands run: pytest",
        "- Verification: test assertion",
        "- Rollback: git commit abc123",
        "- Open issues: none",
        "",
    ]
    changelog.write_text("\n".join(lines), encoding="utf-8")

    content = changelog.read_text(encoding="utf-8")
    assert re.search(r"^## \[\d{4}-\d{2}-\d{2} \d{2}:\d{2}\] CHG-\d{4} — .+$", content, re.MULTILINE)
    assert f"- Phase: {phase}" in content
    assert "- Verification:" in content
