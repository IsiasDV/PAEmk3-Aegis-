"""Prompt templates for the Aegis brain.

Templates are kept separate from the LLM interface so they can be versioned,
tested, and swapped independently of the model backend.
"""

from __future__ import annotations

SYSTEM_PROMPT = """You are Aegis, a local, offline AI agent. You see through a camera,
hear through a microphone, and read keyboard input. You recognize enrolled
people by face and describe what you see. You answer concisely and helpfully.
You never transmit camera, audio, or identity data over the network.
Current mode: keyboard input only (Phase 2)."""


def user_prompt(text: str) -> str:
    """Wrap raw user input into a prompt for the LLM."""
    return f"User: {text}\nAegis:"


def scripted_prompt(index: int, text: str) -> str:
    """Format a scripted prompt for Phase 2 gate testing."""
    return f"[Scripted prompt {index}] {user_prompt(text)}"
