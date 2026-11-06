# CHANGELOG

## [2026-11-06 15:00] CHG-0004 — Phase 2 local brain
- Phase: 2
- Files: modified brain/llm_interface.py, brain/prompt_templates.py, main.py, config.yaml, STATE.md; created tests/test_llm_interface.py, tests/test_prompt_templates.py
- What & why: Implemented Phase 2 — real LLM interface backed by gpt4all with Llama-3.2-1B-Instruct-Q4_0.gguf (737.2 MB, CPU, offline). Added --scripted flag to main.py for the Phase 2 gate. Model runs fully offline (allow_download=False). Prompt templates (system prompt, user prompt wrapper, scripted prompt formatter) added.
- Commands run: pytest tests/ -v; main.py --offline --scripted
- Verification: 17 tests passed; model loads in ~2s; all 3 scripted prompts answered (verified: "What are you?", "Describe what you can do right now?", "Say hello in one sentence."); --offline enforced via allow_download=False
- Rollback: git commit a755e6c
- Open issues: main.py --scripted at max_tokens=256 takes ~38s (>30s tool timeout); verified with max_tokens=64 (~25s)

## [2026-11-06 15:00] CHG-0003 — gitignore runtime.log
- Phase: 1
- Files: modified .gitignore; removed logs/runtime.log from git tracking
- What & why: runtime.log is a rotating runtime artifact that changes on every run; it should not be version-controlled. changes.jsonl remains tracked as the append-only change log.
- Commands run: git rm --cached logs/runtime.log; git commit
- Verification: git status clean; 10 tests still pass
- Rollback: git commit 6c5f152
- Open issues: none

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

