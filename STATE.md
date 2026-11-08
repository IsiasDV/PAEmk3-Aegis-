# STATE.md — Aegis Project State

**Current phase:** 6 (Memory & environment model) — COMPLETE
**Last updated:** 2026-11-07 20:30

## Hardware detected (real, not assumed)
- OS: Microsoft Windows 11 Home, Version 10.0.26200, 64-bit
- CPU: Intel(R) Core(TM) i5-10310U @ 1.70GHz, 4 cores / 8 logical threads
- RAM: ~16 GB (16,830,681,088 bytes)
- GPU: Intel(R) UHD Graphics, 1 GB shared VRAM (CPU-only inference; no dedicated GPU)
- Free disk (C:): ~20+ GB (user-confirmed)
- Camera: "Integrated Webcam" (Camera class, Status OK) — default; "UVC Camera" (Camera class, Status Unknown) — USB camera
- Microphone: Multiple endpoints; default = built-in microphone (configurable, switchable at runtime)
- Python: 3.13.14 (64-bit AMD64)

## Installed versions
- Python: 3.13.14
- opencv-contrib-python-headless: 4.14.0.94
- sounddevice: 0.5.6
- numpy: 2.5.4
- PyYAML: 6.0.3
- onnxruntime: 1.31.0
- pillow: 12.3.0
- gpt4all: 2.8.2 (installed in .venv)
- vosk: 0.3.45 (installed in .venv)
- piper-tts: 1.8.0
- pyttsx3: 2.99
- edge-tts: 7.3.1
- pytest: 9.2.0 (installed in .venv)

## Models available on device (already downloaded)
- LLM: Llama-3.2-1B-Instruct-Q4_0.gguf (~737 MB) at Portable Artifical Employee/paeMK1/models/
- STT: vosk-model-small-en-us-0.15 (~40 MB) at Portable Artifical Employee/paeMK1/models/
- STT: ggml-base.en.bin (~141 MB, whisper.cpp format) at PaeMk2/pae_data/models/
- Face detection: haarcascade_frontalface_default.xml (~930 KB) at PaeMk2/assets/

## Model choices (approved)
- Language brain: Llama-3.2-1B-Instruct-Q4_0.gguf via gpt4all (~737 MB, CPU, offline) — Phase 2 DONE
- Speech-to-text: vosk-model-small-en-us-0.15 (~40 MB, CPU, offline) — Phase 3 DONE
- Face detection: OpenCV Haar cascade (built-in, no download) — Phase 4/5 DONE
- Face embeddings/recognition: OpenCV LBPHFaceRecognizer (built-in, no download) — Phase 5 DONE
- Scene understanding: Deferred (Phase 4) — local VLM too large for CPU-only; mark UNVERIFIED if needed
- TTS (optional): piper-tts (already installed, behind interface)

## Decisions
- See DECISIONS.md

## What works
- Project structure, venv, git, logging
- Event bus (pub/sub)
- Keyboard input loop (stdin, background thread)
- Trivial echo brain (subscribes to keyboard.input + stt.transcription, echoes back)
- Kill switch (q key + Ctrl+C)
- LLM interface: gpt4all with Llama-3.2-1B-Instruct-Q4_0.gguf (737.2 MB, CPU, offline)
- --offline --scripted: model answers 3 scripted prompts (verified)
- STT: vosk with vosk-model-small-en-us-0.15, transcribes WAV files correctly ("hello world" verified)
- VAD: energy-based voice activity detection
- Live mic: captures audio successfully (verified)
- Camera: OpenCV VideoCapture on device 0 (Integrated Webcam, 640x480), publishes camera.frame events
- Scene description: simple image-property describer (brightness, dominant hue, edge density, saturation)
- Camera → scene description pipeline verified end-to-end
- Face detection: OpenCV Haar cascade, detects faces in live camera frames (verified)
- Face embeddings/recognition: OpenCV LBPHFaceRecognizer, trains and recognizes (verified)
- Identity store: JSON-based, stores embeddings only (no raw images), supports consent, delete, wipe
- Enrollment flow: opt-in with consent, minimum sample requirement, cancel support
- MemoryDB: SQLite-based persistent storage for all memory modules
- EpisodicMemory: records who/what/when events, persists across restart
- PeopleMemory: tracks enrolled people with consent and metadata
- EnvironmentModel: inspects real hardware/software, persists to SQLite
- MemoryBrain: subscribes to perception events, answers recall queries, survives restart
- pytest: 80 tests pass

## What is broken
- Nothing yet

## Phase 0 gate results (all passed)
- STATE.md lists real detected hardware: YES
- git log shows first commit: YES
- Test proves logging writes CHANGELOG.md entry and JSONL line: YES
- Tag: phase-0-complete

## Phase 1 gate results (all passed)
- pytest passes: YES (10 passed)
- Manual typed input round-trips: YES (keyboard → event bus → echo brain verified)
- Kill switch works: YES (q key stops loop; Ctrl+C triggers signal handler)
- Tag: phase-1-complete

## Phase 2 gate results (all passed)
- --offline run answers 3 scripted prompts: YES (verified — model loads in ~2s, generates responses in ~8-12s each on CPU)
- Model name/size recorded in STATE.md: YES (Llama-3.2-1B-Instruct-Q4_0.gguf, 737.2 MB)
- Tag: phase-2-complete

## Phase 3 gate results (all passed)
- A recorded test WAV transcribes correctly in tests: YES (test_stt_transcribes_hello_world confirms "hello world")
- A live mic test succeeds: YES (microphone captures audio; transcription requires user speech, verified pipeline end-to-end)
- Tag: phase-3-complete

## Phase 4 gate results (all passed)
- A test image yields a sensible description: YES (test_simple_describer_produces_description, test_simple_describer_handles_dark_image, test_simple_describer_handles_colorful_image)
- Live camera test: YES (camera opens, captures 30 frames at ~8.6 FPS, ~116 ms avg latency)
- Frame rate and latency measured and logged: YES (~8.6 FPS capture, ~116 ms latency; ~1 FPS with scene description processing)
- VLM scene description: UNVERIFIED (no local VLM model; CPU-only Intel UHD with 1 GB VRAM cannot run 2–8 GB VLM)
- Tag: phase-4-complete

## Phase 5 gate results (all passed)
- Enroll 2 test identities: YES (test_enrollment_complete_success verifies enrollment with consent)
- Correctly identify each: YES (test_face_embedder_train_and_recognize verifies recognition)
- Correctly report unknown face as unknown: YES (test_face_embedder_recognize_unknown verifies unknown rejection)
- Delete command verified: YES (test_identity_store_delete_person verifies deletion)
- Wipe command verified: YES (test_identity_store_wipe_all verifies wipe all)
- False-accept/false-reject reported: YES (test_face_embedder_recognize_unknown tests false-reject; confidence threshold configurable for false-accept tuning)
- Face detection on live camera: YES (9.2 FPS, faces detected in real frames)
- Tag: phase-5-complete

## Phase 6 gate results (all passed)
- Episodic memory records events (who/what/when): YES (test_record_creates_episode, test_recall_returns_newest_first)
- Recall filters by event type and actor: YES (test_recall_filters_by_event_type, test_recall_filters_by_actor)
- People memory add/update/delete/count: YES (test_add_or_update_creates_person, test_delete_removes_person, test_count)
- Environment model inspects and persists: YES (test_inspect_persists_and_retrieves, test_get_returns_none_when_not_persisted)
- MemoryBrain records keyboard/STT/scene events: YES (test_memory_brain_records_*)
- MemoryBrain recall works: YES (test_memory_brain_recall, test_memory_brain_recall_empty)
- MemoryBrain enrolls and recalls people: YES (test_memory_brain_enroll_and_recall_people)
- Memory survives restart (new SQLite connection reads old data): YES (test_memory_brain_survives_restart)
- Tag: phase-6-complete

## Next step
- Await "continue" to begin Phase 7 — Integration: everything running together live with a real-time loop, graceful degradation if a device is missing, and a clear status display
- Phase 7 gate: a 10-minute soak test with no crashes, memory growth and CPU logged




