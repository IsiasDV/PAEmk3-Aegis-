"""Aegis entry point.

Phase 3: wires together the event bus, config, runtime logging, keyboard
input loop, echo brain, LLM brain, and microphone + STT. Supports --offline
and a hard kill switch (q key / Ctrl+C). With --scripted, runs 3 scripted
prompts through the LLM and exits (Phase 2 gate). With --stt, enables
microphone + speech-to-text in the interactive loop.
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from typing import Optional

from brain.llm_interface import LLMInterface
from brain.prompt_templates import SYSTEM_PROMPT, scripted_prompt
from brain.planner import EchoBrain
from core.config import Config
from core.event_bus import EventBus
from core.logging_setup import setup_runtime_logging
from perception.keyboard import KeyboardInput
from perception.stt import Stt


SCRIPTED_PROMPTS = [
    "What are you?",
    "Describe what you can do right now.",
    "Say hello in one sentence.",
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Aegis — local live-interactive AI agent")
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Enforce fully offline operation (no network at runtime)",
    )
    parser.add_argument(
        "--scripted",
        action="store_true",
        help="Run 3 scripted prompts through the LLM and exit (Phase 2 gate)",
    )
    parser.add_argument(
        "--stt",
        action="store_true",
        help="Enable microphone + speech-to-text in the interactive loop",
    )
    parser.add_argument(
        "--config",
        default="config.yaml",
        help="Path to config.yaml",
    )
    return parser


def run_scripted(cfg: Config, offline: bool) -> int:
    """Run 3 scripted prompts through the local LLM and print responses."""
    if offline:
        print("[offline] enforced — no network access")

    model_path = cfg.get("llm.model_path")
    if not model_path:
        print("ERROR: llm.model_path not set in config.yaml")
        return 1

    llm = LLMInterface(
        model_path=str(model_path),
        max_tokens=int(cfg.get("llm.max_tokens", 256)),
        temperature=float(cfg.get("llm.temperature", 0.7)),
    )
    print(f"[brain] loading model: {llm.model_name} ({llm.model_size_mb:.1f} MB)")
    llm.load()

    print(f"[brain] system: {SYSTEM_PROMPT[:80]}...\n")
    for i, prompt_text in enumerate(SCRIPTED_PROMPTS, 1):
        full_prompt = scripted_prompt(i, prompt_text)
        response = llm.generate(full_prompt)
        print(f"--- Prompt {i}: {prompt_text}")
        print(f"Response: {response.strip()}\n")

    print("[brain] scripted run complete — model answered 3 scripted prompts")
    return 0


def run_interactive(cfg: Config, enable_stt: bool) -> int:
    """Run the interactive keyboard (+ optional STT) + echo brain loop."""
    print("Aegis is running. Press q or Ctrl+C to stop.")

    event_bus = EventBus()
    brain = EchoBrain(event_bus)
    kill_switch_key = str(cfg.get("keyboard.kill_switch_key", "q"))
    keyboard = KeyboardInput(event_bus, kill_switch_key=kill_switch_key)

    stt: Optional[Stt] = None
    if enable_stt:
        stt_model_path = cfg.get("stt.model_path")
        if not stt_model_path:
            print("ERROR: stt.model_path not set in config.yaml (use --stt)")
            return 1
        stt = Stt(
            event_bus,
            model_path=str(stt_model_path),
            sample_rate=int(cfg.get("microphone.sample_rate", 16000)),
            device_index=cfg.get("microphone.device_index"),
        )
        print(f"[stt] loading model: {stt.model_path}")

    def on_kill_switch() -> None:
        print("\n[main] kill switch engaged — stopping")

    keyboard.register_kill_callback(on_kill_switch)

    brain.start()
    keyboard.start()
    if stt is not None:
        stt.start()

    try:
        while keyboard.running:
            time.sleep(0.1)
    except KeyboardInterrupt:
        pass
    finally:
        keyboard.stop()
        if stt is not None:
            stt.stop()

    print("Aegis stopped.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    logger = setup_runtime_logging()
    logger.info(
        "Aegis starting (offline=%s, scripted=%s, stt=%s)",
        args.offline,
        args.scripted,
        args.stt,
    )

    try:
        cfg = Config.load(args.config)
    except FileNotFoundError as exc:
        logger.error("Configuration not found: %s", exc)
        return 1

    logger.info("Config loaded from %s", os.path.abspath(args.config))

    if args.scripted:
        return run_scripted(cfg, args.offline)

    return run_interactive(cfg, args.stt)


if __name__ == "__main__":
    sys.exit(main())
