"""Voice activity detection (VAD).

Simple energy-based VAD: computes RMS energy over short audio frames and
flags frames whose energy exceeds a threshold. Pure numpy — no extra
dependencies beyond sounddevice/numpy which are already required.

Designed to work with recorded/mock audio so tests pass without hardware.
"""

from __future__ import annotations

import numpy as np


class Vad:
    """Energy-based voice activity detector.

    Parameters
    ----------
    sample_rate:
        Audio sample rate in Hz (used only for reporting, not computation).
    frame_ms:
        Analysis frame length in milliseconds.
    threshold:
        RMS energy threshold above which a frame is considered speech.
    """

    def __init__(self, sample_rate: int = 16000, frame_ms: int = 30, threshold: float = 0.02) -> None:
        self.sample_rate = sample_rate
        self.frame_ms = frame_ms
        self.threshold = threshold
        self.frame_size = int(sample_rate * frame_ms / 1000)

    def is_speech(self, frame: np.ndarray) -> bool:
        """Return True if *frame* contains speech (energy above threshold)."""
        if frame.size == 0:
            return False
        rms = float(np.sqrt(np.mean(np.square(frame.astype(np.float32)))))
        return rms > self.threshold

    def iter_frames(self, audio: np.ndarray):
        """Yield (frame, is_speech) tuples for non-overlapping frames of *audio*."""
        for start in range(0, len(audio) - self.frame_size + 1, self.frame_size):
            frame = audio[start : start + self.frame_size]
            yield frame, self.is_speech(frame)
