"""
JARVIS OS - Application Launch Skills
=====================================

Launch whitelisted desktop applications by friendly name.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

from core.security import Permission
from .base import Skill, SkillContext, SkillResult


# Friendly name → candidate binaries / commands (cross-platform-ish)
APP_MAP: dict[str, list[str]] = {
    "chrome": ["google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "chrome"],
    "firefox": ["firefox"],
    "code": ["code", "code-insiders"],
    "vscode": ["code", "code-insiders"],
    "vs code": ["code"],
    "terminal": ["x-terminal-emulator", "gnome-terminal", "konsole", "xterm", "wt"],
    "calculator": ["gnome-calculator", "kcalc", "calc", "gnome-calculator"],
    "notepad": ["notepad", "gedit", "kate", "mousepad", "notepad.exe"],
    "spotify": ["spotify"],
    "discord": ["discord"],
    "slack": ["slack"],
    "telegram": ["telegram-desktop", "telegram"],
    "vlc": ["vlc"],
    "files": ["nautilus", "dolphin", "thunar", "explorer"],
    "file manager": ["nautilus", "dolphin", "thunar"],
}


def _which(cmd: str) -> str | None:
    return shutil.which(cmd)


def _resolve_app(name: str) -> tuple[str, list[str]] | None:
    key = name.lower().strip()
    # direct key
    candidates = APP_MAP.get(key)
    if not candidates:
        # fuzzy: any key contained
        for k, v in APP_MAP.items():
            if k in key or key in k:
                candidates = v
                key = k
                break
    if not candidates:
        # treat as raw command if whitelisted-looking
        if re.match(r"^[a-zA-Z0-9_.-]+$", key) and _which(key):
            return key, [key]
        return None
    for c in candidates:
        path = _which(c)
        if path:
            return key, [path]
    # Windows: try start
    if sys.platform == "win32":
        return key, ["cmd", "/c", "start", "", key]
    return None


class LaunchAppSkill(Skill):
    name = "apps.launch"
    description = "Launch a whitelisted desktop application."
    permissions = [Permission.AUTOMATION_EXECUTE, Permission.SHELL_COMMAND]
    examples = [
        "open chrome",
        "open firefox",
        "open vs code",
        "open vscode",
        "launch terminal",
        "open calculator",
        "open spotify",
        "start discord",
    ]

    def matches(self, text: str) -> float:
        t = (text or "").lower()
        if re.search(r"\b(open|launch|start)\b", t):
            for name in APP_MAP:
                if name in t:
                    return 0.92
            # "open X" generic
            if re.search(r"\b(open|launch|start)\s+[a-z0-9]", t):
                return 0.55
        return super().matches(text)

    async def run(self, ctx: SkillContext) -> SkillResult:
        text = ctx.user_text or ""
        app = ctx.params.get("app")
        if not app:
            m = re.search(r"\b(?:open|launch|start)\s+(.+)$", text, re.I)
            app = (m.group(1) if m else text).strip(" .\"'")
            # strip trailing filler
            app = re.sub(r"\s+(please|now|for me)$", "", app, flags=re.I).strip()

        # Don't steal youtube/gmail (browser skills score higher usually)
        if re.search(r"youtube|gmail|http", app, re.I):
            return SkillResult(
                success=False,
                message="That looks like a browser action, not a local app.",
                skill=self.name,
                error="USE_BROWSER_SKILL",
            )

        resolved = _resolve_app(app)
        if not resolved:
            known = ", ".join(sorted(APP_MAP.keys())[:12])
            return SkillResult(
                success=False,
                message=f"I don't know how to open '{app}'. Known apps include: {known}.",
                skill=self.name,
                error="UNKNOWN_APP",
                data={"requested": app},
            )

        friendly, cmd = resolved
        if ctx.dry_run:
            return SkillResult(
                success=True,
                message=f"Would launch {friendly}.",
                skill=self.name,
                data={"app": friendly, "cmd": cmd, "dry_run": True},
            )

        try:
            subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
                cwd=str(Path.home()),
                env={**os.environ, "DISPLAY": os.environ.get("DISPLAY", ":0")},
            )
        except Exception as exc:
            return SkillResult(
                success=False,
                message=f"Failed to launch {friendly}: {exc}",
                skill=self.name,
                error=str(exc),
            )

        return SkillResult(
            success=True,
            message=f"Launching {friendly}, sir.",
            skill=self.name,
            data={"app": friendly, "cmd": cmd},
        )
