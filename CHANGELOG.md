# CHANGELOG

## [2026-11-06 14:30] CHG-0001 — Phase 0 project setup
- Phase: 0
- Files: created aegis/ (core/, perception/, recognition/, vision/, brain/, memory/, tools/, selfmod/, tests/, logs/), CHANGELOG.md, STATE.md, DECISIONS.md, config.yaml, requirements.txt, README.md, logs/changes.jsonl, core/__init__.py, core/event_bus.py, core/config.py, core/logging_setup.py, core/scheduler.py, main.py, tests/__init__.py, tests/test_logging.py
- What & why: Initialized the Aegis project per the prompt file. Created project directory structure, virtual environment, git repo, logging files, and core module stubs. This is the foundation for all subsequent phases.
- Commands run: python -m venv .venv; pip install pytest pyyaml; git init
- Verification: pytest passes (see CHG-0002); git log shows first commit; logging test writes CHANGELOG.md entry and JSONL line
- Rollback: git commit <first-commit-hash>
- Open issues: none
