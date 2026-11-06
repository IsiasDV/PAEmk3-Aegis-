"""Prompt template stub.

Placeholder for prompt templates (Phase 2). Defined here so the architecture
is in place; no templates are needed for the Phase 1 echo brain.
"""

from __future__ import annotations


def echo_prompt(text: str) -> str:
    """Return a trivial echo prompt for Phase 1."""
    return f"Echo: {text}"
