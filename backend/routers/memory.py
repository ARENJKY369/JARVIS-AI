"""
JARVIS OS - Advanced Memory Router
==================================

Endpoints for long-term memory operations.

This is the foundation for semantic recall.
"""

from fastapi import APIRouter, status
from pydantic import BaseModel, Field

from backend.app.dependencies import PermissionManagerDep, AuditLoggerDep
from backend.services.memory_service import get_memory_service
from core.security import AuditEventType

router = APIRouter()


class StoreMemoryRequest(BaseModel):
    user_id: str = "default"
    content: str = Field(..., min_length=3, max_length=2000)
    metadata: dict | None = None


class RecallRequest(BaseModel):
    user_id: str = "default"
    query: str = ""
    limit: int = Field(5, ge=1, le=20)


class MemoryEntryResponse(BaseModel):
    id: str
    content: str
    timestamp: float
    metadata: dict


@router.post("/memory/store", status_code=status.HTTP_201_CREATED)
async def store_memory(
    req: StoreMemoryRequest,
    pm: PermissionManagerDep,
    audit: AuditLoggerDep,
):
    mem = get_memory_service()
    entry_id = mem.store(req.user_id, req.content, req.metadata)
    audit.log_event(AuditEventType.AUTOMATION_ACTION, details={"memory": "store"})
    return {"id": entry_id, "status": "stored"}


@router.post("/memory/recall", response_model=list[MemoryEntryResponse])
async def recall_memory(
    req: RecallRequest,
    pm: PermissionManagerDep,
):
    mem = get_memory_service()
    entries = mem.recall(req.user_id, req.query, req.limit)
    return [
        MemoryEntryResponse(
            id=e.id,
            content=e.content,
            timestamp=e.timestamp,
            metadata=e.metadata,
        )
        for e in entries
    ]


@router.get("/memory/status")
async def memory_status():
    mem = get_memory_service()
    return {
        "status": "operational",
        "mode": "in_memory_advanced",
        "sessions": len(mem._store),
    }
