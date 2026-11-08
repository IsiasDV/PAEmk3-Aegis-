"""Environment model — structured description of the agent's own system.

Produced by inspecting the real environment (files, modules, devices,
models, capabilities, known failures), not by guessing. Self-coding
proposals (Phase 8) must cite which part of this model motivated them.
"""

from __future__ import annotations

import importlib
import json
import os
import platform
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from typing import Any

from memory.db import MemoryDB


class EnvironmentModel:
    """Builds and maintains a structured, verified description of the
    agent's own system by inspecting the real environment.

    Parameters
    ----------
    db:
        A MemoryDB instance (shared across memory modules).
    """

    def __init__(self, db: MemoryDB) -> None:
        self.db = db

    def _utc_now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def inspect(self) -> dict[str, Any]:
        """Inspect the real environment and return a structured model."""
        model: dict[str, Any] = {
            "inspected_at": self._utc_now(),
            "system": self._inspect_system(),
            "python": self._inspect_python(),
            "devices": self._inspect_devices(),
            "models": self._inspect_models(),
            "capabilities": self._inspect_capabilities(),
            "known_failures": self._inspect_known_failures(),
        }
        self._persist(model)
        return model

    def _inspect_system(self) -> dict[str, Any]:
        try:
            import psutil  # type: ignore

            return {
                "os": platform.system(),
                "os_version": platform.version(),
                "architecture": platform.machine(),
                "processor": platform.processor(),
                "cpu_cores": os.cpu_count(),
                "ram_bytes": psutil.virtual_memory().total,
                "disk_free_bytes": shutil.disk_usage("/").free,
            }
        except Exception:  # noqa: BLE001
            return {
                "os": platform.system(),
                "os_version": platform.version(),
                "architecture": platform.machine(),
                "processor": platform.processor(),
                "cpu_cores": os.cpu_count(),
                "ram_bytes": 0,
                "disk_free_bytes": shutil.disk_usage("/").free,
                "error": "psutil not available",
            }

    def _inspect_python(self) -> dict[str, Any]:
        return {
            "version": sys.version,
            "executable": sys.executable,
            "version_info": list(sys.version_info),
        }

    def _inspect_devices(self) -> dict[str, Any]:
        devices: dict[str, Any] = {"camera": [], "microphone": []}

        try:
            import cv2  # type: ignore

            for idx in range(5):
                cap = cv2.VideoCapture(idx)
                if cap.isOpened():
                    ret, _ = cap.read()
                    devices["camera"].append(
                        {
                            "index": idx,
                            "available": ret,
                            "backend": cap.getBackendName()
                            if hasattr(cap, "getBackendName")
                            else "unknown",
                        }
                    )
                    cap.release()
                else:
                    cap.release()
        except Exception as exc:  # noqa: BLE001
            devices["camera"] = {"error": str(exc)}

        try:
            import sounddevice as sd  # type: ignore

            for dev in sd.query_devices():
                if dev.get("max_input_channels", 0) > 0:
                    devices["microphone"].append(
                        {
                            "index": dev.get("index"),
                            "name": dev.get("name"),
                            "channels": dev.get("max_input_channels"),
                        }
                    )
        except Exception as exc:  # noqa: BLE001
            devices["microphone"] = {"error": str(exc)}

        return devices

    def _inspect_models(self) -> dict[str, Any]:
        models: dict[str, Any] = {}

        try:
            from gpt4all import GPT4All  # type: ignore

            models["gpt4all_available"] = True
        except Exception:  # noqa: BLE001
            models["gpt4all_available"] = False

        try:
            import vosk  # type: ignore

            models["vosk_available"] = True
        except Exception:  # noqa: BLE001
            models["vosk_available"] = False

        try:
            import cv2  # type: ignore

            models["opencv_version"] = cv2.__version__
            models["opencv_has_cascade"] = hasattr(cv2, "CascadeClassifier")
            models["opencv_has_face"] = hasattr(cv2, "face")
        except Exception:  # noqa: BLE001
            models["opencv_available"] = False

        return models

    def _inspect_capabilities(self) -> dict[str, Any]:
        caps: dict[str, Any] = {}
        for mod_name in ["cv2", "sounddevice", "vosk", "gpt4all", "yaml", "numpy"]:
            try:
                importlib.import_module(mod_name)
                caps[mod_name] = True
            except Exception:  # noqa: BLE001
                caps[mod_name] = False
        return caps

    def _inspect_known_failures(self) -> list[str]:
        failures: list[str] = []

        try:
            import cv2  # type: ignore

            if not hasattr(cv2, "CascadeClassifier"):
                failures.append("cv2.CascadeClassifier unavailable (need opencv-contrib)")
            if not hasattr(cv2, "face"):
                failures.append("cv2.face unavailable (need opencv-contrib for LBPH)")
        except Exception:
            failures.append("opencv not importable")

        try:
            import gpt4all  # type: ignore
        except Exception:
            failures.append("gpt4all not importable")

        try:
            import vosk  # type: ignore
        except Exception:
            failures.append("vosk not importable")

        return failures

    def _persist(self, model: dict[str, Any]) -> None:
        self.db.execute(
            """
            INSERT OR REPLACE INTO environment (key, value, updated_at)
            VALUES (?, ?, ?)
            """,
            ("full_model", json.dumps(model, indent=2), model["inspected_at"]),
        )
        self.db.commit()

    def get(self) -> dict[str, Any] | None:
        """Return the last persisted environment model, or None."""
        row = self.db.execute(
            "SELECT value FROM environment WHERE key = 'full_model'"
        ).fetchone()
        if row is None:
            return None
        return json.loads(row["value"])

