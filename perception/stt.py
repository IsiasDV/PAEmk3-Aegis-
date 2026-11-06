"""Speech-to-text perception module.

Uses vosk for offline speech recognition. Reads audio from a WAV file (for
tests) or from a microphone device (live), runs VAD to gate recognition, and
publishes ``stt.transcription`` events on the event bus.

Perception modules only publish events — the brain subscribes and decides.
"""

from __future__ import annotations

import threading
import wave
from typing import Callable, Optional

import numpy as np
import sounddevice as sd
import vosk
from core.event_bus import EventBus
from perception.vad import Vad


class Stt:
    """Offline speech-to-text using vosk."""

    def __init__(
        self,
        event_bus: EventBus,
        model_path: str,
        sample_rate: int = 16000,
        device_index: Optional[int] = None,
    ) -> None:
        self.event_bus = event_bus
        self.model_path = model_path
        self.sample_rate = sample_rate
        self.device_index = device_index
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._model: Optional[object] = None
        self._rec: Optional[object] = None
        self._vad = Vad(sample_rate=sample_rate)
        self._on_transcription: list[Callable[[str], None]] = []

    def load(self) -> None:
        """Load the vosk model. Raises FileNotFoundError if the path is invalid."""
        if self._model is not None:
            return
        import os

        if not os.path.isdir(self.model_path):
            raise FileNotFoundError(f"Vosk model not found: {self.model_path}")
        self._model = vosk.Model(self.model_path)
        self._rec = vosk.KaldiRecognizer(self._model, self.sample_rate)

    def transcribe_wav(self, wav_path: str) -> str:
        """Transcribe a WAV file and return the recognized text.

        Uses the WAV file's native sample rate for vosk (avoids crude
        resampling that degrades recognition quality). Runs VAD gating at
        the native rate: only speech frames are fed to the recognizer.
        """
        import json
        import os

        self.load()
        if not os.path.exists(wav_path):
            raise FileNotFoundError(f"WAV file not found: {wav_path}")

        with wave.open(wav_path, "rb") as wf:
            n_channels = wf.getnchannels()
            framerate = wf.getframerate()
            raw = wf.readframes(wf.getnframes())

        audio = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
        if n_channels > 1:
            audio = audio.reshape(-1, n_channels).mean(axis=1)

        # Use the WAV's native rate for vosk and VAD.
        rec = vosk.KaldiRecognizer(self._model, framerate)
        vad = Vad(sample_rate=framerate)

        chunk = vad.frame_size
        results: list[str] = []
        buffer = np.zeros(0, dtype=np.float32)
        for start in range(0, len(audio) - chunk + 1, chunk):
            frame = audio[start : start + chunk]
            if vad.is_speech(frame):
                buffer = np.concatenate([buffer, frame])
                if len(buffer) >= chunk * 4:
                    pcm = (buffer * 32768).astype(np.int16).tobytes()
                    if rec.AcceptWaveform(pcm):
                        results.append(json.loads(rec.Result())["text"])
                    buffer = np.zeros(0, dtype=np.float32)

        if len(buffer) > 0:
            pcm = (buffer * 32768).astype(np.int16).tobytes()
            if rec.AcceptWaveform(pcm):
                results.append(json.loads(rec.Result())["text"])
        final = json.loads(rec.FinalResult())["text"] if rec else ""
        if final:
            results.append(final)

        text = " ".join(r for r in results if r).strip()
        self.event_bus.publish("stt.transcription", {"text": text, "source": wav_path})
        return text

    def register_transcription_callback(self, cb: Callable[[str], None]) -> None:
        """Register a callback to run when a transcription is produced."""
        self._on_transcription.append(cb)

    def start(self) -> None:
        """Start live microphone transcription in a background thread."""
        if self._running:
            return
        self.load()
        self._running = True
        self._thread = threading.Thread(target=self._live_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop live transcription."""
        self._running = False

    def _live_loop(self) -> None:
        """Capture microphone audio, VAD-gate it, and transcribe."""
        chunk = self._vad.frame_size
        buffer = np.zeros(0, dtype=np.float32)

        def callback(indata: np.ndarray, frames: int, time_info, status) -> None:
            nonlocal buffer
            if not self._running:
                return
            mono = indata[:, 0] if indata.ndim > 1 else indata
            frame = mono.astype(np.float32)
            if self._vad.is_speech(frame):
                buffer = np.concatenate([buffer, frame])
                if len(buffer) >= chunk * 4:
                    pcm = (buffer * 32768).astype(np.int16).tobytes()
                    if self._rec and self._rec.AcceptWaveform(pcm):
                        import json

                        text = json.loads(self._rec.Result())["text"].strip()
                        if text:
                            self.event_bus.publish(
                                "stt.transcription", {"text": text, "source": "microphone"}
                            )
                            for cb in list(self._on_transcription):
                                try:
                                    cb(text)
                                except Exception:  # noqa: BLE001
                                    pass
                    buffer = np.zeros(0, dtype=np.float32)

        with sd.InputStream(
            samplerate=self.sample_rate,
            channels=1,
            dtype="int16",
            device=self.device_index,
            blocksize=chunk,
            callback=callback,
        ):
            while self._running:
                threading.Event().wait(0.1)

    @property
    def running(self) -> bool:
        return self._running
