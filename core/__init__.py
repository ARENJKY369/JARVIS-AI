"""
JARVIS OS - Core Shared Primitives
==================================

This package contains the foundational, reusable components used across
the entire JARVIS OS system:

- Configuration management (type-safe, env-driven)
- Security primitives (permissions, sandbox, crypto helpers)
- Shared memory interfaces
- Logging and error handling
- Dependency injection containers

Design Principles:
- Zero side effects on import
- Fully type-hinted
- Offline-first defaults
- Thread/async safe where applicable
- Production hardened

All higher-level modules (backend, agents, etc.) MUST import from here
for shared concerns.
"""

from .config import Settings, get_settings

__version__ = "1.0.0"
__all__ = ["get_settings", "Settings"]
