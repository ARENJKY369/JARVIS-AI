"""
JARVIS OS - Health Check Router
===============================

Lightweight health and readiness endpoints.

Used by:
- Electron shell
- Docker / monitoring
- Frontend status polling
"""

from fastapi import APIRouter, status
from pydantic import BaseModel

from core.config import get_settings

router = APIRouter()


class HealthResponse(BaseModel):
    status: str
    version: str
    environment: str
    offline: bool


@router.get("/health", response_model=HealthResponse, status_code=status.HTTP_200_OK)
async def health_check() -> HealthResponse:
    """Basic liveness probe."""
    settings = get_settings()
    return HealthResponse(
        status="healthy",
        version=settings.version,
        environment=settings.environment,
        offline=settings.is_offline_mode(),
    )


@router.get("/ready", status_code=status.HTTP_200_OK)
async def readiness_check() -> dict:
    """Readiness probe (can be extended with DB/LLM checks later)."""
    settings = get_settings()
    return {
        "status": "ready",
        "components": {
            "config": "ok",
            "security": "ok",
            "database": "pending",  # will be implemented in memory module
        },
    }
