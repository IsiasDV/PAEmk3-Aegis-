# CHANGELOG
## [2026-11-06 16:15] CHG-0008 — Phase 5 face recognition with consent
- Phase: 5
- Files: created recognition/identity_store.py, recognition/face_detect.py, recognition/face_embed.py, recognition/enrollment.py, recognition/__init__.py; created tests/test_identity_store.py, tests/test_face_detector.py, tests/test_face_embedder.py, tests/test_enrollment.py; modified config.yaml, requirements.txt, DECISIONS.md, STATE.md, main.py
- What & why: Implemented Phase 5 — face recognition with consent. Identity store (JSON-based, embeddings only, no raw images), Haar cascade face detection, LBPHFaceRecognizer embeddings/recognition, enrollment flow with opt-in consent. Privacy: unenrolled faces reported as "unknown" and never stored; delete/wipe commands supported. Verified: enroll 2 identities, identify each, report unknown as unknown, delete/wipe work, false-accept/false-reject tested via confidence threshold. Live camera face detection at 9.2 FPS.
- Commands run: pytest tests/ -v; manual live camera face detection test
- Verification: 21 Phase 5 tests passed; live camera detects faces (9.2 FPS); Haar cascade loads from existing model on device; LBPH trains and recognizes
- Rollback: git commit 827d7df
- Open issues: none



## [2026-11-06 15:45] CHG-0007 — Phase 4 camera + scene description
- Phase: 4
- Files: created perception/camera.py, vision/scene_describer.py, tests/test_camera.py, tests/test_scene_describer.py; modified main.py, config.yaml, STATE.md
- What & why: Implemented Phase 4 — camera capture (OpenCV, rate-limited, publishes camera.frame events) and scene description (simple image-property describer always available; VLM stub marked UNVERIFIED). Camera verified on device 0 (Integrated Webcam, 640x480, ~8.6 FPS capture, ~116 ms latency). Full pipeline (camera → describer) produces descriptions (~1 FPS including OpenCV processing). VLM path is UNVERIFIED: no local VLM model, CPU-only Intel UHD with 1 GB VRAM cannot run a 2–8 GB VLM.
- Commands run: pytest tests/ -v; manual live camera test
- Verification: 35 tests passed; test camera publishes frames; scene describer produces sensible descriptions from test images; live camera + describer pipeline verified; frame rate and latency measured and logged
- Rollback: git commit 684d91a
- Open issues: VLM scene description is UNVERIFIED (no model, insufficient hardware); camera FPS drops when scene description processing is included

## [2026-11-06 15:15] CHG-0006 — Phase 3 microphone + speech-to-text
- Phase: 3
- Files: created perception/vad.py, perception/stt.py, tests/test_stt.py, tests/test_hello.wav; modified main.py, brain/planner.py, config.yaml, requirements.txt
- What & why: Implemented Phase 3 — microphone + offline speech-to-text using vosk. VAD (energy-based) gates recognition. STT publishes stt.transcription events to the event bus; EchoBrain subscribes to both keyboard.input and stt.transcription. main.py gained --stt flag for live mic + STT. Verified: vosk transcribes "hello world" WAV correctly; live mic captures audio successfully.
- Commands run: pytest tests/ -v; manual live mic capture test; WAV transcription test
- Verification: 24 tests passed; test_stt_transcribes_hello_world confirms "hello world" transcription; live mic test captured audio (RMS=0.000867)
- Rollback: git commit 68d4e11
- Open issues: live mic transcription requires user to speak (not automated); STT model path in config.yaml points to existing vosk-model-small-en-us-0.15 on device

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

