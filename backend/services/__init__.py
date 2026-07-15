"""
JARVIS OS - Backend Services Layer
==================================

Services contain the core business logic.

All services are:
- Stateless where possible
- Depend on core primitives (config, security, memory)
- Fully type-hinted
- Async-friendly
"""

from .ai_service import AIService, get_ai_service
from .voice_service import VoiceService, get_voice_service

__all__ = [
    "AIService",
    "get_ai_service",
    "VoiceService",
    "get_voice_service",
]
