"""Scene description module.

Provides a scene description interface with two backends:

1. **SimpleDescriber** (default, always available): produces a sensible
   description from basic image properties (brightness, dominant color,
   edge density). No model download required; works fully offline on any
   hardware.

2. **VlmDescriber** (stub): interface for a local vision-language model
   (e.g. Moondream, LLaVA, Qwen-VL). Marked UNVERIFIED on this device
   because no VLM model is available and the hardware (Intel UHD, 1 GB
   shared VRAM, CPU-only) cannot run a 2–8 GB VLM at usable speed.

Perception modules only publish events — the brain subscribes and decides.
"""

from __future__ import annotations

from typing import Optional

import cv2
import numpy as np
from core.event_bus import EventBus
from core.logging_setup import get_logger

logger = get_logger()


class SceneDescriber:
    """Describes what is visible in a camera frame.

    Parameters
    ----------
    event_bus:
        Event bus to publish ``vision.scene_description`` events on.
    use_vlm:
        If True, attempt to use a VLM backend. Since no VLM model is
        installed on this device, this falls back to the simple describer
        and logs that the VLM path is UNVERIFIED.
    """

    def __init__(self, event_bus: EventBus, use_vlm: bool = False) -> None:
        self.event_bus = event_bus
        self.use_vlm = use_vlm
        self._vlm_available = False
        self._vlm_reason: Optional[str] = None
        if use_vlm:
            self._vlm_available, self._vlm_reason = self._check_vlm()
        self._description_count = 0

    def _check_vlm(self) -> tuple[bool, Optional[str]]:
        """Check whether a VLM backend is available.

        Returns (False, reason) on this device because no VLM model exists
        locally and CPU-only hardware cannot run one at usable speed.
        """
        reason = (
            "No local VLM model found (Moondream/LLaVA/Qwen-VL not downloaded), "
            "and CPU-only Intel UHD with 1 GB shared VRAM cannot run a "
            "2–8 GB VLM at usable speed. Marked UNVERIFIED."
        )
        logger.info("VLM scene description: %s", reason)
        return False, reason

    def describe(self, frame: np.ndarray) -> str:
        """Produce a text description of *frame*.

        Falls back to the simple describer when no VLM is available.
        """
        if self._vlm_available:
            return self._describe_vlm(frame)
        return self._describe_simple(frame)

    def _describe_simple(self, frame: np.ndarray) -> str:
        """Produce a sensible description from basic image properties."""
        self._description_count += 1
        h, w = frame.shape[:2]

        # Convert to HSV for color analysis
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        brightness = float(np.mean(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)))

        # Dominant hue
        hue_hist = np.bincount(hsv[:, :, 0].ravel(), minlength=180)
        dominant_hue = int(np.argmax(hue_hist))
        hue_name = self._hue_name(dominant_hue)

        # Edge density (texture detail)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        edge_density = float(np.mean(edges > 0))

        # Saturation (colorfulness)
        saturation = float(np.mean(hsv[:, :, 1]))

        brightness_word = (
            "bright" if brightness > 120 else "dim" if brightness < 60 else "moderately lit"
        )
        color_word = (
            "colorful" if saturation > 80 else "muted" if saturation < 40 else "neutral"
        )
        detail_word = (
            "detailed" if edge_density > 0.05 else "simple" if edge_density < 0.02 else "moderately detailed"
        )

        description = (
            f"A {brightness_word}, {color_word} indoor scene, {detail_word}, "
            f"with {hue_name} tones. Image size: {w}x{h}."
        )

        self.event_bus.publish(
            "vision.scene_description",
            {
                "description": description,
                "source": "simple",
                "frame_size": [w, h],
                "brightness": brightness,
                "edge_density": edge_density,
                "saturation": saturation,
            },
        )
        return description

    def _describe_vlm(self, frame: np.ndarray) -> str:
        """Stub for VLM-based description — not implemented on this device."""
        raise NotImplementedError("VLM scene description is not available on this device")

    @staticmethod
    def _hue_name(hue: int) -> str:
        """Map OpenCV hue (0–179) to a color name."""
        if hue < 5 or hue >= 175:
            return "red"
        if hue < 22:
            return "orange"
        if hue < 33:
            return "yellow"
        if hue < 78:
            return "green"
        if hue < 131:
            return "blue"
        if hue < 167:
            return "purple"
        return "pink"

    @property
    def description_count(self) -> int:
        return self._description_count

    @property
    def vlm_available(self) -> bool:
        return self._vlm_available

    @property
    def vlm_reason(self) -> Optional[str]:
        return self._vlm_reason
