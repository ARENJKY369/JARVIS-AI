"""
JARVIS OS - Skills API
======================

Expose one-command actions to the console / clients.

  GET  /skills           — catalog of available powers
  POST /skills/execute   — run a skill by name or free text
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Any

from backend.app.dependencies import AuditLoggerDep
from agents.orchestrator import get_orchestrator
from skills.base import SkillContext
from skills.registry import get_skill_registry
from core.security import AuditEventType

router = APIRouter()


class ExecuteRequest(BaseModel):
    text: str | None = Field(None, max_length=2000, description="Natural language command")
    skill: str | None = Field(None, description="Force a skill id, e.g. browser.open_youtube")
    params: dict[str, Any] = Field(default_factory=dict)
    confirmed: bool = False
    dry_run: bool = False
    speak: bool = Field(default=False, description="Also synthesize spoken reply")


class ExecuteResponse(BaseModel):
    handled: bool
    skill: str | None = None
    reply: str
    intent: str
    success: bool = True
    data: dict[str, Any] = Field(default_factory=dict)
    audio_base64: str | None = None
    data_uri: str | None = None
    duration_ms: float = 0.0
    needs_confirmation: bool = False


@router.get("/skills")
async def list_skills() -> dict[str, Any]:
    reg = get_skill_registry()
    return {
        "count": len(reg.list_skills()),
        "skills": reg.catalog(),
        "examples": [
            "Open YouTube",
            "Open YouTube search lo-fi hip hop",
            "Open Gmail",
            "Search for Iron Man trailer",
            "Open Chrome",
            "System status",
            "email test@example.com saying Hello from JARVIS",
            "add contact Mom email mom@gmail.com",
            "email Mom saying I'll be late",
            "send email to alice@example.com saying Project done",
            "confirm send email",
        ],
    }


@router.post("/skills/execute", response_model=ExecuteResponse)
async def execute_skill(
    req: ExecuteRequest,
    audit: AuditLoggerDep,
) -> ExecuteResponse:
    if not req.text and not req.skill:
        raise HTTPException(400, "Provide text or skill")

    orch = get_orchestrator()
    text = req.text or req.skill or ""

    if req.skill and req.params:
        # Direct skill invoke with params
        reg = get_skill_registry()
        ctx = SkillContext(user_text=text, params=req.params, dry_run=req.dry_run)
        result = await reg.execute(req.skill, ctx, confirmed=req.confirmed)
        handled = True
        reply = result.message
        skill_name = req.skill
        intent = req.skill.split(".")[0]
        success = result.success
        data = result.data
        needs = result.needs_confirmation
        duration = 0.0
    else:
        action = await orch.handle(
            text,
            confirmed=req.confirmed,
            dry_run=req.dry_run,
            force_skill=req.skill,
        )
        handled = action.handled
        reply = action.reply or (
            "I don't have a skill for that yet, sir. Try: open YouTube, open Gmail, system status."
            if not action.handled
            else action.reply
        )
        skill_name = action.skill
        intent = action.intent
        success = bool(action.skill_result.success) if action.skill_result else action.handled
        data = action.data
        needs = bool(action.skill_result.needs_confirmation) if action.skill_result else False
        duration = action.duration_ms

    audio_b64 = None
    data_uri = None
    if req.speak and reply:
        try:
            from backend.services.voice_service import get_voice_service

            speech = get_voice_service().synthesize(reply)
            audio_b64 = speech.audio_base64
            data_uri = speech.data_uri
        except Exception:
            pass

    audit.log_event(
        AuditEventType.AUTOMATION_ACTION,
        details={"type": "skills_api", "skill": skill_name, "text": text[:80]},
        success=success,
    )

    return ExecuteResponse(
        handled=handled,
        skill=skill_name,
        reply=reply,
        intent=intent,
        success=success,
        data=data,
        audio_base64=audio_b64,
        data_uri=data_uri,
        duration_ms=duration,
        needs_confirmation=needs,
    )
