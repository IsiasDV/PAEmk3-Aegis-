"""Aegis entry point.

Phase 0: minimal stub that initializes logging, loads config, and prints
a startup banner. Phase 1 adds the keyboard input loop, event bus, and
echo brain.
"""

from __future__ import annotations

import argparse
import sys

from core.config import Config
from core.logging_setup import setup_runtime_logging


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
    return 0


if __name__ == "__main__":
    import os  # noqa: E402  (imported late to avoid circular style issues)

    sys.exit(main())
