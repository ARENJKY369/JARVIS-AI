"""
JARVIS OS - System Router
=========================

Endpoints for system introspection, permissions, and status.

All endpoints here are security-sensitive and require appropriate permissions.
"""

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel

from core.security import Permission, get_permission_manager, PermissionManager
from core.security.audit import get_audit_logger, AuditLogger, AuditEventType

from backend.app.dependencies import PermissionManagerDep, AuditLoggerDep

router = APIRouter()


class SystemStatus(BaseModel):
    app_name: str
    version: str
    environment: str
    offline: bool
    permissions_granted: list[str]


class PermissionStatus(BaseModel):
    permission: str
    granted: bool


class AuditEventResponse(BaseModel):
    event_type: str
    timestamp: float
    actor: str
    success: bool
    details: dict | None = None


@router.get("/system/status", response_model=SystemStatus)
async def get_system_status(
    pm: PermissionManagerDep,
) -> SystemStatus:
    """Return high-level system status and active permissions."""
    from core.config import get_settings

    settings = get_settings()
    active = [p.permission.name for p in pm.get_active_grants()]

    return SystemStatus(
        app_name=settings.app_name,
        version=settings.version,
        environment=settings.environment,
        offline=settings.is_offline_mode(),
        permissions_granted=active,
    )


@router.get("/system/permissions", response_model=list[PermissionStatus])
async def list_permissions(
    pm: PermissionManagerDep,
) -> list[PermissionStatus]:
    """List all defined permissions and current grant status."""
    results = []
    for perm in Permission:
        results.append(
            PermissionStatus(
                permission=perm.name,
                granted=pm.has_permission(perm),
            )
        )
    return results


@router.post("/system/permissions/grant", status_code=status.HTTP_200_OK)
async def grant_permission(
    permission: str,
    pm: PermissionManagerDep,
    audit: AuditLoggerDep,
) -> dict:
    """Grant a permission (for demo / UI use). In production this would require user consent flow."""
    try:
        perm = Permission[permission]
    except KeyError:
        return {"error": "UNKNOWN_PERMISSION", "message": f"Permission {permission} does not exist"}

    if not pm.has_permission(perm):
        pm.grant(perm, reason="API grant request")

    audit.log_event(
        AuditEventType.PERMISSION_GRANTED,
        details={"permission": permission, "source": "api"},
    )

    return {"status": "granted", "permission": permission}


@router.get("/system/audit", response_model=list[AuditEventResponse])
async def get_recent_audit(
    audit: AuditLoggerDep,
    limit: int = 20,
) -> list[AuditEventResponse]:
    """Return recent audit events (for debugging and security review)."""
    events = audit.get_recent_events(limit=limit)
    return [
        AuditEventResponse(
            event_type=e.event_type.value,
            timestamp=e.timestamp,
            actor=e.actor,
            success=e.success,
            details=e.details,
        )
        for e in events
    ]
