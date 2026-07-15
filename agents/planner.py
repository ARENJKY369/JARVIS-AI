"""
JARVIS OS - Multi-step Mission Planner
======================================

Turns compound commands into ordered skill executions:

  "open youtube and email mom saying I'll be late"
  "search for iron man then open gmail"
  "set a timer for 5 minutes and note call the client"

Splits on connectors, runs each sub-command, returns a combined briefing.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from loguru import logger

from agents.orchestrator import AgentOrchestrator, OrchestratorResult, get_orchestrator
from agents.personality import style_skill_reply


# Ordered alternation: longer connectors first, bare "and" last.
_SPLITTERS = re.compile(
    r"\s+and then\s+|\s+after that\s+|\s+and also\s+|\s+then\s+|\s+also\s+|\s+plus\s+|,\s*and\s+|\s+&\s+|\s+and\s+",
    re.I,
)


@dataclass
class MissionStep:
    text: str
    skill: str | None
    reply: str
    success: bool
    data: dict[str, Any] = field(default_factory=dict)


@dataclass
class MissionResult:
    original: str
    steps: list[MissionStep]
    reply: str
    handled: bool = True
    multi: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "original": self.original,
            "multi": self.multi,
            "handled": self.handled,
            "reply": self.reply,
            "steps": [
                {
                    "text": s.text,
                    "skill": s.skill,
                    "reply": s.reply,
                    "success": s.success,
                    "data": s.data,
                }
                for s in self.steps
            ],
        }


def split_mission(text: str) -> list[str]:
    """Split a compound command into sub-missions."""
    t = (text or "").strip()
    if not t:
        return []
    if len(t) < 12:
        return [t]
    # Prefer strong connectors; only use bare "and" if both sides look like actions
    strong = re.compile(
        r"\s+and then\s+|\s+after that\s+|\s+and also\s+|\s+then\s+",
        re.I,
    )
    if strong.search(t):
        parts = strong.split(t)
    else:
        # Split on " and " only when both sides start with action verbs / known skills
        action_start = re.compile(
            r"^(open|launch|play|search|email|mail|ask|research|set|note|"
            r"calculate|compute|go|show|write|draft|help|take|copy|lock|"
            r"remember|google|navigate|directions)",
            re.I,
        )
        soft_parts = re.split(r"\s+and\s+", t, flags=re.I)
        if len(soft_parts) >= 2 and all(
            action_start.search(p.strip()) for p in soft_parts if p.strip()
        ):
            parts = soft_parts
        else:
            return [t]

    cleaned = [p.strip(" .,;") for p in parts if p and p.strip(" .,;")]
    cleaned = [c for c in cleaned if len(c) >= 3]
    if len(cleaned) <= 1:
        return [t]
    return cleaned[:4]


class MissionPlanner:
    """Execute multi-step natural language missions."""

    def __init__(self, orch: AgentOrchestrator | None = None) -> None:
        self.orch = orch or get_orchestrator()

    async def run(
        self,
        text: str,
        *,
        session_id: str = "default",
        dry_run: bool = False,
        confirmed: bool = False,
    ) -> MissionResult:
        parts = split_mission(text)
        multi = len(parts) > 1

        if not multi:
            single = await self.orch.handle(
                text,
                session_id=session_id,
                dry_run=dry_run,
                confirmed=confirmed,
                allow_chat_fallback=True,
            )
            step = MissionStep(
                text=text,
                skill=single.skill,
                reply=single.reply,
                success=True,
                data=single.data,
            )
            return MissionResult(
                original=text,
                steps=[step],
                reply=single.reply,
                handled=single.handled,
                multi=False,
            )

        steps: list[MissionStep] = []
        for part in parts:
            try:
                result = await self.orch.handle(
                    part,
                    session_id=session_id,
                    dry_run=dry_run,
                    confirmed=confirmed,
                    allow_chat_fallback=True,
                )
                steps.append(
                    MissionStep(
                        text=part,
                        skill=result.skill,
                        reply=result.reply,
                        success=bool(
                            result.skill_result.success
                            if result.skill_result is not None
                            else result.handled
                        ),
                        data=result.data,
                    )
                )
            except Exception as exc:
                logger.warning(f"Mission step failed ({part}): {exc}")
                steps.append(
                    MissionStep(
                        text=part,
                        skill=None,
                        reply=f"Step failed: {exc}",
                        success=False,
                    )
                )

        # Build Iron Man-style mission briefing
        n_ok = sum(1 for s in steps if s.success)
        lines = [f"Mission complete, sir. {n_ok}/{len(steps)} steps executed."]
        for i, s in enumerate(steps, 1):
            mark = "✓" if s.success else "✗"
            brief = s.reply.replace("\n", " ")
            if len(brief) > 100:
                brief = brief[:100] + "…"
            lines.append(f"{mark} Step {i}: {brief}")
        reply = " ".join(lines)
        # Soft style polish
        if not reply.lower().startswith(("mission", "certainly", "of course")):
            reply = style_skill_reply(reply)

        return MissionResult(
            original=text,
            steps=steps,
            reply=reply,
            handled=True,
            multi=True,
        )


_planner: MissionPlanner | None = None


def get_planner() -> MissionPlanner:
    global _planner
    if _planner is None:
        _planner = MissionPlanner()
    return _planner


__all__ = [
    "MissionPlanner",
    "MissionResult",
    "MissionStep",
    "split_mission",
    "get_planner",
]
