"""
JARVIS OS - Browser Skills
==========================

One-command browser actions:
  - Open YouTube
  - Open Gmail
  - Open arbitrary URL
  - Web search
"""

from __future__ import annotations

import re
import webbrowser
from urllib.parse import quote_plus

from core.security import Permission
from .base import Skill, SkillContext, SkillResult


def _open(url: str, dry_run: bool = False) -> None:
    if not dry_run:
        # new=2 → new tab when possible
        webbrowser.open(url, new=2)


def _extract_url(text: str) -> str | None:
    m = re.search(r"https?://[^\s]+", text or "", re.I)
    if m:
        return m.group(0).rstrip(".,);]")
    # bare domains
    m = re.search(r"\b([a-z0-9-]+\.)+(com|org|net|io|ai|in|co|dev|app)\b", text or "", re.I)
    if m:
        return "https://" + m.group(0)
    return None


class OpenUrlSkill(Skill):
    name = "browser.open_url"
    description = "Open a URL in the default browser."
    permissions = [Permission.AUTOMATION_BROWSER]
    examples = [
        "open url",
        "open website",
        "go to github.com",
        "open https://example.com",
    ]

    async def run(self, ctx: SkillContext) -> SkillResult:
        url = ctx.params.get("url") or _extract_url(ctx.user_text)
        if not url:
            return SkillResult(
                success=False,
                message="I need a URL to open, sir.",
                skill=self.name,
                error="MISSING_URL",
            )
        if not url.startswith("http"):
            url = "https://" + url
        _open(url, dry_run=ctx.dry_run)
        return SkillResult(
            success=True,
            message=f"Opening {url}, sir.",
            skill=self.name,
            data={"url": url, "dry_run": ctx.dry_run},
        )


class OpenYouTubeSkill(Skill):
    name = "browser.open_youtube"
    description = "Open YouTube, optionally with a search query."
    permissions = [Permission.AUTOMATION_BROWSER]
    examples = [
        "open youtube",
        "open you tube",
        "youtube",
        "play on youtube",
        "search youtube for",
        "youtube search",
    ]

    def matches(self, text: str) -> float:
        t = (text or "").lower()
        if "youtube" in t or "you tube" in t:
            return 0.98
        return super().matches(text)

    async def run(self, ctx: SkillContext) -> SkillResult:
        text = ctx.user_text or ""
        query = ctx.params.get("query")
        if not query:
            m = re.search(
                r"(?:youtube|you tube)(?:\s+for|\s+search)?\s+(.+)$",
                text,
                re.I,
            )
            if m:
                query = m.group(1).strip(" .\"'")
            # "play X on youtube"
            m2 = re.search(r"play\s+(.+?)\s+on\s+youtube", text, re.I)
            if m2:
                query = m2.group(1).strip(" .\"'")
            m3 = re.search(r"search\s+(?:on\s+)?youtube\s+(?:for\s+)?(.+)$", text, re.I)
            if m3:
                query = m3.group(1).strip(" .\"'")

        if query:
            url = f"https://www.youtube.com/results?search_query={quote_plus(query)}"
            msg = f"Searching YouTube for {query}, sir."
        else:
            url = "https://www.youtube.com"
            msg = "Opening YouTube, sir."

        _open(url, dry_run=ctx.dry_run)
        return SkillResult(
            success=True,
            message=msg,
            skill=self.name,
            data={"url": url, "query": query},
        )


class OpenGmailSkill(Skill):
    name = "browser.open_gmail"
    description = "Open Gmail in the browser (compose later via email skill)."
    permissions = [Permission.AUTOMATION_BROWSER]
    examples = [
        "open gmail",
        "open email",
        "open mail",
        "check gmail",
        "open google mail",
    ]

    def matches(self, text: str) -> float:
        t = (text or "").lower()
        if any(k in t for k in ("gmail", "open mail", "open email", "check mail", "check email")):
            # Don't steal "send email" — that's a future email skill
            if re.search(r"\bsend\b", t):
                return 0.2
            return 0.96
        return super().matches(text)

    async def run(self, ctx: SkillContext) -> SkillResult:
        # compose deep-link if "compose" / "write" present
        text = (ctx.user_text or "").lower()
        if "compose" in text or "write" in text or "new mail" in text:
            url = "https://mail.google.com/mail/u/0/#inbox?compose=new"
            msg = "Opening Gmail compose, sir."
        else:
            url = "https://mail.google.com"
            msg = "Opening Gmail, sir."
        _open(url, dry_run=ctx.dry_run)
        return SkillResult(
            success=True,
            message=msg,
            skill=self.name,
            data={"url": url},
        )


class WebSearchSkill(Skill):
    name = "browser.search"
    description = "Search the web with the default browser."
    permissions = [Permission.AUTOMATION_BROWSER]
    examples = [
        "search for",
        "google",
        "search the web",
        "look up",
    ]

    def matches(self, text: str) -> float:
        t = (text or "").lower()
        if re.search(r"\b(search for|google|look up|search the web)\b", t):
            return 0.9
        return super().matches(text)

    async def run(self, ctx: SkillContext) -> SkillResult:
        text = ctx.user_text or ""
        query = ctx.params.get("query")
        if not query:
            m = re.search(
                r"(?:search(?:\s+the\s+web)?(?:\s+for)?|google|look up)\s+(.+)$",
                text,
                re.I,
            )
            query = m.group(1).strip() if m else text
        url = f"https://www.google.com/search?q={quote_plus(query)}"
        _open(url, dry_run=ctx.dry_run)
        return SkillResult(
            success=True,
            message=f"Searching the web for {query}, sir.",
            skill=self.name,
            data={"url": url, "query": query},
        )
