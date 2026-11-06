"""LLM interface backed by gpt4all with a local GGUF model.

Runs fully offline after the one-time model download. Any model can be swapped
later by changing ``config.yaml`` and reimplementing behind this same interface
(Section 1: design every model behind an interface).
"""

from __future__ import annotations

import os
from typing import Optional

from core.logging_setup import get_logger

logger = get_logger()


class LLMInterface:
    """Local LLM interface backed by gpt4all (llama.cpp backend).

    Parameters
    ----------
    model_path:
        Absolute path to a GGUF model file. If the file does not exist,
        :meth:`load` raises ``FileNotFoundError`` rather than falling back
        silently (Section 0 rule 6: no silent fallbacks).
    max_tokens:
        Maximum number of tokens to generate per response.
    temperature:
        Sampling temperature (0.0 = deterministic, 1.0 = creative).
    """

    def __init__(
        self,
        model_path: str,
        max_tokens: int = 256,
        temperature: float = 0.7,
    ) -> None:
        self.model_path = os.path.abspath(model_path)
        self.max_tokens = max_tokens
        self.temperature = temperature
        self._model: Optional[object] = None
        self._loaded = False

    def load(self) -> None:
        """Load the model into memory. Call before :meth:`generate`.

        Enforces offline operation: gpt4all is pointed at the local model file
        and is not allowed to download anything.
        """
        if self._loaded:
            return
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"LLM model not found: {self.model_path}")
        try:
            from gpt4all import GPT4All  # imported lazily so this module loads
            # without gpt4all installed

            model_name = os.path.basename(self.model_path)
            model_dir = os.path.dirname(self.model_path)
            self._model = GPT4All(
                model_name=model_name,
                model_path=model_dir,
                allow_download=False,  # enforce offline: never fetch from network
            )
            self._loaded = True
            logger.info(
                "LLM model loaded: %s (%.1f MB)",
                self.model_path,
                os.path.getsize(self.model_path) / 1024 / 1024,
            )
        except Exception as exc:  # noqa: BLE001 - surface model load errors
            logger.error("Failed to load LLM model %s: %s", self.model_path, exc)
            raise

    def generate(
        self, prompt: str, max_tokens: Optional[int] = None, temperature: Optional[float] = None
    ) -> str:
        """Generate a completion for *prompt*.

        Raises ``RuntimeError`` if the model has not been loaded.
        """
        if not self._loaded:
            raise RuntimeError("LLM model not loaded; call load() first")
        try:
            response = self._model.generate(
                prompt,
                max_tokens=max_tokens or self.max_tokens,
                temp=temperature if temperature is not None else self.temperature,
            )
            logger.info("LLM generated %d chars", len(response))
            return response
        except Exception as exc:  # noqa: BLE001
            logger.error("LLM generation failed: %s", exc)
            raise

    @property
    def loaded(self) -> bool:
        return self._loaded

    @property
    def model_name(self) -> str:
        return os.path.basename(self.model_path)

    @property
    def model_size_mb(self) -> float:
        return os.path.getsize(self.model_path) / 1024 / 1024
