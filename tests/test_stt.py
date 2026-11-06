"""Tests for the STT perception module.

Tests use synthetic WAV audio so they run without a microphone. The vosk
model is loaded from the existing model on this device.
"""

from __future__ import annotations

import json
import wave
from pathlib import Path

from pathlib import Path

import numpy as np
import pytest

from core.event_bus import EventBus
from perception.stt import Stt
from perception.vad import Vad

VOSK_MODEL = (
    "C:/Users/conta/Documents/DayToDayProjects/Portable Artifical Employee/"
    "paeMK1/models/vosk-model-small-en-us-0.15"
)


def _write_wav(path: Path, audio: np.ndarray, sample_rate: int = 16000) -> None:
    """Write float32 audio (-1..1) as a 16-bit mono WAV file."""
    pcm = (np.clip(audio, -1.0, 1.0) * 32767).astype(np.int16)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm.tobytes())


def test_stt_loads_model(tmp_path):
    """Stt.load() succeeds with a valid vosk model directory."""
    bus = EventBus()
    stt = Stt(bus, model_path=VOSK_MODEL)
    stt.load()
    assert stt._model is not None
    assert stt._rec is not None


def test_stt_raises_if_model_missing(tmp_path):
    """Stt with a nonexistent model path raises FileNotFoundError on load."""
    bus = EventBus()
    stt = Stt(bus, model_path=str(tmp_path / "no-such-model"))
    try:
        stt.load()
        assert False, "expected FileNotFoundError"
    except FileNotFoundError:
        pass


def test_stt_transcribe_wav_publishes_event(tmp_path):
    """transcribe_wav processes a WAV and publishes an stt.transcription event."""
    bus = EventBus()
    captured: list[dict] = []
    bus.subscribe("stt.transcription", captured.append)

    stt = Stt(bus, model_path=VOSK_MODEL)

    # Synthetic audio: 1 second of silence (no speech -> empty transcription)
    wav_path = tmp_path / "test.wav"
    _write_wav(wav_path, np.zeros(16000, dtype=np.float32))

    text = stt.transcribe_wav(str(wav_path))
    assert isinstance(text, str)
    assert len(captured) == 1
    assert captured[0]["source"] == str(wav_path)
    assert captured[0]["text"] == text


def test_stt_transcribe_wav_with_speech_like_audio(tmp_path):
    """transcribe_wav handles speech-like audio without crashing."""
    bus = EventBus()
    stt = Stt(bus, model_path=VOSK_MODEL)

    # Frequency sweep (chirp) to simulate varying audio
    t = np.linspace(0, 1, 16000, endpoint=False)
    audio = 0.3 * np.sin(2 * np.pi * np.linspace(200, 2000, 16000) * t)

    wav_path = tmp_path / "chirp.wav"
    _write_wav(wav_path, audio)

    text = stt.transcribe_wav(str(wav_path))
    assert isinstance(text, str)


def test_stt_transcribes_hello_world():
    """transcribe_wav correctly transcribes a real 'hello world' WAV file."""
    bus = EventBus()
    stt = Stt(bus, model_path=VOSK_MODEL)

    wav_path = Path("tests/test_hello.wav")
    assert wav_path.exists(), "test_hello.wav fixture missing"

    text = stt.transcribe_wav(str(wav_path))
    assert "hello" in text.lower(), f"Expected 'hello' in transcription, got: {text!r}"


def test_vad_detects_silence():
    """VAD reports silence for zero audio."""
    vad = Vad(sample_rate=16000, threshold=0.02)
    assert vad.is_speech(np.zeros(480, dtype=np.float32)) is False


def test_vad_detects_loud_tone():
    """VAD reports speech for a loud tone."""
    vad = Vad(sample_rate=16000, threshold=0.02)
    tone = 0.5 * np.sin(2 * np.pi * 440 * np.arange(480) / 16000)
    assert vad.is_speech(tone) is True
