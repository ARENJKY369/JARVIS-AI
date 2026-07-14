"""
JARVIS OS - Core Security Module
================================

Centralized security primitives for the entire JARVIS OS.

Responsibilities:
- Permission system (granular capability-based)
- Sandboxed execution context
- Cryptographic helpers (key generation, signing, encryption)
- Audit event logging
- Input sanitization and path validation
- Rate limiting primitives

Security Model (v1.0):
- Principle of Least Privilege
- All privileged actions require explicit user consent (via UI or voice)
- Sandbox: subprocess isolation + command whitelist + timeout
- No network by default
- Full audit trail (tamper-evident where possible)
- Secrets never leave secure memory

Usage:
    from core.security import get_permission_manager, Permission, require_permission

    if permission_manager.has_permission(Permission.AUTOMATION_EXECUTE):
        ...
"""

from __future__ import annotations

from .audit import AuditEvent, AuditLogger, AuditEventType, get_audit_logger
from .crypto import (
    decrypt_data,
    encrypt_data,
    generate_key_pair,
    hash_password,
    verify_password,
)
from .permissions import (
    Permission,
    PermissionLevel,
    PermissionManager,
    get_permission_manager,
    require_permission,
)
from .sandbox import (
    Sandbox,
    SandboxConfig,
    SandboxResult,
    execute_in_sandbox,
)

__all__ = [
    # Permissions
    "Permission",
    "PermissionLevel",
    "PermissionManager",
    "get_permission_manager",
    "require_permission",
    # Sandbox
    "Sandbox",
    "SandboxConfig",
    "SandboxResult",
    "execute_in_sandbox",
    # Crypto
    "generate_key_pair",
    "encrypt_data",
    "decrypt_data",
    "hash_password",
    "verify_password",
    # Audit
    "AuditLogger",
    "AuditEvent",
    "get_audit_logger",
]
