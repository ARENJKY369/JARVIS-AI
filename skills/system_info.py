"""
JARVIS OS - System info skill (safe, read-only).
"""

from __future__ import annotations

import platform
import re
from datetime import datetime

from core.security import Permission
from .base import Skill, SkillContext, SkillResult


class SystemStatusSkill(Skill):
    name = "system.status"
    description = "Report basic system and JARVIS status."
    permissions = [Permission.SYSTEM_INFO]
    examples = [
        "system status",
        "status report",
        "diagnostics",
        "system report",
        "run diagnostics",
    ]

    def matches(self, text: str) -> float:
        t = (text or "").lower()
        # Don't steal pure social "how are you"
        if re.search(r"\bhow are you\b", t) and "status" not in t and "system" not in t:
            return 0.1
        if any(k in t for k in ("system status", "status report", "diagnostic", "system report")):
            return 0.9
        if re.search(r"\b(status|diagnostics)\b", t) and re.search(
            r"\b(system|core|full|run)\b", t
        ):
            return 0.88
        return super().matches(text)

    async def run(self, ctx: SkillContext) -> SkillResult:
        now = datetime.now().strftime("%H:%M")
        msg = (
            f"All systems nominal, sir. Host {platform.node()}, "
            f"{platform.system()} {platform.release()}. Local time {now}. "
            f"Voice and skill subsystems online."
        )
        return SkillResult(
            success=True,
            message=msg,
            skill=self.name,
            data={
                "host": platform.node(),
                "system": platform.system(),
                "time": now,
            },
        )
