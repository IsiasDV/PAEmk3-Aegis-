"""Face detection using OpenCV Haar cascade.

Detects faces in camera frames and returns bounding boxes. Designed to work
with the Haar cascade classifier (no model download required, fully offline).
"""

from __future__ import annotations

from typing import Optional

import cv2
import numpy as np


class FaceDetector:
    """Detects faces in images using OpenCV's Haar cascade classifier.

    Parameters
    ----------
    cascade_path:
        Absolute path to a Haar cascade XML file (e.g.
        haarcascade_frontalface_default.xml).
    scale_factor:
        Parameter specifying how much the image size is reduced at each
        image scale.
    min_neighbors:
        Parameter specifying how many neighbors each candidate rectangle
        should have to retain it.
    min_size:
        Minimum possible object size. Objects smaller than this are
        ignored.
    """

    def __init__(
        self,
        cascade_path: str,
        scale_factor: float = 1.1,
        min_neighbors: int = 5,
        min_size: tuple[int, int] = (30, 30),
    ) -> None:
        self.cascade_path = cascade_path
        self.scale_factor = scale_factor
        self.min_neighbors = min_neighbors
        self.min_size = min_size
        self._cascade: Optional[cv2.CascadeClassifier] = None

    def load(self) -> None:
        """Load the Haar cascade classifier. Raises FileNotFoundError if
        the cascade file does not exist."""
        if self._cascade is not None:
            return
        if not os.path.exists(self.cascade_path):
            raise FileNotFoundError(f"Haar cascade not found: {self.cascade_path}")
        self._cascade = cv2.CascadeClassifier(self.cascade_path)
        if self._cascade.empty():
            raise ValueError(f"Failed to load Haar cascade: {self.cascade_path}")

    def detect(self, frame: np.ndarray) -> list[dict]:
        """Detect faces in *frame*.

        Returns a list of dicts with keys: x, y, w, h (bounding box in
        pixels), and confidence (always 1.0 for Haar cascade).
        """
        self.load()
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self._cascade.detectMultiScale(
            gray,
            scaleFactor=self.scale_factor,
            minNeighbors=self.min_neighbors,
            minSize=self.min_size,
        )
        results: list[dict] = []
        for x, y, w, h in faces:
            results.append(
                {
                    "x": int(x),
                    "y": int(y),
                    "w": int(w),
                    "h": int(h),
                    "confidence": 1.0,
                }
            )
        return results

    @property
    def loaded(self) -> bool:
        return self._cascade is not None


import os
