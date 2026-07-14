"""
JARVIS OS - Core Domain Exceptions
==================================

Base exceptions used across the entire system.

All application-level exceptions should inherit from these for
consistent error handling, logging, and API responses.

Hierarchy:
    JarvisError
    ├── ConfigError (in config/)
    ├── SecurityError
    ├── PermissionError (already in permissions)
    ├── AutomationError
    ├── VoiceError
    ├── VisionError
    └── MemoryError
"""

from __future__ import annotations

from typing import Any


class JarvisError(Exception):
    """Base exception for all JARVIS OS domain errors."""

    def __init__(
        self,
        message: str,
        *,
        code: str | None = None,
        details: dict[str, Any] | None = None,
        cause: Exception | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code or self.__class__.__name__
        self.details = details or {}
        self.cause = cause

    def __str__(self) -> str:
        if self.details:
            return f"{self.message} (code={self.code}) | {self.details}"
        return f"{self.message} (code={self.code})"


class SecurityError(JarvisError):
    """Raised for any security violation (sandbox, permissions, crypto)."""

    pass


class PermissionDeniedError(SecurityError):
    """Raised when a required permission is missing."""

    def __init__(self, permission: str, action: str = "") -> None:
        msg = f"Permission denied: {permission}"
        if action:
            msg += f" (action: {action})"
        super().__init__(msg, code="PERMISSION_DENIED")
        self.permission = permission


class SandboxError(SecurityError):
    """Raised by the execution sandbox."""

    pass


class AutomationError(JarvisError):
    """Raised for failures in the automation layer."""

    pass


class VoiceError(JarvisError):
    """Voice (STT/TTS) related errors."""

    pass


class VisionError(JarvisError):
    """Computer vision / OCR errors."""

    pass


class MemoryError(JarvisError):
    """Memory / vector database errors."""

    pass


class PluginError(JarvisError):
    """Plugin system errors."""

    pass


class ModelError(JarvisError):
    """Local AI model errors."""

    pass


# Re-export common ones for convenience
__all__ = [
    "JarvisError",
    "SecurityError",
    "PermissionDeniedError",
    "SandboxError",
    "AutomationError",
    "VoiceError",
    "VisionError",
    "MemoryError",
    "PluginError",
    "ModelError",
]
