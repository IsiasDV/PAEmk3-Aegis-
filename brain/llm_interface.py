"""LLM interface stub.

Placeholder for the real local LLM brain (Phase 2: Llama-3.2-1B via gpt4all).
Defined here so the architecture is in place; the echo brain in planner.py
serves as the trivial brain for Phase 1.
"""

from __future__ import annotations


class LLMInterface:
    """Stub LLM interface — not yet wired in Phase 1."""

    def __init__(self, model_path: str) -> None:
        self.model_path = model_path

    def generate(self, prompt: str) -> str:
        raise NotImplementedError("LLM brain is implemented in Phase 2")
