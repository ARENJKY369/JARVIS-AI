"""
JARVIS OS - Voice Router (Advanced)
===================================

Production stub for voice operations.

In the full system this will integrate:
- faster-whisper (STT)
- Piper TTS
- Real-time streaming

Current version:
- Accepts text-to-speech requests (returns placeholder audio)
- Accepts base64 audio for transcription (returns text)
- Full permission gating
- Returns realistic metadata
"""

from __future__ import annotations

from fastapi import APIRouter, status, HTTPException
from pydantic import BaseModel, Field
from typing import Literal

from backend.app.dependencies import PermissionManagerDep, AuditLoggerDep
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
    duration_ms: float
    success: bool = True
    message: str | None = None


@router.post("/voice", response_model=VoiceResponse)
async def voice_endpoint(
    req: VoiceRequest,
    pm: PermissionManagerDep,
    audit: AuditLoggerDep,
) -> VoiceResponse:
    """Advanced voice endpoint (STT + TTS stub)."""

    if req.action == "synthesize":
        if not req.text:
            raise HTTPException(400, "text is required for synthesize")

        # Permission check
        pm.require(Permission.VOICE_SPEAK)

        # In real system we would call Piper here
        # For now return a placeholder
        fake_audio = "UklGRiQAAABXQVZFZm10IBAAAAABAAEARKwAAIhYAQACABAAZGF0YQAAAAA="  # minimal wav header

        audit.log_event(
            AuditEventType.AUTOMATION_ACTION,
            details={"type": "voice_synthesize", "length": len(req.text)},
        )

        return VoiceResponse(
            text=req.text,
            audio_base64=fake_audio,
            duration_ms=len(req.text) * 45.0,  # rough estimate
            success=True,
            message="Voice synthesis completed (fallback mode)",
        )

    elif req.action == "transcribe":
        if not req.audio_base64:
            raise HTTPException(400, "audio_base64 is required for transcribe")

        pm.require(Permission.VOICE_LISTEN)

        # Real implementation would use faster-whisper
        transcribed = "Hello JARVIS. This is a simulated transcription in offline mode."

        audit.log_event(
            AuditEventType.AUTOMATION_ACTION,
            details={"type": "voice_transcribe"},
        )

        return VoiceResponse(
            text=transcribed,
            audio_base64=None,
            duration_ms=180.0,
            success=True,
            message="Transcription complete (fallback)",
        )

    return VoiceResponse(
        text=None,
        audio_base64=None,
        duration_ms=0,
        success=False,
        message="Unknown action",
    )


@router.get("/voice/status")
async def voice_status() -> dict:
    """Voice subsystem status."""
    return {
        "status": "operational",
        "mode": "fallback",
        "stt": "simulated",
        "tts": "simulated",
        "note": "Real Whisper + Piper will be enabled when models are installed",
    }
