"""Aegis recognition module: face detection, face embeddings, enrollment, identity store."""

from __future__ import annotations

from recognition.identity_store import IdentityStore
from recognition.face_detect import FaceDetector
from recognition.face_embed import FaceEmbedder
from recognition.enrollment import EnrollmentManager

__all__ = [
    "IdentityStore",
    "FaceDetector",
    "FaceEmbedder",
    "EnrollmentManager",
]
