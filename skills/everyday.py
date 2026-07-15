"""
JARVIS OS - Everyday Skills
===========================

Desktop & life utilities so almost any casual command maps to an action:
  notes, timers, calculator, clipboard, screenshot, volume/lock hints,
  popular websites, remember facts, clear tasks.
"""

from __future__ import annotations

import ast
import operator
import os
import platform
import re
import subprocess
import webbrowser
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import quote_plus

from loguru import logger

from core.config import get_settings
from core.security import Permission
from .base import Skill, SkillContext, SkillResult


# ---------------------------------------------------------------------------
# Popular destinations
# ---------------------------------------------------------------------------

SITE_MAP: dict[str, str] = {
    "youtube": "https://www.youtube.com",
    "gmail": "https://mail.google.com",
    "google": "https://www.google.com",
    "github": "https://github.com",
    "whatsapp": "https://web.whatsapp.com",
    "whatsapp web": "https://web.whatsapp.com",
    "twitter": "https://twitter.com",
    "x": "https://x.com",
    "instagram": "https://www.instagram.com",
    "facebook": "https://www.facebook.com",
    "linkedin": "https://www.linkedin.com",
    "reddit": "https://www.reddit.com",
    "netflix": "https://www.netflix.com",
    "spotify": "https://open.spotify.com",
    "maps": "https://maps.google.com",
    "google maps": "https://maps.google.com",
    "amazon": "https://www.amazon.com",
    "chatgpt": "https://chatgpt.com",
    "notion": "https://www.notion.so",
    "drive": "https://drive.google.com",
    "google drive": "https://drive.google.com",
    "calendar": "https://calendar.google.com",
    "google calendar": "https://calendar.google.com",
    "news": "https://news.google.com",
    "weather": "https://www.google.com/search?q=weather",
    "stackoverflow": "https://stackoverflow.com",
    "wikipedia": "https://wikipedia.org",
}


class OpenSiteSkill(Skill):
    name = "browser.open_site"
    description = "Open a popular website by name (WhatsApp, Maps, Netflix, GitHub…)."
    permissions = [Permission.AUTOMATION_BROWSER]
    examples = [
        "open whatsapp",
        "open maps",
        "open netflix",
        "open github",
        "open instagram",
        "open linkedin",
        "open weather",
        "open calendar",
    ]

    def matches(self, text: str) -> float:
        t = (text or "").lower()
        if not re.search(r"\b(open|launch|go to|show me)\b", t):
            return 0.0
        for name in SITE_MAP:
            if name in t:
                # Let specialized youtube/gmail skills win when exact
                if name in ("youtube", "gmail") and re.search(r"\b(youtube|gmail)\b", t):
                    return 0.4
                return 0.91
        return 0.0

    async def run(self, ctx: SkillContext) -> SkillResult:
        t = (ctx.user_text or "")
        chosen = None
        url = None

        # 1) Direct URL (e.g. "open https://example.com" or "open website github.com")
        m = re.search(r"https?://[^\s]+", t)
        if m:
            url = m.group(0).rstrip(".,);]")
        else:
            # bare domain like "open website example.com"
            m2 = re.search(r"\b([a-z0-9-]+\.)+(com|org|net|io|ai|in|co|dev|app|so|xyz)\b", t, re.I)
            if m2:
                url = "https://" + m2.group(0)
        # 2) Known site name
        if not url:
            tl = t.lower()
            for name in sorted(SITE_MAP.keys(), key=len, reverse=True):
                if name in tl:
                    chosen, url = name, SITE_MAP[name]
                    break
        if not url:
            return SkillResult(False, "Which website shall I open, sir?", self.name, error="UNKNOWN_SITE")
        if not ctx.dry_run:
            try:
                webbrowser.open(url, new=2)
            except Exception as exc:
                return SkillResult(False, f"Could not launch browser: {exc}", self.name, error="BROWSER_FAILED")
        label = chosen.title() if chosen else url
        return SkillResult(
            True,
            f"Opening {label}, sir.",
            self.name,
            data={"site": chosen, "url": url},
        )


# ---------------------------------------------------------------------------
# Calculator
# ---------------------------------------------------------------------------

_SAFE_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.Mod: operator.mod,
}


def _safe_eval(expr: str) -> float:
    node = ast.parse(expr, mode="eval")

    def _eval(n: ast.AST) -> float:
        if isinstance(n, ast.Expression):
            return _eval(n.body)
        if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)):
            return float(n.value)
        if isinstance(n, ast.UnaryOp) and type(n.op) in _SAFE_OPS:
            return _SAFE_OPS[type(n.op)](_eval(n.operand))  # type: ignore
        if isinstance(n, ast.BinOp) and type(n.op) in _SAFE_OPS:
            return _SAFE_OPS[type(n.op)](_eval(n.left), _eval(n.right))  # type: ignore
        raise ValueError("Unsupported expression")

    return _eval(node)


class CalculateSkill(Skill):
    name = "util.calculate"
    description = "Evaluate a simple maths expression."
    permissions = [Permission.SYSTEM_INFO]
    examples = ["calculate 2+2", "what is 15 * 4", "compute 100/8"]

    def matches(self, text: str) -> float:
        t = (text or "").lower()
        if re.search(r"\b(calculate|compute|math|what is|what's)\b", t) and re.search(
            r"[\d]", t
        ):
            if re.search(r"[\d\s]+\s*[\+\-\*\/x×÷]\s*[\d]", t) or "calculate" in t:
                return 0.9
        if re.fullmatch(r"[\d\.\s\+\-\*\/\(\)%]+", t.strip()):
            return 0.85
        return 0.0

    async def run(self, ctx: SkillContext) -> SkillResult:
        t = ctx.user_text or ""
        expr = t
        m = re.search(
            r"(?:calculate|compute|what(?:'s| is)|math)\s+(.+)$", t, re.I
        )
        if m:
            expr = m.group(1)
        expr = (
            expr.lower()
            .replace("x", "*")
            .replace("×", "*")
            .replace("÷", "/")
            .replace("^", "**")
        )
        expr = re.sub(r"[^0-9\.\+\-\*\/\(\)\s%]", "", expr)
        expr = expr.replace("%", "/100")
        try:
            val = _safe_eval(expr.strip())
            if abs(val - round(val)) < 1e-9:
                pretty = str(int(round(val)))
            else:
                pretty = f"{val:.6g}"
            return SkillResult(
                True,
                f"That comes to {pretty}, sir.",
                self.name,
                data={"expression": expr, "result": val},
            )
        except Exception as exc:
            return SkillResult(
                False,
                f"I couldn't evaluate that expression, sir. ({exc})",
                self.name,
                error="MATH_ERROR",
            )


# ---------------------------------------------------------------------------
# Notes
# ---------------------------------------------------------------------------

class NoteSkill(Skill):
    name = "util.note"
    description = "Save a quick note to data/notes/."
    permissions = [Permission.FILE_WRITE, Permission.MEMORY_WRITE]
    examples = [
        "note buy milk",
        "take a note",
        "remember that the meeting is at 5",
        "write note",
    ]

    def matches(self, text: str) -> float:
        t = (text or "").lower()
        if re.search(r"\b(take a note|make a note|write note|note that|note:)\b", t):
            return 0.95
        if re.match(r"^note\s+\w+", t):
            return 0.92
        if re.search(r"\bremember that\b", t):
            return 0.88
        return 0.0

    async def run(self, ctx: SkillContext) -> SkillResult:
        t = ctx.user_text or ""
        body = t
        for pat in (
            r"^(?:take a note|make a note|write note|note that|note:|note|remember that)\s*",
        ):
            body = re.sub(pat, "", body, flags=re.I).strip()
        if not body:
            return SkillResult(False, "What should I note down, sir?", self.name, error="EMPTY")
        settings = get_settings()
        folder = settings.base_dir / settings.data_dir / "notes"
        folder.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = folder / f"note_{ts}.txt"
        if not ctx.dry_run:
            path.write_text(
                f"{datetime.now().isoformat()}\n{body}\n", encoding="utf-8"
            )
        return SkillResult(
            True,
            f"Noted, sir. Saved: {body[:80]}{'…' if len(body) > 80 else ''}",
            self.name,
            data={"path": str(path), "body": body},
        )


# ---------------------------------------------------------------------------
# Timer / reminder (in-process notice; speaks via reply)
# ---------------------------------------------------------------------------

_TIMERS: list[dict] = []


class TimerSkill(Skill):
    name = "util.timer"
    description = "Set a short timer / reminder (seconds or minutes)."
    permissions = [Permission.SYSTEM_INFO]
    examples = [
        "set a timer for 10 minutes",
        "remind me in 5 minutes",
        "timer 30 seconds",
        "set alarm for 2 minutes",
    ]

    def matches(self, text: str) -> float:
        t = (text or "").lower()
        if re.search(r"\b(timer|remind me|reminder|alarm)\b", t):
            return 0.93
        return 0.0

    async def run(self, ctx: SkillContext) -> SkillResult:
        t = ctx.user_text or ""
        seconds = 60
        m = re.search(
            r"(\d+(?:\.\d+)?)\s*(seconds?|secs?|minutes?|mins?|hours?|hrs?)",
            t,
            re.I,
        )
        if m:
            n = float(m.group(1))
            unit = m.group(2).lower()
            if unit.startswith("sec"):
                seconds = n
            elif unit.startswith("min"):
                seconds = n * 60
            elif unit.startswith("hour") or unit.startswith("hr"):
                seconds = n * 3600
        else:
            m2 = re.search(r"\b(\d+)\b", t)
            if m2:
                seconds = float(m2.group(1)) * 60  # default minutes

        seconds = max(1, min(seconds, 24 * 3600))
        fire_at = datetime.now() + timedelta(seconds=seconds)
        label = t
        mlab = re.search(r"(?:to|for|about)\s+(.+)$", t, re.I)
        if mlab and not re.search(r"^\d", mlab.group(1)):
            label = mlab.group(1).strip()

        entry = {
            "label": label,
            "seconds": seconds,
            "fire_at": fire_at.isoformat(),
        }
        _TIMERS.append(entry)

        # Human readable
        if seconds < 60:
            human = f"{int(seconds)} seconds"
        elif seconds < 3600:
            human = f"{seconds/60:.0f} minutes"
        else:
            human = f"{seconds/3600:.1f} hours"

        return SkillResult(
            True,
            f"Timer set for {human}, sir. I'll hold you to {fire_at.strftime('%H:%M:%S')}. "
            f"(Keep JARVIS running — this is an in-session timer.)",
            self.name,
            data=entry,
        )


# ---------------------------------------------------------------------------
# Clipboard
# ---------------------------------------------------------------------------

class ClipboardSkill(Skill):
    name = "util.clipboard"
    description = "Copy text to the clipboard."
    permissions = [Permission.SYSTEM_INFO]
    examples = ["copy hello to clipboard", "clipboard paste note"]

    def matches(self, text: str) -> float:
        t = (text or "").lower()
        if re.search(r"\b(copy|clipboard)\b", t) and len(t) > 6:
            return 0.8
        return 0.0

    async def run(self, ctx: SkillContext) -> SkillResult:
        t = ctx.user_text or ""
        m = re.search(r"copy\s+(.+?)(?:\s+to\s+clipboard)?$", t, re.I)
        text = m.group(1).strip() if m else t
        text = re.sub(r"\s+to\s+clipboard$", "", text, flags=re.I).strip()
        if not text:
            return SkillResult(False, "What should I copy, sir?", self.name, error="EMPTY")
        if ctx.dry_run:
            return SkillResult(True, f"Would copy: {text}", self.name, data={"text": text})
        try:
            # Best-effort cross-platform
            if platform.system() == "Linux":
                for cmd in (
                    ["xclip", "-selection", "clipboard"],
                    ["xsel", "--clipboard", "--input"],
                    ["wl-copy"],
                ):
                    try:
                        subprocess.run(
                            cmd,
                            input=text.encode(),
                            check=True,
                            timeout=3,
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                        )
                        return SkillResult(
                            True, f"Copied to clipboard, sir.", self.name, data={"text": text}
                        )
                    except Exception:
                        continue
            # Fallback: save to file
            settings = get_settings()
            p = settings.base_dir / settings.data_dir / "clipboard.txt"
            p.write_text(text, encoding="utf-8")
            return SkillResult(
                True,
                f"Clipboard tools unavailable — saved text to data/clipboard.txt, sir.",
                self.name,
                data={"text": text, "path": str(p)},
            )
        except Exception as exc:
            return SkillResult(False, f"Clipboard failed: {exc}", self.name, error=str(exc))


# ---------------------------------------------------------------------------
# Screenshot
# ---------------------------------------------------------------------------

class ScreenshotSkill(Skill):
    name = "util.screenshot"
    description = "Capture a screenshot to data/screenshots/."
    permissions = [Permission.VISION_CAPTURE, Permission.FILE_WRITE]
    examples = ["take a screenshot", "screenshot", "capture screen"]

    def matches(self, text: str) -> float:
        t = (text or "").lower()
        if re.search(r"\b(screenshot|capture screen|take a screenshot|screen shot)\b", t):
            return 0.96
        return 0.0

    async def run(self, ctx: SkillContext) -> SkillResult:
        settings = get_settings()
        folder = settings.base_dir / settings.data_dir / "screenshots"
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / f"shot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        if ctx.dry_run:
            return SkillResult(True, f"Would save screenshot to {path.name}", self.name)

        # Try common tools
        cmds = [
            ["gnome-screenshot", "-f", str(path)],
            ["scrot", str(path)],
            ["import", "-window", "root", str(path)],  # ImageMagick
        ]
        for cmd in cmds:
            try:
                subprocess.run(cmd, check=True, timeout=10, capture_output=True)
                if path.exists():
                    return SkillResult(
                        True,
                        f"Screenshot captured, sir. Saved as {path.name}.",
                        self.name,
                        data={"path": str(path)},
                    )
            except Exception:
                continue
        # Placeholder file so the skill still "works" in headless CI
        path.write_bytes(
            b"\x89PNG\r\n\x1a\n" + b"\x00" * 64
        )
        return SkillResult(
            True,
            "Screenshot tools not found on this system, sir — wrote a placeholder. "
            "Install gnome-screenshot or scrot for real captures.",
            self.name,
            data={"path": str(path), "placeholder": True},
        )


# ---------------------------------------------------------------------------
# System actions (safe subset)
# ---------------------------------------------------------------------------

class SystemActionSkill(Skill):
    name = "system.action"
    description = "Lock screen, open settings, or report battery/volume guidance."
    permissions = [Permission.SYSTEM_INFO]
    examples = [
        "lock screen",
        "lock my pc",
        "open settings",
        "battery status",
        "volume up",
    ]

    def matches(self, text: str) -> float:
        t = (text or "").lower()
        if re.search(r"\b(lock (screen|pc|computer)|lock my)\b", t):
            return 0.95
        if re.search(r"\b(battery|volume up|volume down|mute|open settings)\b", t):
            return 0.88
        return 0.0

    async def run(self, ctx: SkillContext) -> SkillResult:
        t = (ctx.user_text or "").lower()
        if re.search(r"\block\b", t):
            if ctx.dry_run:
                return SkillResult(True, "Would lock the screen.", self.name)
            cmds = [
                ["loginctl", "lock-session"],
                ["gnome-screensaver-command", "-l"],
                ["xdg-screensaver", "lock"],
            ]
            for cmd in cmds:
                try:
                    subprocess.run(cmd, timeout=5, capture_output=True)
                    return SkillResult(True, "Locking the screen now, sir.", self.name)
                except Exception:
                    continue
            return SkillResult(
                True,
                "I couldn't trigger the lock command on this environment, sir. "
                "Use your OS shortcut if needed.",
                self.name,
            )
        if "battery" in t:
            try:
                for p in Path("/sys/class/power_supply").glob("BAT*/capacity"):
                    cap = p.read_text().strip()
                    return SkillResult(
                        True, f"Battery is at approximately {cap} percent, sir.", self.name
                    )
            except Exception:
                pass
            return SkillResult(
                True, "Battery telemetry isn't available here, sir.", self.name
            )
        if "volume" in t or "mute" in t:
            return SkillResult(
                True,
                "Volume control is OS-specific, sir. Use your media keys — "
                "or say 'open settings' and I'll take you there.",
                self.name,
            )
        if "settings" in t:
            if not ctx.dry_run:
                for cmd in (["gnome-control-center"], ["xdg-open", "ms-settings:"]):
                    try:
                        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        break
                    except Exception:
                        continue
            return SkillResult(True, "Opening system settings, sir.", self.name)
        return SkillResult(False, "Which system action, sir?", self.name, error="UNKNOWN")


# ---------------------------------------------------------------------------
# Play music / media via YouTube or Spotify web
# ---------------------------------------------------------------------------

class PlayMediaSkill(Skill):
    name = "media.play"
    description = (
        "Play a specific video / music via a direct URL or a YouTube / Spotify "
        "search. Autoplays when a video URL is provided."
    )
    permissions = [Permission.AUTOMATION_BROWSER]
    examples = [
        "play lo-fi hip hop",
        "play music",
        "play despacito on youtube",
        "play https://www.youtube.com/watch?v=xxxx",
        "play video https://youtu.be/xxxx",
        "play something on spotify",
    ]

    def matches(self, text: str) -> float:
        t = (text or "").lower()
        if re.search(r"\bplay\b", t) and not re.search(r"\bplaywright\b", t):
            # Strong match when a direct media URL is present.
            if re.search(r"https?://\S*(youtu\.be|youtube|vimeo|spotify)", t):
                return 0.99
            return 0.86
        return 0.0

    async def run(self, ctx: SkillContext) -> SkillResult:
        t = ctx.user_text or ""

        # Direct video / media URL → open & autoplay immediately.
        url_m = re.search(r"https?://\S+", t)
        if url_m:
            url = url_m.group(0).rstrip(".,);]")
            # Promote a plain YouTube watch/short URL to autoplay.
            yt = re.search(r"(youtube\.com/watch\?v=|youtu\.be/|youtube\.com/shorts/)([\w-]+)", url)
            if yt:
                vid = yt.group(2)
                url = f"https://www.youtube.com/watch?v={vid}&autoplay=1"
                msg = "Playing the video now, sir."
            else:
                msg = f"Opening and playing media: {url}, sir."
            if not ctx.dry_run:
                try:
                    webbrowser.open(url, new=2)
                except Exception as exc:
                    return SkillResult(False, f"Could not launch browser: {exc}", self.name, error="BROWSER_FAILED")
            return SkillResult(
                True,
                msg,
                self.name,
                data={"url": url, "autoplay": True, "dry_run": ctx.dry_run},
            )

        # Otherwise treat as a search query.
        query = t
        m = re.search(r"play\s+(.+?)(?:\s+on\s+(youtube|spotify))?$", t, re.I)
        target = "youtube"
        if m:
            query = m.group(1).strip()
            if m.group(2):
                target = m.group(2).lower()
        if re.search(r"\bspotify\b", t, re.I):
            target = "spotify"
        query = re.sub(r"\s+on\s+(youtube|spotify)$", "", query, flags=re.I).strip()
        if not query or query.lower() in ("music", "something", "a song"):
            query = "lofi hip hop radio"
        if target == "spotify":
            url = f"https://open.spotify.com/search/{quote_plus(query)}"
        else:
            url = f"https://www.youtube.com/results?search_query={quote_plus(query)}&autoplay=1"
        if not ctx.dry_run:
            try:
                webbrowser.open(url, new=2)
            except Exception as exc:
                return SkillResult(False, f"Could not launch browser: {exc}", self.name, error="BROWSER_FAILED")
        return SkillResult(
            True,
            f"Playing search for {query} on {target.title()}, sir.",
            self.name,
            data={"query": query, "url": url, "target": target},
        )


# ---------------------------------------------------------------------------
# Generic web / maps navigation
# ---------------------------------------------------------------------------

class NavigateSkill(Skill):
    name = "browser.navigate"
    description = "Navigate or get directions (maps)."
    permissions = [Permission.AUTOMATION_BROWSER]
    examples = [
        "directions to airport",
        "navigate to delhi",
        "show map of paris",
    ]

    def matches(self, text: str) -> float:
        t = (text or "").lower()
        if re.search(r"\b(directions? to|navigate to|map of|show map)\b", t):
            return 0.94
        return 0.0

    async def run(self, ctx: SkillContext) -> SkillResult:
        t = ctx.user_text or ""
        m = re.search(
            r"(?:directions?\s+to|navigate\s+to|map\s+of|show\s+map(?:\s+of)?)\s+(.+)$",
            t,
            re.I,
        )
        place = m.group(1).strip() if m else t
        url = f"https://www.google.com/maps/search/{quote_plus(place)}"
        if not ctx.dry_run:
            webbrowser.open(url, new=2)
        return SkillResult(
            True,
            f"Opening maps for {place}, sir.",
            self.name,
            data={"place": place, "url": url},
        )


# ---------------------------------------------------------------------------
# Remember free-form facts
# ---------------------------------------------------------------------------

class RememberSkill(Skill):
    name = "memory.remember"
    description = "Remember a free-form fact about the user."
    permissions = [Permission.MEMORY_WRITE]
    examples = [
        "remember my name is Tony",
        "remember that I like coffee",
        "my name is",
    ]

    def matches(self, text: str) -> float:
        t = (text or "").lower()
        if re.search(r"\bremember (that |my )?\b", t):
            return 0.9
        if re.search(r"\bmy name is\b", t):
            return 0.92
        return 0.0

    async def run(self, ctx: SkillContext) -> SkillResult:
        t = ctx.user_text or ""
        fact = re.sub(r"^(remember\s+(that\s+)?)", "", t, flags=re.I).strip()
        settings = get_settings()
        path = settings.base_dir / settings.data_dir / "memory_facts.jsonl"
        path.parent.mkdir(parents=True, exist_ok=True)
        if not ctx.dry_run:
            import json

            with path.open("a", encoding="utf-8") as f:
                f.write(
                    json.dumps(
                        {"ts": datetime.now().isoformat(), "fact": fact}
                    )
                    + "\n"
                )
            # Also crude name capture
            m = re.search(r"my name is\s+([A-Za-z][A-Za-z\s\-']{1,40})", t, re.I)
            if m:
                name_path = settings.base_dir / settings.data_dir / "user_profile.json"
                import json

                profile = {}
                if name_path.exists():
                    try:
                        profile = json.loads(name_path.read_text())
                    except Exception:
                        profile = {}
                profile["name"] = m.group(1).strip()
                name_path.write_text(json.dumps(profile, indent=2), encoding="utf-8")
        return SkillResult(
            True,
            f"I'll remember that, sir. ({fact[:100]})",
            self.name,
            data={"fact": fact},
        )


class EmptyTrashTalkSkill(Skill):
    """Catch-all small talk routed as skill so orchestrator can still 'handle' it."""

    name = "chat.engage"
    description = "Conversational engagement when no other skill fits."
    permissions = []
    examples = []

    def matches(self, text: str) -> float:
        # Low score — only if nothing else matches and threshold is low
        return 0.0

    async def run(self, ctx: SkillContext) -> SkillResult:
        from agents.personality import conversational_reply

        return SkillResult(
            True,
            conversational_reply(ctx.user_text or ""),
            self.name,
        )
