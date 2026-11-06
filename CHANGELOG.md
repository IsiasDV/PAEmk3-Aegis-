# CHANGELOG

## [2026-11-06 14:50] CHG-0002 — Phase 1 core + keyboard
- Phase: 1
- Files: created perception/keyboard.py, brain/planner.py, brain/llm_interface.py, brain/prompt_templates.py; modified main.py; created tests/test_keyboard.py, tests/test_echo_brain.py, tests/test_kill_switch.py
- What & why: Implemented Phase 1 — keyboard input loop that publishes to the event bus, trivial echo brain that subscribes and echoes back, hard kill switch (q key / Ctrl+C). Wired everything together in main.py.
- Commands run: pytest tests/ -v
- Verification: 10 tests passed; manual round-trip keyboard→event bus→echo brain verified; import check passed
- Rollback: git commit 190925b
- Open issues: none

## [2026-11-06 14:30] CHG-0001 — Phase 0 project setup
- Phase: 0
- Files: created aegis/ (core/, perception/, recognition/, vision/, brain/, memory/, tools/, selfmod/, tests/, logs/), CHANGELOG.md, STATE.md, DECISIONS.md, config.yaml, requirements.txt, README.md, logs/changes.jsonl, core/__init__.py, core/event_bus.py, core/config.py, core/logging_setup.py, core/scheduler.py, main.py, tests/__init__.py, tests/test_logging.py
- What & why: Initialized the Aegis project per the prompt file. Created project directory structure, virtual environment, git repo, logging files, and core module stubs. This is the foundation for all subsequent phases.
- Commands run: python -m venv .venv; pip install pytest pyyaml; git init
- Verification: pytest tests/ -v -> 2 passed (test_log_change_writes_jsonl, test_changelog_entry_format); git log shows first commit; STATE.md lists real detected hardware
- Rollback: git commit <first-commit-hash>
- Open issues: none

