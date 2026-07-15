"""
JARVIS OS - Voice Service re-export
===================================

Thin adapter so routers import from backend.services consistently.
"""

from voice.service import (
    VoiceService,
    get_voice_service,
    TranscriptionResult,
    VoiceCommandResult,
)
from voice.tts import SpeechResult, synthesize_speech

__all__ = [
    "VoiceService",
    "get_voice_service",
    "TranscriptionResult",
    "VoiceCommandResult",
    "SpeechResult",
    "synthesize_speech",
]
