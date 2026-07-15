"""
JARVIS OS - Speech-to-Text (STT)
================================

Real-time transcription using faster-whisper.

Features:
- Local inference (no cloud)
- Multiple model sizes
- VAD-based segmentation
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from loguru import logger

try:
    from faster_whisper import WhisperModel
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False

from core.config import get_settings


class SpeechToText:
    """Local speech-to-text engine."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self._model: Any = None
        self._loaded = False

    def _load(self) -> None:
        if self._loaded or not WHISPER_AVAILABLE:
            return
        try:
            self._model = WhisperModel(
                self.settings.voice.stt_model,
                device=self.settings.voice.device,
                compute_type="int8",
            )
            self._loaded = True
            logger.success(f"Whisper model loaded: {self.settings.voice.stt_model}")
        except Exception as e:
            logger.warning(f"Failed to load Whisper: {e}")

    def transcribe(self, audio_path: Path | str) -> str:
        self._load()
        if self._model is None:
            return "[STT unavailable — Whisper not installed]"

        segments, _ = self._model.transcribe(str(audio_path), language=self.settings.voice.language)
        return " ".join([s.text for s in segments]).strip()


_stt: SpeechToText | None = None


def get_stt() -> SpeechToText:
    global _stt
    if _stt is None:
        _stt = SpeechToText()
    return _stt
