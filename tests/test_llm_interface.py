"""Tests for the LLM interface (mocked — no 737 MB model loaded in unit tests)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from brain.llm_interface import LLMInterface


def test_llm_interface_raises_if_model_missing(tmp_path):
    """LLMInterface with a nonexistent model path raises FileNotFoundError on load."""
    missing = tmp_path / "nonexistent.gguf"
    llm = LLMInterface(model_path=str(missing))
    try:
        llm.load()
        assert False, "expected FileNotFoundError"
    except FileNotFoundError:
        pass


def test_llm_interface_raises_if_generate_before_load():
    """generate() before load() raises RuntimeError."""
    llm = LLMInterface(model_path="/nonexistent/model.gguf")
    try:
        llm.generate("hello")
        assert False, "expected RuntimeError"
    except RuntimeError:
        pass


def test_llm_interface_properties_before_load():
    """model_name and model_size_mb work before loading."""
    llm = LLMInterface(model_path="/some/path/model.gguf")
    assert llm.model_name == "model.gguf"
    assert llm.loaded is False


@patch("gpt4all.GPT4All")
def test_llm_interface_generate_returns_response(mock_gpt4all, tmp_path):
    """generate() returns the model's response text."""
    fake_model = tmp_path / "model.gguf"
    fake_model.write_bytes(b"\x00" * 100)

    mock_model = MagicMock()
    mock_model.generate.return_value = "Hello, I am Aegis."
    mock_gpt4all.return_value = mock_model

    llm = LLMInterface(model_path=str(fake_model))
    llm.load()  # triggers the patched GPT4All constructor
    assert llm.loaded is True

    response = llm.generate("Say hello")
    assert response == "Hello, I am Aegis."
    mock_model.generate.assert_called_once()
