"""
JARVIS OS - FastAPI Dependency Injection
========================================

Central place for reusable dependencies.

All dependencies here are designed to be:
- Easy to override in tests (using FastAPI's dependency_overrides)
- Type-safe
- Lazy where possible
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends

from core.config import get_settings, Settings
from core.security import (
    get_permission_manager,
    PermissionManager,
    get_audit_logger,
    AuditLogger,
)


def get_settings_dependency() -> Settings:
    """Dependency that returns the global validated Settings."""
    return get_settings()


def get_permission_manager_dependency() -> PermissionManager:
    """Dependency for the permission system."""
    return get_permission_manager()


def get_audit_logger_dependency() -> AuditLogger:
    """Dependency for audit logging."""
    return get_audit_logger()


# Type aliases for cleaner router signatures
SettingsDep = Annotated[Settings, Depends(get_settings_dependency)]
PermissionManagerDep = Annotated[PermissionManager, Depends(get_permission_manager_dependency)]
AuditLoggerDep = Annotated[AuditLogger, Depends(get_audit_logger_dependency)]


__all__ = [
    "get_settings_dependency",
    "get_permission_manager_dependency",
    "get_audit_logger_dependency",
    "SettingsDep",
    "PermissionManagerDep",
    "AuditLoggerDep",
]
