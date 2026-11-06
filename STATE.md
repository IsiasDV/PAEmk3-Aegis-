# STATE.md — Aegis Project State

**Current phase:** 2 (Local brain) — COMPLETE
**Last updated:** 2026-11-06 15:05

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
- opencv-python-headless: 4.14.0.94
- sounddevice: 0.5.6
- numpy: 2.5.4
- PyYAML: 6.0.3
- onnxruntime: 1.31.0
- pillow: 12.3.0
- gpt4all: 2.8.2 (installed in .venv)
- vosk: 0.3.45
- piper-tts: 1.8.0
- pyttsx3: 2.99
- edge-tts: 7.3.1
- pytest: 9.2.0 (installed in .venv)

## Models available on device (already downloaded)
- LLM: Llama-3.2-1B-Instruct-Q4_0.gguf (~737 MB) at Portable Artifical Employee/paeMK1/models/
- STT: ggml-base.en.bin (~141 MB, whisper.cpp format) at PaeMk2/pae_data/models/
- Face detection: haarcascade_frontalface_default.xml (~930 KB) at PaeMk2/assets/

## Model choices (approved)
- Language brain: Llama-3.2-1B-Instruct-Q4_0.gguf via gpt4all (~737 MB, CPU, offline) — Phase 2 DONE
- Speech-to-text: vosk small English model (~40 MB, to be downloaded) — Phase 3
- Face detection: OpenCV Haar cascade (built-in, no download) — Phase 4
- Face embeddings/recognition: OpenCV LBPHFaceRecognizer (built-in, no download) — Phase 5
- Scene understanding: Deferred (Phase 4) — local VLM too large for CPU-only; mark UNVERIFIED if needed
- TTS (optional): piper-tts (already installed, behind interface)

## Decisions
- See DECISIONS.md

## What works
- Project structure, venv, git, logging
- Event bus (pub/sub)
- Keyboard input loop (stdin, background thread)
- Trivial echo brain (subscribes to keyboard.input, echoes back)
- Kill switch (q key + Ctrl+C)
- LLM interface: gpt4all with Llama-3.2-1B-Instruct-Q4_0.gguf (737.2 MB, CPU, offline)
- --offline --scripted: model answers 3 scripted prompts (verified)
- pytest: 17 tests pass

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

## Next step
- Await "continue" to begin Phase 3 — Microphone + speech-to-text: capture, VAD, local transcription feeding the brain
- Phase 3 gate: a recorded test WAV transcribes correctly in tests; a live mic test succeeds, or is marked UNVERIFIED with the reason



