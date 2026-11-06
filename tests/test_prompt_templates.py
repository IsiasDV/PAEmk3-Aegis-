"""Tests for prompt templates."""

from __future__ import annotations

from brain.prompt_templates import SYSTEM_PROMPT, scripted_prompt, user_prompt


def test_system_prompt_nonempty():
    """The system prompt is defined and nonempty."""
    assert isinstance(SYSTEM_PROMPT, str)
    assert len(SYSTEM_PROMPT) > 0
    assert "Aegis" in SYSTEM_PROMPT


def test_user_prompt_wraps_text():
    """user_prompt wraps raw text with the expected prefix/suffix."""
    result = user_prompt("hello there")
    assert "hello there" in result
    assert result.endswith("Aegis:")


def test_scripted_prompt_includes_index():
    """scripted_prompt includes the prompt index."""
    result = scripted_prompt(2, "What are you?")
    assert "[Scripted prompt 2]" in result
    assert "What are you?" in result
