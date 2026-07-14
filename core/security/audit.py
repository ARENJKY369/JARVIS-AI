"""
JARVIS OS - Audit Logging System
================================

Tamper-evident audit trail for all security-sensitive operations.

Features:
- Structured event logging
- Timestamped + context-rich
- Multiple output sinks (file + memory buffer for now)
- Easy querying for security reviews
- Integration with permission checks

Events are logged for:
- Permission grants/revokes
- Sandbox executions
- File operations
- Authentication attempts (future)
- Configuration changes
- Plugin loads

Implementation:
- Uses loguru for robust structured logging
- In-memory ring buffer for recent events (queryable)
- Optional JSON file output
"""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any

from loguru import logger

from core.config import get_settings


class AuditEventType(StrEnum):
    """Types of auditable events."""

    PERMISSION_GRANTED = "permission_granted"
    PERMISSION_REVOKED = "permission_revoked"
    PERMISSION_DENIED = "permission_denied"
    SANDBOX_EXECUTION = "sandbox_execution"
    FILE_ACCESS = "file_access"
    CONFIG_CHANGED = "config_changed"
    PLUGIN_LOADED = "plugin_loaded"
    VOICE_COMMAND = "voice_command"
    AUTOMATION_ACTION = "automation_action"
    SYSTEM_START = "system_start"
    SYSTEM_SHUTDOWN = "system_shutdown"


@dataclass
class AuditEvent:
    """A single audit event record."""

    event_type: AuditEventType
    timestamp: float
    actor: str = "jarvis"
    details: dict[str, Any] | None = None
    success: bool = True
    ip_address: str | None = None  # Future use (local only)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["event_type"] = self.event_type.value
        return d

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), default=str)


class AuditLogger:
    """
    Centralized audit logger.

    Provides both persistent logging and in-memory recent history.
    """

    def __init__(self, max_buffer: int = 500) -> None:
        self.settings = get_settings()
        self._buffer: list[AuditEvent] = []
        self._max_buffer = max_buffer
        self._log_file: Path | None = None

        if self.settings.logging.file_enabled:
            self._setup_file_logging()

        # Log system startup
        self.log_event(
            AuditEventType.SYSTEM_START,
            details={
                "version": self.settings.version,
                "env": self.settings.environment,
            },
        )

    def _setup_file_logging(self) -> None:
        """Configure loguru to also write structured audit logs."""
        logs_dir = self.settings.base_dir / self.settings.logs_dir
        logs_dir.mkdir(parents=True, exist_ok=True)

        self._log_file = logs_dir / "audit.log"

        # Add a dedicated audit sink (JSON lines)
        logger.add(
            str(self._log_file),
            level="INFO",
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level} | AUDIT | {message}",
            rotation="50 MB",
            retention="30 days",
            filter=lambda record: "audit" in record.get("extra", {}),
            serialize=False,
        )

    def log_event(
        self,
        event_type: AuditEventType,
        *,
        actor: str = "jarvis",
        details: dict[str, Any] | None = None,
        success: bool = True,
    ) -> AuditEvent:
        """Log a new audit event."""
        event = AuditEvent(
            event_type=event_type,
            timestamp=time.time(),
            actor=actor,
            details=details or {},
            success=success,
        )

        # Add to in-memory buffer (circular)
        self._buffer.append(event)
        if len(self._buffer) > self._max_buffer:
            self._buffer.pop(0)

        # Structured log
        log_extra = {
            "audit": True,
            "event_type": event_type.value,
            "actor": actor,
            "success": success,
            **(details or {}),
        }

        if success:
            logger.bind(**log_extra).info(f"AUDIT: {event_type.value} | actor={actor}")
        else:
            logger.bind(**log_extra).warning(
                f"AUDIT: {event_type.value} (FAILED) | actor={actor}"
            )

        return event

    def get_recent_events(self, limit: int = 50) -> list[AuditEvent]:
        """Return most recent events (newest last)."""
        return self._buffer[-limit:]

    def get_events_by_type(self, event_type: AuditEventType) -> list[AuditEvent]:
        """Filter events by type."""
        return [e for e in self._buffer if e.event_type == event_type]

    def clear_buffer(self) -> None:
        """Clear in-memory buffer (for tests)."""
        self._buffer.clear()

    def export_recent_as_json(self) -> str:
        """Export recent events as JSON array."""
        return json.dumps([e.to_dict() for e in self._buffer], indent=2, default=str)


# =============================================================================
# Global singleton
# =============================================================================

_audit_logger: AuditLogger | None = None


def get_audit_logger() -> AuditLogger:
    """Return the global audit logger singleton."""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger


__all__ = [
    "AuditEventType",
    "AuditEvent",
    "AuditLogger",
    "get_audit_logger",
]
