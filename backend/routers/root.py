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


class UIProfileResponse(BaseModel):
    app_name: str
    version: str
    operator_name: str
    operator_avatar: str
    jarvis_persona: str
    default_voice: str
    voices: list[dict]


@router.get("/ui/profile", response_model=UIProfileResponse, tags=["UI"])
async def ui_profile():
    """Operator + persona profile for the HUD console (custom name, avatar, voices)."""
    from voice.tts import list_voices

    settings = get_settings()
    return UIProfileResponse(
        app_name=settings.app_name,
        version=settings.version,
        operator_name=settings.ui.user_name or "Operator",
        operator_avatar=settings.ui.user_avatar or "",
        jarvis_persona=settings.ui.default_voice or "jarvis",
        default_voice=settings.ui.default_voice or "jarvis",
        voices=list_voices(),
    )
