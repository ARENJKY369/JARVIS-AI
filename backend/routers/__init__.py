"""
JARVIS OS - API Routers Package

All routers are cleanly importable.
"""
from .health import router as health_router
from .system import router as system_router

__all__ = ["health_router", "system_router"]
