"""Enrollment flow for face recognition.

Enrollment is opt-in by consent only. A person is recognized only after
they are enrolled with their explicit consent. Unenrolled faces are
reported only as "an unrecognized person", never stored.
"""

from __future__ import annotations

from typing import Optional

import numpy as np

from recognition.identity_store import IdentityStore


class EnrollmentManager:
    """Manages face enrollment with consent.

    Parameters
    ----------
    identity_store:
        The identity store where enrolled people are persisted.
    face_detector:
        Face detector for cropping face regions from frames.
    face_embedder:
        Face recognizer for embedding faces.
    min_enrollment_samples:
        Minimum number of face samples required to enroll a person.
    """

    def __init__(
        self,
        identity_store: IdentityStore,
        face_detector,
        face_embedder,
        min_enrollment_samples: int = 3,
    ) -> None:
        self.identity_store = identity_store
        self.face_detector = face_detector
        self.face_embedder = face_embedder
        self.min_enrollment_samples = min_enrollment_samples
        self._pending_enrollment: Optional[str] = None
        self._consent_given = False
        self._samples: list[np.ndarray] = []

    def request_enrollment(self, person_id: str) -> str:
        """Request enrollment for *person_id*. Returns a prompt asking for
        consent. The person must be present and agree."""
        self._pending_enrollment = person_id
        self._consent_given = False
        self._samples = []
        return (
            f"Enrollment requested for '{person_id}'. "
            f"Please confirm consent (yes/no). "
            f"This will store your face embedding locally for recognition."
        )

    def grant_consent(self) -> None:
        """Record that the pending enrollment has given consent."""
        self._consent_given = True

    def deny_consent(self) -> None:
        """Record that the pending enrollment has denied consent and
        cancel enrollment."""
        self._pending_enrollment = None
        self._consent_given = False
        self._samples = []

    def add_sample(self, face_image: np.ndarray) -> bool:
        """Add a face sample for the pending enrollment. Returns True if
        the sample was accepted. Requires consent to have been granted."""
        if self._pending_enrollment is None or not self._consent_given:
            return False
        self._samples.append(face_image)
        return True

    def complete_enrollment(self) -> str:
        """Finalize enrollment. Stores embeddings and consent in the
        identity store and trains the face embedder.

        Returns a status message.
        """
        person_id = self._pending_enrollment
        if person_id is None:
            return "No pending enrollment."
        if not self._consent_given:
            self._pending_enrollment = None
            self._consent_given = False
            self._samples = []
            return "Consent not given. Enrollment cancelled."
        if len(self._samples) < self.min_enrollment_samples:
            self._pending_enrollment = None
            self._consent_given = False
            self._samples = []
            return (
                f"Not enough samples ({len(self._samples)}/"
                f"{self.min_enrollment_samples}). Enrollment cancelled."
            )

        # Store each sample as an embedding (as grayscale face image arrays)
        for sample in self._samples:
            self.identity_store.add_embedding(person_id, sample.tolist())
        self.identity_store.set_consent(person_id, True)
        self.identity_store.save()

        # Retrain the embedder with all enrolled people
        self._retrain_embedder()

        result = (
            f"Enrollment complete for '{person_id}' with "
            f"{len(self._samples)} samples."
        )
        self._pending_enrollment = None
        self._consent_given = False
        self._samples = []
        return result

    def cancel_enrollment(self) -> str:
        """Cancel the pending enrollment without saving anything."""
        person_id = self._pending_enrollment
        self._pending_enrollment = None
        self._consent_given = False
        self._samples = []
        if person_id:
            return f"Enrollment cancelled for '{person_id}'."
        return "No pending enrollment to cancel."

    def is_enrolling(self) -> bool:
        return self._pending_enrollment is not None

    def pending_person(self) -> Optional[str]:
        return self._pending_enrollment

    def consent_given(self) -> bool:
        return self._consent_given

    def sample_count(self) -> int:
        return len(self._samples)

    def _retrain_embedder(self) -> None:
        """Retrain the face embedder with all enrolled identities and
        their stored samples."""
        embeddings_by_person: dict[str, list[np.ndarray]] = {}
        for person_id in self.identity_store.list_people():
            embeddings = self.identity_store.get_embeddings(person_id)
            images = [np.array(e, dtype=np.uint8) for e in embeddings if e]
            if images:
                embeddings_by_person[person_id] = images
        self.face_embedder.train(embeddings_by_person)
