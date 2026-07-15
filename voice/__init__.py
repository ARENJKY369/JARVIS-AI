"""
JARVIS OS - Voice Pipeline
==========================

Speech-to-text and text-to-speech services.

Components:
- STT: faster-whisper integration
- TTS: Piper TTS integration
"""

from .stt import SpeechToText, get_stt
from .tts import TextToSpeech, get_tts

__all__ = ["SpeechToText", "get_stt", "TextToSpeech", "get_tts"]
