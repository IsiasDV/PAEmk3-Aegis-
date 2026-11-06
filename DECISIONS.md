# DECISIONS.md

## D-0001: Project root directory
**Decision:** All project code lives under `./aegis/` (created), per prompt Section 0 rule 7.
**Reason:** Prompt mandates staying inside `./aegis/`.

## D-0002: Language model
**Decision:** Use existing `Llama-3.2-1B-Instruct-Q4_0.gguf` (~737 MB) via `gpt4all` (already installed).
**Reason:** Already on device, CPU-friendly, fits disk, fully offline after download. Path of least resistance.

## D-0003: Speech-to-text
**Decision:** Use `vosk` (already installed) with `vosk-model-small-en-us-0.15` (~40 MB, to be downloaded).
**Reason:** `vosk` package is already installed; fully offline; small; CPU-friendly. The existing `ggml-base.en.bin` is whisper.cpp format, not directly usable by the vosk Python package.

## D-0004: Face detection
**Decision:** Use OpenCV Haar cascade (`haarcascade_frontalface_default.xml`, already on device) via `opencv-python-headless`.
**Reason:** Already on device, no extra dependency, works offline, CPU-friendly.

## D-0005: Face embeddings/recognition
**Decision:** Use OpenCV `LBPHFaceRecognizer` (built-in to opencv-python-headless).
**Reason:** Avoids `dlib`/`insightface` which are difficult to install on Windows + Python 3.13. Stores embeddings only (no raw face images), per privacy rules.

## D-0006: Scene understanding
**Decision:** Deferred to Phase 4; mark UNVERIFIED if no suitable small local VLM fits hardware.
**Reason:** Local VLMs (Moondream/LLaVA/Qwen-VL) are 2–8 GB and require GPU for usable speed; this machine has only 1 GB shared VRAM.

## D-0007: Default camera / microphone
**Decision:** Default camera = "Integrated Webcam"; default microphone = built-in microphone. Both are configurable in `config.yaml` and switchable at runtime.
**Reason:** User specified integrated camera as default and default built-in mic, with ability to switch both.

## D-0008: Virtual environment
**Decision:** Project-local venv at `aegis/.venv` with Python 3.13.
**Reason:** Prompt Section 3 requires project-local venv with pinned dependencies.

## D-0009: Configuration
**Decision:** Configuration in `config.yaml`, no hard-coded paths or device indices.
**Reason:** Prompt Section 3 rule.

## D-0010: Model storage location
**Decision:** Models stored outside `aegis/` source tree (referenced by absolute path in config.yaml) to avoid bloating the git repo.
**Reason:** Model files are large (hundreds of MB to GB) and should not be version-controlled.
