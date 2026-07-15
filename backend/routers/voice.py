"""
JARVIS OS - Voice Router
========================

Production voice endpoints:

- POST /voice              — synthesize or transcribe
- POST /voice/speak        — TTS only (returns playable WAV base64)
- POST /voice/command      — full pipeline: text/audio → AI → spoken reply
- GET  /voice/status       — subsystem health
- GET  /voice/demo         — short audible demo clip

Audio is returned as base64 WAV so browsers can play it immediately via
``data:audio/wav;base64,...`` or the ``data_uri`` field.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import Response
from pydantic import BaseModel, Field
from typing import Literal, Any

from backend.app.dependencies import PermissionManagerDep, AuditLoggerDep
from backend.services.voice_service import get_voice_service
from core.security import Permission, AuditEventType

router = APIRouter()


class VoiceRequest(BaseModel):
    text: str | None = Field(None, max_length=2000)
    audio_base64: str | None = None
    action: Literal["synthesize", "transcribe"] = "synthesize"
    voice: str | None = Field(default="jarvis", description="Voice profile")


class VoiceResponse(BaseModel):
    text: str | None = None
    audio_base64: str | None = None
    data_uri: str | None = None
    duration_ms: float
    success: bool = True
    message: str | None = None
    engine: str | None = None


class SpeakRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=2000)
    voice: str | None = Field(default="jarvis")
    rate: float = Field(default=0.95, ge=0.5, le=2.0)


class CommandRequest(BaseModel):
    text: str | None = Field(None, max_length=2000, description="Typed or STT text")
    audio_base64: str | None = None
    speak: bool = Field(default=True, description="Synthesize spoken reply")
    voice: str | None = Field(default="jarvis")


class CommandResponse(BaseModel):
    transcript: str
    response_text: str
    audio_base64: str | None = None
    data_uri: str | None = None
    duration_ms: float
    intent: str
    success: bool = True
    message: str | None = None
    skill: str | None = None


@router.post("/voice", response_model=VoiceResponse)
async def voice_endpoint(
    req: VoiceRequest,
    pm: PermissionManagerDep,
    audit: AuditLoggerDep,
) -> VoiceResponse:
    """Synthesize speech or transcribe audio."""
    service = get_voice_service()
    await service.initialize()

    if req.action == "synthesize":
        if not req.text:
            raise HTTPException(status_code=400, detail="text is required for synthesize")

        result = service.synthesize(req.text, voice=req.voice)
        return VoiceResponse(
            text=req.text,
            audio_base64=result.audio_base64,
            data_uri=result.data_uri,
            duration_ms=result.duration_ms,
            success=result.success,
            message=result.message,
            engine=result.engine,
        )

    if req.action == "transcribe":
        if not req.audio_base64 and not req.text:
            raise HTTPException(
                status_code=400,
                detail="audio_base64 or text hint required for transcribe",
            )
        tr = service.transcribe(req.audio_base64, hint=req.text)
        return VoiceResponse(
            text=tr.text,
            audio_base64=None,
            data_uri=None,
            duration_ms=tr.duration_ms,
            success=tr.success,
            message=tr.message,
            engine=tr.engine,
        )

    return VoiceResponse(
        text=None,
        audio_base64=None,
        duration_ms=0,
        success=False,
        message="Unknown action",
    )


@router.post("/voice/speak", response_model=VoiceResponse)
async def speak(
    req: SpeakRequest,
    pm: PermissionManagerDep,
    audit: AuditLoggerDep,
) -> VoiceResponse:
    """Text-to-speech — returns real audible WAV audio (base64 + data URI)."""
    service = get_voice_service()
    result = service.synthesize(req.text, voice=req.voice, rate=req.rate)
    audit.log_event(
        AuditEventType.AUTOMATION_ACTION,
        details={"type": "voice_speak", "chars": len(req.text)},
    )
    return VoiceResponse(
        text=req.text,
        audio_base64=result.audio_base64,
        data_uri=result.data_uri,
        duration_ms=result.duration_ms,
        success=True,
        message=result.message,
        engine=result.engine,
    )


@router.post("/voice/speak.wav")
async def speak_wav(req: SpeakRequest, pm: PermissionManagerDep) -> Response:
    """TTS that streams raw WAV bytes (useful for <audio src=...> proxies)."""
    service = get_voice_service()
    result = service.synthesize(req.text, voice=req.voice, rate=req.rate)
    return Response(
        content=result.audio_bytes,
        media_type="audio/wav",
        headers={
            "Content-Disposition": 'inline; filename="jarvis.wav"',
            "X-Duration-Ms": str(int(result.duration_ms)),
            "X-Engine": result.engine,
        },
    )


@router.post("/voice/command", response_model=CommandResponse)
async def voice_command(
    req: CommandRequest,
    pm: PermissionManagerDep,
    audit: AuditLoggerDep,
) -> CommandResponse:
    """
    Full voice command loop: understand input → reason → speak reply.

    Provide either ``text`` (typed or from browser Web Speech API) or
    ``audio_base64``. Response includes playable audio when ``speak=true``.
    """
    if not req.text and not req.audio_base64:
        raise HTTPException(status_code=400, detail="text or audio_base64 required")

    service = get_voice_service()
    await service.initialize()
    result = await service.handle_command(
        text=req.text,
        audio_base64=req.audio_base64,
        speak=req.speak,
        voice=req.voice,
    )
    audit.log_event(
        AuditEventType.AUTOMATION_ACTION,
        details={
            "type": "voice_command",
            "intent": result.intent,
            "transcript_len": len(result.transcript),
        },
        success=result.success,
    )
    return CommandResponse(
        transcript=result.transcript,
        response_text=result.response_text,
        audio_base64=result.audio_base64,
        data_uri=result.data_uri,
        duration_ms=result.duration_ms,
        intent=result.intent,
        success=result.success,
        message=result.message,
        skill=getattr(result, "skill", None),
    )


@router.get("/voice/status")
async def voice_status() -> dict[str, Any]:
    """Voice subsystem status."""
    service = get_voice_service()
    await service.initialize()
    return service.health()


@router.get("/voice/voices")
async def list_voice_profiles() -> dict[str, Any]:
    """
    List selectable TTS voice profiles (male + female).

    Use the ``id`` field as ``voice`` on /voice/speak and /voice/command.
    """
    service = get_voice_service()
    voices = service.list_voices()
    from core.config import get_settings

    return {
        "default": get_settings().ui.default_voice or "jarvis",
        "count": len(voices),
        "voices": voices,
        "male": [v for v in voices if v["gender"] == "male"],
        "female": [v for v in voices if v["gender"] == "female"],
    }


@router.get("/voice/demo")
async def voice_demo() -> VoiceResponse:
    """
    Quick audible demo: 'Good evening, sir. JARVIS online.'

    Use this to verify speakers / browser audio playback.
    """
    service = get_voice_service()
    # Ensure speak permission is present (dev defaults already grant it)
    pm = None
    try:
        from core.security import get_permission_manager

        pm = get_permission_manager()
        if not pm.has_permission(Permission.VOICE_SPEAK):
            pm.grant(Permission.VOICE_SPEAK, reason="demo")
    except Exception:
        pass

    phrase = "Good evening, sir. JARVIS online. All primary systems nominal."
    result = service.synthesize(phrase, voice="jarvis")
    return VoiceResponse(
        text=phrase,
        audio_base64=result.audio_base64,
        data_uri=result.data_uri,
        duration_ms=result.duration_ms,
        success=True,
        message=(
            "Demo clip ready. Other voices: GET /api/v1/voice/voices "
            "then POST /voice/speak with voice=aria|nova|friday|deep|..."
        ),
        engine=result.engine,
    )
