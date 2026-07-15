"""
JARVIS OS - Voice Package
=========================

Offline-first speech synthesis and recognition primitives.

Exports:
    - VoiceService / get_voice_service  (high-level STT + TTS)
    - synthesize_speech                 (low-level formant TTS)
"""

from .tts import synthesize_speech, SpeechResult, list_voices, resolve_voice_id
from .piper_tts import synthesize_auto, piper_available, tts_status
from .service import VoiceService, get_voice_service

__all__ = [
    "synthesize_speech",
    "synthesize_auto",
    "SpeechResult",
    "list_voices",
    "resolve_voice_id",
    "VoiceService",
    "get_voice_service",
    "piper_available",
    "tts_status",
]
