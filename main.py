"""Aegis entry point.

Phase 1: wires together the event bus, config, runtime logging, keyboard
input loop, and the trivial echo brain. Supports --offline and a hard kill
switch (q key / Ctrl+C).
"""

from __future__ import annotations

import argparse
import os
import sys
import time

from core.config import Config
from core.event_bus import EventBus
from core.logging_setup import setup_runtime_logging
from brain.planner import EchoBrain
from perception.keyboard import KeyboardInput


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Aegis — local live-interactive AI agent")
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Enforce fully offline operation (no network at runtime)",
    )
    parser.add_argument(
        "--config",
        default="config.yaml",
        help="Path to config.yaml",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    logger = setup_runtime_logging()
    logger.info("Aegis starting (offline=%s)", args.offline)

    try:
        cfg = Config.load(args.config)
    except FileNotFoundError as exc:
        logger.error("Configuration not found: %s", exc)
        return 1

    logger.info("Config loaded from %s", os.path.abspath(args.config))
    print("Aegis is running. Press q or Ctrl+C to stop.")

    event_bus = EventBus()
    brain = EchoBrain(event_bus)
    kill_switch_key = str(cfg.get("keyboard.kill_switch_key", "q"))
    keyboard = KeyboardInput(event_bus, kill_switch_key=kill_switch_key)

    def on_kill_switch() -> None:
        print("\n[main] kill switch engaged — stopping")

    keyboard.register_kill_callback(on_kill_switch)

    brain.start()
    keyboard.start()

    try:
        while keyboard.running:
            time.sleep(0.1)
    except KeyboardInterrupt:
        pass
    finally:
        keyboard.stop()
        logger.info("Aegis stopped")

    print("Aegis stopped.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
