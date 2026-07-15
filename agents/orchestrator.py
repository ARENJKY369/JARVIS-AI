"""
JARVIS OS - Agent Orchestrator (universal command router)
=========================================================

Anything the user says goes through here:
  1. Match a skill (browser, email, timer, note, play, …)
  2. Else conversational JARVIS personality (human butler)
  3. Always return a spoken-friendly reply
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from loguru import logger

from skills.base import SkillContext, SkillResult
from skills.registry import get_skill_registry, SkillRegistry
from core.security import get_audit_logger, AuditEventType
from agents.personality import style_skill_reply, conversational_reply


@dataclass
class OrchestratorResult:
    handled: bool
    skill: str | None
    reply: str
    skill_result: SkillResult | None = None
    intent: str = "chat"
    duration_ms: float = 0.0
    data: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "handled": self.handled,
            "skill": self.skill,
            "reply": self.reply,
            "intent": self.intent,
            "duration_ms": self.duration_ms,
            "data": self.data,
            "skill_result": self.skill_result.to_dict() if self.skill_result else None,
        }


class AgentOrchestrator:
    """Routes every natural-language command."""

    def __init__(self, registry: SkillRegistry | None = None) -> None:
        self.registry = registry or get_skill_registry()
        self.audit = get_audit_logger()

    async def handle(
        self,
        text: str,
        *,
        session_id: str = "default",
        confirmed: bool = False,
        dry_run: bool = False,
        force_skill: str | None = None,
        allow_chat_fallback: bool = True,
    ) -> OrchestratorResult:
        start = time.perf_counter()
        text = (text or "").strip()
        if not text:
            return OrchestratorResult(
                handled=True,
                skill=None,
                reply="I didn't quite catch that, sir. Try again when you're ready.",
                intent="none",
            )

        if text.lower().startswith("skill:"):
            force_skill = text.split(":", 1)[1].strip()
            text = force_skill

        skill = None
        if force_skill:
            skill = self.registry.get(force_skill)
        else:
            # Slightly lower threshold so more casual phrases map to skills
            skill = self.registry.match(text, threshold=0.42)

        if skill:
            ctx = SkillContext(
                user_text=text,
                session_id=session_id,
                dry_run=dry_run,
                params={"confirmed": confirmed} if confirmed else {},
            )
            result = await self.registry.execute(skill.name, ctx, confirmed=confirmed)
            self.audit.log_event(
                AuditEventType.AUTOMATION_ACTION,
                details={
                    "type": "skill_execute",
                    "skill": skill.name,
                    "success": result.success,
                    "text": text[:120],
                },
                success=result.success,
            )
            reply = style_skill_reply(result.message)
            if result.needs_confirmation:
                reply = f"{reply} Say 'confirm' when you want me to proceed, sir."

            return OrchestratorResult(
                handled=True,
                skill=skill.name,
                reply=reply,
                skill_result=result,
                intent=skill.name.split(".")[0],
                duration_ms=(time.perf_counter() - start) * 1000,
                data=result.data,
            )

        # No skill — full conversational JARVIS (always "handled")
        if allow_chat_fallback:
            try:
                from backend.services.ai_service import get_ai_service

                ai = get_ai_service()
                chat = await ai.chat(text, session_id=session_id, use_memory=True)
                reply = chat.response
            except Exception as exc:
                logger.warning(f"AI chat failed: {exc}")
                reply = conversational_reply(text)

            self.audit.log_event(
                AuditEventType.AUTOMATION_ACTION,
                details={"type": "chat", "text": text[:120]},
                success=True,
            )
            return OrchestratorResult(
                handled=True,
                skill="chat.jarvis",
                reply=reply,
                intent="chat",
                duration_ms=(time.perf_counter() - start) * 1000,
            )

        return OrchestratorResult(
            handled=False,
            skill=None,
            reply="",
            intent="chat",
            duration_ms=(time.perf_counter() - start) * 1000,
        )

    def list_capabilities(self) -> list[dict[str, Any]]:
        return self.registry.catalog()


_orchestrator: AgentOrchestrator | None = None


def get_orchestrator() -> AgentOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = AgentOrchestrator()
    return _orchestrator


__all__ = ["AgentOrchestrator", "OrchestratorResult", "get_orchestrator"]
