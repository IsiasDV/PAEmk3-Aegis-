# Aegis — Local, Live-Interactive AI Agent

A local, offline-capable AI agent with camera, microphone, keyboard input, face recognition, scene understanding, persistent memory, and supervised self-coding.

## Project structure
```
aegis/
  CHANGELOG.md  STATE.md  DECISIONS.md  config.yaml  requirements.txt  README.md
  logs/            (changes.jsonl, runtime.log, self_mod.jsonl)
  core/            (event_bus.py, scheduler.py, config.py, logging_setup.py)
  perception/      (camera.py, microphone.py, keyboard.py, stt.py, vad.py)
  recognition/     (face_detect.py, face_embed.py, enrollment.py, identity_store.py)
  vision/          (scene_describer.py)
  brain/           (llm_interface.py, planner.py, prompt_templates.py)
  memory/          (db.py, episodic.py, people.py, environment_model.py)
  tools/           (registry.py, safe_tools.py)
  selfmod/         (sandbox.py, proposer.py, validator.py, applier.py, protected_paths.py)
  tests/
  main.py
```

## Setup
1. Create and activate the virtual environment:
   ```
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```
2. Download models (see `STATE.md` for model sources already on this device).
3. Edit `config.yaml` to point `llm.model_path`, `stt.model_path`, and `face.cascade_path` to the downloaded model files.
4. Run:
   ```
   python main.py
   ```

## Controls
- `q` key — hard kill switch (stops all capture immediately)
- `Ctrl+C` — hard kill switch

## Privacy
- Face recognition is opt-in by enrollment only. Unenrolled faces are reported as "an unrecognized person" and never stored.
- Face data stays local as embeddings only. No raw face images retained.
- No camera, audio, or identity data is transmitted over the network.

## Phases
See `STATE.md` for current phase and next steps. See `CHANGELOG.md` for change history.
