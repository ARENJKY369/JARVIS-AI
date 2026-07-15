"""
JARVIS OS - API Routers Package

All routers are cleanly importable.
"""
from .health import router as health_router
from .system import router as system_router
from .ai import router as ai_router
from .voice import router as voice_router
from .memory import router as memory_router
from .root import router as root_router

__all__ = [
    "health_router",
    "system_router",
    "ai_router",
    "voice_router",
    "memory_router",
    "root_router",
]
