"""
JARVIS OS - API Root Router
"""

from fastapi import APIRouter
from pydantic import BaseModel

from core.config import get_settings

router = APIRouter()


class APIRootResponse(BaseModel):
    name: str
    version: str
    status: str = "online"
    message: str = "JARVIS OS API is fully operational"
    endpoints: list[str]


@router.get("", response_model=APIRootResponse)
async def api_root():
    """Root of the API v1."""
    settings = get_settings()
    return APIRootResponse(
        name=settings.app_name,
        version=settings.version,
        endpoints=[
            "/health",
            "/ready",
            "/system/status",
            "/system/permissions",
            "/ai/chat",
            "/ai/models",
            "/voice",
        ],
    )
