"""Configuration loader for Aegis.

Reads `config.yaml` and provides typed access to settings. No hard-coded
paths or device indices live in code — everything is configurable here.
"""

from __future__ import annotations

import os
from typing import Any

import yaml

DEFAULT_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "config.yaml")


class Config:
    """Wrapper around a YAML configuration file.

    Values are accessed via nested attribute-style lookup:
        cfg = Config.load()
        cfg.camera.index
    """

    def __init__(self, data: dict[str, Any]) -> None:
        self._data = data

    @classmethod
    def load(cls, path: str = DEFAULT_CONFIG_PATH) -> "Config":
        """Load configuration from *path* (defaults to project config.yaml)."""
        resolved = os.path.abspath(path)
        if not os.path.exists(resolved):
            raise FileNotFoundError(f"Config file not found: {resolved}")
        with open(resolved, "r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh) or {}
        return cls(data)

    def get(self, dotted_key: str, default: Any = None) -> Any:
        """Look up a value by dotted key (e.g. ``camera.index``)."""
        node: Any = self._data
        for part in dotted_key.split("."):
            if not isinstance(node, dict):
                return default
            node = node.get(part, default)
            if node is None:
                return default
        return node

    def __getattr__(self, name: str) -> Any:
        if name.startswith("_"):
            raise AttributeError(name)
        section = self._data.get(name)
        if isinstance(section, dict):
            return _Section(section)
        return section


class _Section:
    """Helper to allow attribute-style access to a config section dict."""

    def __init__(self, data: dict[str, Any]) -> None:
        self._data = data

    def __getattr__(self, name: str) -> Any:
        if name.startswith("_"):
            raise AttributeError(name)
        value = self._data.get(name)
        if isinstance(value, dict):
            return _Section(value)
        return value

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)
