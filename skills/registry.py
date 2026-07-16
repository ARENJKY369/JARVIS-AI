"""
JARVIS OS - Skill Registry
==========================

Discovers and routes skills. Keeps orchestration simple and testable.
"""

from __future__ import annotations

from typing import Iterable

from loguru import logger

from core.security import get_permission_manager, Permission
from .base import Skill, SkillContext, SkillResult


class SkillRegistry:
    def __init__(self) -> None:
        self._skills: dict[str, Skill] = {}

    def register(self, skill: Skill) -> None:
        self._skills[skill.name] = skill
        logger.debug(f"Registered skill: {skill.name}")

    def register_many(self, skills: Iterable[Skill]) -> None:
        for s in skills:
            self.register(s)

    def get(self, name: str) -> Skill | None:
        return self._skills.get(name)

    def list_skills(self) -> list[Skill]:
        return list(self._skills.values())

    def catalog(self) -> list[dict]:
        return [s.to_tool_spec() for s in self._skills.values()]

    def match(self, text: str, *, threshold: float = 0.45) -> Skill | None:
        """Pick best skill by heuristic score."""
        best: Skill | None = None
        best_score = 0.0
        for skill in self._skills.values():
            score = skill.matches(text)
            if score > best_score:
                best_score = score
                best = skill
        if best and best_score >= threshold:
            return best
        return None

    async def execute(
        self,
        name: str,
        ctx: SkillContext,
        *,
        confirmed: bool = False,
    ) -> SkillResult:
        skill = self.get(name)
        if not skill:
            return SkillResult(
                success=False,
                message=f"Unknown skill '{name}'.",
                skill=name,
                error="NOT_FOUND",
            )

        pm = get_permission_manager()
        for perm in skill.permissions:
            if not pm.has_permission(perm):
                # Auto-grant safe browser/app opens in development for UX
                try:
                    from core.config import get_settings

                    if get_settings().environment == "development" and perm in (
                        Permission.AUTOMATION_BROWSER,
                        Permission.AUTOMATION_EXECUTE,
                        Permission.SHELL_COMMAND,
                        Permission.SYSTEM_INFO,
                        Permission.MEMORY_WRITE,
                        Permission.MEMORY_READ,
                        Permission.NETWORK_ACCESS,
                        Permission.FILE_WRITE,
                        Permission.FILE_READ,
                        Permission.VISION_CAPTURE,
                    ):
                        pm.grant(perm, reason="development skill auto-grant")
                    else:
                        return SkillResult(
                            success=False,
                            message=f"Permission denied: {perm.name}. Grant it in settings, sir.",
                            skill=skill.name,
                            error="PERMISSION_DENIED",
                        )
                except Exception:
                    return SkillResult(
                        success=False,
                        message=f"Permission denied: {perm.name}.",
                        skill=skill.name,
                        error="PERMISSION_DENIED",
                    )

        if skill.require_confirmation and not confirmed and not ctx.dry_run:
            return SkillResult(
                success=False,
                message=f"Confirm to run {skill.name}: {skill.description}",
                skill=skill.name,
                needs_confirmation=True,
                error="NEEDS_CONFIRMATION",
            )

        try:
            return await skill.run(ctx)
        except Exception as exc:
            logger.exception(f"Skill {skill.name} failed")
            return SkillResult(
                success=False,
                message=f"Skill failed: {exc}",
                skill=skill.name,
                error=str(exc),
            )


_registry: SkillRegistry | None = None


def get_skill_registry() -> SkillRegistry:
    """Singleton registry with built-in skills loaded once."""
    global _registry
    if _registry is None:
        _registry = SkillRegistry()
        _load_builtin_skills(_registry)
    return _registry


def _load_builtin_skills(reg: SkillRegistry) -> None:
    from .browser import OpenUrlSkill, OpenYouTubeSkill, OpenGmailSkill, WebSearchSkill
    from .apps import LaunchAppSkill
    from .system_info import SystemStatusSkill
    from .email_skill import EmailSkill, ConfirmEmailSkill, AddContactSkill
    from .everyday import (
        OpenSiteSkill,
        CalculateSkill,
        NoteSkill,
        TimerSkill,
        ClipboardSkill,
        ScreenshotSkill,
        SystemActionSkill,
        PlayMediaSkill,
        NavigateSkill,
        RememberSkill,
    )
    from .work_ai import AskChatGPTSkill, OpenChatGPTSkill
    from .smart_home_skill import SmartHomeSkill
    from .calendar_skill import CalendarSkill, ReminderSkill
    from .desktop_gui_skill import DesktopGUISkill
    from .vision_skill import VisionSkill

    reg.register_many(
        [
            # Work / AI research (high priority patterns)
            AskChatGPTSkill(),
            OpenChatGPTSkill(),
            # Browser / media
            OpenYouTubeSkill(),
            OpenGmailSkill(),
            OpenUrlSkill(),
            WebSearchSkill(),
            OpenSiteSkill(),
            PlayMediaSkill(),
            NavigateSkill(),
            # Apps / system
            LaunchAppSkill(),
            SystemStatusSkill(),
            SystemActionSkill(),
            # Email / contacts
            EmailSkill(),
            ConfirmEmailSkill(),
            AddContactSkill(),
            # Everyday utilities
            CalculateSkill(),
            NoteSkill(),
            TimerSkill(),
            ClipboardSkill(),
            ScreenshotSkill(),
            RememberSkill(),
            # Smart home / IoT
            SmartHomeSkill(),
            # Calendar / scheduling
            CalendarSkill(),
            ReminderSkill(),
            # Desktop GUI automation
            DesktopGUISkill(),
            # Vision / camera
            VisionSkill(),
        ]
    )


__all__ = ["SkillRegistry", "get_skill_registry"]
