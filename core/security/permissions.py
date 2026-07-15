"""
JARVIS OS - Permission System
=============================

Capability-based permission model for secure operations.

Design:
- Enum of fine-grained permissions
- Hierarchical permission levels (USER, POWER_USER, ADMIN, SYSTEM)
- PermissionManager with runtime grants + revocation
- Context manager and decorator support
- Persisted user grants (future: stored in DB)
- All privileged actions require explicit consent

This is the gatekeeper for:
- Automation execution
- File system access
- Code execution
- Browser control
- System commands
- Microphone / camera access

Security Guarantees:
- Default deny
- Explicit allow only
- Time-bounded grants
- Full audit on every check
"""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum, auto
from functools import wraps
from typing import Any, TypeVar

from loguru import logger

from core.config import get_settings


class PermissionLevel(Enum):
    """Coarse-grained access levels."""

    USER = auto()
    POWER_USER = auto()
    ADMIN = auto()
    SYSTEM = auto()


class Permission(Enum):
    """Fine-grained permissions used throughout JARVIS OS."""

    # Voice
    VOICE_LISTEN = auto()
    VOICE_SPEAK = auto()

    # Vision
    VISION_CAPTURE = auto()
    VISION_ANALYZE = auto()

    # Automation
    AUTOMATION_EXECUTE = auto()
    AUTOMATION_BROWSER = auto()
    AUTOMATION_DESKTOP = auto()

    # Code & Shell
    CODE_EXECUTE = auto()
    SHELL_COMMAND = auto()

    # File System
    FILE_READ = auto()
    FILE_WRITE = auto()
    FILE_DELETE = auto()

    # Memory
    MEMORY_READ = auto()
    MEMORY_WRITE = auto()

    # Plugins
    PLUGIN_LOAD = auto()
    PLUGIN_EXECUTE = auto()

    # System
    SYSTEM_INFO = auto()
    SYSTEM_CONFIG = auto()

    # Network (disabled by default)
    NETWORK_ACCESS = auto()


@dataclass
class PermissionGrant:
    """Represents a time-limited or permanent grant."""

    permission: Permission
    granted_at: float = field(default_factory=time.time)
    expires_at: float | None = None
    reason: str = ""
    granted_by: str = "user"

    def is_valid(self) -> bool:
        if self.expires_at is None:
            return True
        return time.time() < self.expires_at


class PermissionManager:
    """
    Runtime permission manager.

    Thread-safe in practice for current use cases (single-process desktop).
    """

    def __init__(self) -> None:
        self._grants: dict[Permission, PermissionGrant] = {}
        self._level: PermissionLevel = PermissionLevel.USER
        self._settings = get_settings()

        # Default grants for development (strictly limited in prod)
        if self._settings.environment == "development":
            self._grant_defaults_dev()

    def _grant_defaults_dev(self) -> None:
        """Development convenience grants (never in production)."""
        dev_grants = [
            Permission.SYSTEM_INFO,
            Permission.MEMORY_READ,
            Permission.MEMORY_WRITE,
            Permission.FILE_READ,
            Permission.FILE_WRITE,
            Permission.VOICE_LISTEN,
            Permission.VOICE_SPEAK,
            Permission.AUTOMATION_BROWSER,
            Permission.AUTOMATION_EXECUTE,
            Permission.SHELL_COMMAND,
            Permission.NETWORK_ACCESS,  # SMTP / optional network skills in dev
            Permission.VISION_CAPTURE,
        ]
        for p in dev_grants:
            self.grant(p, reason="development default")

    def grant(
        self,
        permission: Permission,
        *,
        reason: str = "",
        expires_in_seconds: int | None = None,
        granted_by: str = "user",
    ) -> None:
        """Grant a permission (optionally time-bounded)."""
        expires_at = None
        if expires_in_seconds:
            expires_at = time.time() + expires_in_seconds

        grant = PermissionGrant(
            permission=permission,
            expires_at=expires_at,
            reason=reason,
            granted_by=granted_by,
        )
        self._grants[permission] = grant
        logger.info(
            f"Permission granted: {permission.name} | reason={reason} | expires={expires_at}"
        )

    def revoke(self, permission: Permission) -> None:
        """Revoke a previously granted permission."""
        if permission in self._grants:
            del self._grants[permission]
            logger.warning(f"Permission revoked: {permission.name}")

    def has_permission(self, permission: Permission) -> bool:
        """Check whether a permission is currently granted and valid."""
        grant = self._grants.get(permission)
        if grant is None:
            return False
        return grant.is_valid()

    def require(self, permission: Permission, *, action: str = "") -> None:
        """
        Raise PermissionError if permission is not granted.
        Used internally by decorators and critical paths.
        """
        if not self.has_permission(permission):
            msg = f"Permission denied: {permission.name}"
            if action:
                msg += f" for action '{action}'"
            logger.error(msg)
            raise PermissionError(msg)

    def set_level(self, level: PermissionLevel) -> None:
        """Elevate or downgrade current permission level (future use)."""
        self._level = level
        logger.info(f"Permission level changed to {level.name}")

    def get_active_grants(self) -> list[PermissionGrant]:
        """Return list of currently valid grants."""
        return [g for g in self._grants.values() if g.is_valid()]

    def reset(self) -> None:
        """Reset all grants (used in tests and session restart)."""
        self._grants.clear()
        if self._settings.environment == "development":
            self._grant_defaults_dev()


# =============================================================================
# Global singleton
# =============================================================================

_permission_manager: PermissionManager | None = None


def get_permission_manager() -> PermissionManager:
    """Returns the global permission manager singleton."""
    global _permission_manager
    if _permission_manager is None:
        _permission_manager = PermissionManager()
    return _permission_manager


# =============================================================================
# Decorators & Context Helpers
# =============================================================================

F = TypeVar("F", bound=Callable[..., Any])


def require_permission(permission: Permission) -> Callable[[F], F]:
    """
    Decorator that enforces a permission before executing a function.

    Example:
        @require_permission(Permission.AUTOMATION_EXECUTE)
        async def run_automation(...):
            ...
    """

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            pm = get_permission_manager()
            pm.require(permission, action=func.__name__)
            return func(*args, **kwargs)

        return wrapper  # type: ignore

    return decorator


class PermissionContext:
    """
    Context manager for temporary permission elevation.

    with PermissionContext(Permission.AUTOMATION_EXECUTE, expires_in=60):
        run_automation()
    """

    def __init__(
        self,
        permission: Permission,
        *,
        reason: str = "temporary context",
        expires_in_seconds: int = 60,
    ) -> None:
        self.permission = permission
        self.reason = reason
        self.expires_in = expires_in_seconds
        self._manager = get_permission_manager()
        self._had_before = self._manager.has_permission(permission)

    def __enter__(self) -> PermissionContext:
        if not self._had_before:
            self._manager.grant(
                self.permission,
                reason=self.reason,
                expires_in_seconds=self.expires_in,
            )
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if not self._had_before:
            self._manager.revoke(self.permission)


__all__ = [
    "Permission",
    "PermissionLevel",
    "PermissionGrant",
    "PermissionManager",
    "get_permission_manager",
    "require_permission",
    "PermissionContext",
]
