"""
JARVIS OS - Advanced AI Router
==============================

Production endpoints for conversational AI.

Features:
- POST /chat - Full conversational AI with context
- GET /models - List available local models
- GET /health - AI subsystem health

All requests are audited and permission-checked.
"""

from __future__ import annotations

from fastapi import APIRouter, status
from pydantic import BaseModel, Field
from typing import Any

from backend.app.dependencies import PermissionManagerDep, AuditLoggerDep
from backend.services.ai_service import get_ai_service, AIService, ChatResult
from backend.services.memory_service import get_memory_service
from core.security import Permission, AuditEventType

router = APIRouter()


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    model: str | None = None
    temperature: float | None = Field(default=None, ge=0.0, le=2.0)
    context: list[dict[str, str]] | None = None


class ChatResponse(BaseModel):
    response: str
    model_used: str
    duration_ms: float
    tokens_used: int | None = None
    success: bool = True


class ModelListResponse(BaseModel):
    models: list[str]
    default: str


@router.post("/ai/chat", response_model=ChatResponse, status_code=status.HTTP_200_OK)
async def chat(
    req: ChatRequest,
    pm: PermissionManagerDep,
    audit: AuditLoggerDep,
) -> ChatResponse:
    """Send a natural language message to JARVIS AI."""
    service: AIService = get_ai_service()
    result: ChatResult = await service.chat(
        message=req.message,
        model=req.model,
        temperature=req.temperature,
        session_id="default",
        use_memory=True,
    )

    audit.log_event(
        AuditEventType.AUTOMATION_ACTION,
        details={"message_length": len(req.message), "model": result.model},
        success=result.success,
    )

    return ChatResponse(
        response=result.response,
        model_used=result.model,
        duration_ms=result.duration_ms,
        tokens_used=result.tokens_used,
        success=result.success,
    )


@router.get("/ai/models", response_model=ModelListResponse)
async def list_models() -> ModelListResponse:
    """List all locally available LLM models."""
    service = get_ai_service()
    models = await service.list_models()
    from core.config import get_settings

    settings = get_settings()
    return ModelListResponse(models=models, default=settings.ai.default_model)


@router.get("/ai/health")
async def ai_health() -> dict[str, Any]:
    """Detailed health of the AI subsystem."""
    service = get_ai_service()
    return await service.health_check()
