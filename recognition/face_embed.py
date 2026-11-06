"""Face embedding and recognition using OpenCV LBPHFaceRecognizer.

LBPH (Local Binary Patterns Histograms) is a simple, effective face
recognition method that works fully offline on CPU. It produces a
confidence value where LOWER is better (more confident match).
"""

from __future__ import annotations

from typing import Optional

import cv2
import numpy as np


class FaceEmbedder:
    """Face embedding and recognition using OpenCV LBPHFaceRecognizer.

    Parameters
    ----------
    confidence_threshold:
        Maximum confidence value for a match. Lower = stricter. Default
        70.0 (LBPH returns distance-like values where lower is better).
    radius:
        LBPH radius parameter.
    neighbors:
        LBPH number of neighbors.
    grid_x:
        LBPH grid X size.
    grid_y:
        LBPH grid Y size.
    """

    def __init__(
        self,
        confidence_threshold: float = 70.0,
        radius: int = 1,
        neighbors: int = 8,
        grid_x: int = 8,
        grid_y: int = 8,
    ) -> None:
        self.confidence_threshold = confidence_threshold
        self._recognizer = cv2.face.LBPHFaceRecognizer_create(
            radius=radius, neighbors=neighbors, grid_x=grid_x, grid_y=grid_y
        )
        self._trained = False
        self._label_map: dict[int, str] = {}  # numeric label -> person_id
        self._reverse_map: dict[str, int] = {}  # person_id -> numeric label

    def train(self, embeddings_by_person: dict[str, list[np.ndarray]]) -> None:
        """Train the recognizer on *embeddings_by_person*, a dict mapping
        person_id to a list of face images (grayscale numpy arrays).

        Each image should be a cropped, aligned face region.
        """
        faces: list[np.ndarray] = []
        labels: list[int] = []
        self._label_map = {}
        self._reverse_map = {}

        for person_id, images in embeddings_by_person.items():
            if not images:
                continue
            label = len(self._label_map)
            self._label_map[label] = person_id
            self._reverse_map[person_id] = label
            for img in images:
                faces.append(img)
                labels.append(label)

        if faces:
            self._recognizer.train(faces, np.array(labels))
            self._trained = True

    def recognize(self, face_image: np.ndarray) -> tuple[Optional[str], float]:
        """Recognize *face_image* (a cropped grayscale face region).

        Returns a tuple of (person_id, confidence) where person_id is None
        if no confident match is found. Confidence is lower = better match.
        """
        if not self._trained:
            return None, float("inf")

        label, confidence = self._recognizer.predict(face_image)
        if confidence <= self.confidence_threshold:
            person_id = self._label_map.get(label)
            return person_id, float(confidence)
        return None, float(confidence)

    def is_trained(self) -> bool:
        return self._trained

    @property
    def enrolled_people(self) -> list[str]:
        return list(self._reverse_map.keys())
