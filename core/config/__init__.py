"""
JARVIS OS - Core Configuration Module
=====================================

Production-grade, type-safe configuration system.

Features:
- Pydantic v2 Settings with validation
- Environment variable overrides (JARVIS_* prefix)
- Nested configuration models
- Offline-first sensible defaults
- Secure secret handling (never logged)
- Path resolution for models, database, logs
- Environment profiles (dev / prod / test)
- Hot-reload support in dev (future)

Usage:
    from core.config import get_settings, Settings

    settings = get_settings()
    print(settings.ai.model)

All other modules should use dependency injection of Settings
rather than importing get_settings directly in business logic.
"""

from .settings import ConfigError, Settings, _clear_settings_cache, get_settings

__all__ = [
    "Settings",
    "get_settings",
    "ConfigError",
    "_clear_settings_cache",
]
