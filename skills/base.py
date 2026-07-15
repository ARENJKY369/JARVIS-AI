"""
JARVIS OS - Skill Base Types
============================

Every automation power implements the Skill interface.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from core.security import Permission


@dataclass
class SkillContext:
    """Runtime context passed into every skill execution."""

    user_text: str = ""
    session_id: str = "default"
    dry_run: bool = False
    params: dict[str, Any] = field(default_factory=dict)


@dataclass
class SkillResult:
    """Standardized skill outcome (spoken + machine readable)."""

    success: bool
    message: str
    skill: str
    data: dict[str, Any] = field(default_factory=dict)
    needs_confirmation: bool = False
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "message": self.message,
            "skill": self.skill,
            "data": self.data,
            "needs_confirmation": self.needs_confirmation,
            "error": self.error,
        }


class Skill(ABC):
    """
    Abstract skill.

    Subclasses set:
      - name: unique id (e.g. "browser.open")
      - description: for LLM tool catalogs
      - permissions: required Permission enums
      - examples: natural phrases that should route here
    """

    name: str = "base"
    description: str = ""
    permissions: list[Permission] = []
    examples: list[str] = []
    # If True, orchestrator will ask user before running
    require_confirmation: bool = False

    @abstractmethod
    async def run(self, ctx: SkillContext) -> SkillResult:
        """Execute the skill."""

    def matches(self, text: str) -> float:
        """
        Cheap heuristic score 0..1 for routing without an LLM.
        Override for better matching; default uses examples/keywords.
        """
        t = (text or "").lower()
        if not t:
            return 0.0
        score = 0.0
        for ex in self.examples:
            ex_l = ex.lower()
            if ex_l in t or t in ex_l:
                score = max(score, 0.95)
            else:
                # token overlap
                et = set(ex_l.split())
                tt = set(t.split())
                if et and tt:
                    overlap = len(et & tt) / len(et)
                    score = max(score, overlap * 0.7)
        return min(1.0, score)

    def to_tool_spec(self) -> dict[str, Any]:
        """JSON schema-ish description for LLM tool calling."""
        return {
            "name": self.name,
            "description": self.description,
            "examples": self.examples,
            "permissions": [p.name for p in self.permissions],
            "require_confirmation": self.require_confirmation,
        }
