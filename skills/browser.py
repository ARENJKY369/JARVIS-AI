"""
JARVIS OS - Browser Skills (v2 - video play + website open from website + ChatGPT auto-send)
"""

from __future__ import annotations

import re
import webbrowser
from urllib.parse import quote_plus

from core.security import Permission
from .base import Skill, SkillContext, SkillResult


def _open(url: str, dry_run: bool = False) -> None:
    if not dry_run:
        webbrowser.open(url, new=2)


def _extract_url(text: str) -> str | None:
    m = re.search(r"https?://[^\s]+", text or "", re.I)
    if m:
        return m.group(0).rstrip(".,);]")
    m = re.search(r"\b([a-z0-9-]+\.)+(com|org|net|io|ai|in|co|dev|app|tv|me|app|gov|edu)\b", text or "", re.I)
    if m:
        return "https://" + m.group(0)
    return None


class OpenUrlSkill(Skill):
    name = "browser.open_url"
    description = "Open any URL or website from the website (e.g., open github.com). Frontend opens new tab + preview."
    permissions = [Permission.AUTOMATION_BROWSER]
    examples = [
        "open url",
        "open website",
        "open website from website",
        "go to github.com",
        "open https://example.com",
        "open github",
        "open site",
        "visit",
    ]

    def matches(self, text: str) -> float:
        t = (text or "").lower()
        # Don't steal email / contact skills
        if re.search(r"[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}", t):
            # If it's an email command, let email skill win
            if re.search(r"\b(email|mail|contact|send)\b", t):
                return 0.05
        if re.search(r"\b(add contact|save contact)\b", t):
            return 0.05
        if _extract_url(t):
            # If URL is inside an email command, lower score
            if re.search(r"\bemail\b", t) and "@" in t:
                return 0.2
            return 0.97
        if re.search(r"\b(open|launch|go to|visit|browse to)\b", t) and re.search(r"\b(website|site|url|page|link)\b", t):
            return 0.92
        if re.search(r"\b(open|go to|visit)\s+[a-z0-9-]+\.(com|org|net|io|ai|in|co|dev|app|tv|me)\b", t):
            return 0.96
        return super().matches(text)

    async def run(self, ctx: SkillContext) -> SkillResult:
        url = ctx.params.get("url") or _extract_url(ctx.user_text or "")
        if not url:
            mm = re.search(r"(?:open|go to|visit)\s+([a-z0-9-]+\.[a-z]{2,}(?:/[^\s]*)?)", ctx.user_text or "", re.I)
            if mm:
                url = "https://" + mm.group(1)
        if not url:
            if re.search(r"\bopen website\b", ctx.user_text or "", re.I):
                return SkillResult(
                    success=False,
                    message="Which website shall I open, sir? Try 'open github.com' or 'open youtube.com'.",
                    skill=self.name,
                    error="MISSING_URL",
                )
            return SkillResult(
                success=False,
                message="I need a URL to open, sir. Try 'open github.com' or paste a link.",
                skill=self.name,
                error="MISSING_URL",
            )
        if not url.startswith("http"):
            url = "https://" + url
        _open(url, dry_run=ctx.dry_run)
        return SkillResult(
            success=True,
            message=f"Opening {url} - new tab + preview active, sir.",
            skill=self.name,
            data={"url": url, "dry_run": ctx.dry_run, "type": "website", "action": "open_website"},
        )


class OpenYouTubeSkill(Skill):
    name = "browser.open_youtube"
    description = "Open YouTube or play a video - embeds video + opens new tab. Supports 'play X on youtube', 'play video'."
    permissions = [Permission.AUTOMATION_BROWSER]
    examples = [
        "open youtube",
        "open you tube",
        "youtube",
        "play on youtube",
        "search youtube for",
        "youtube search",
        "play video",
        "play youtube video",
        "play lo-fi on youtube",
        "watch",
    ]

    def matches(self, text: str) -> float:
        t = (text or "").lower()
        if "youtube" in t or "you tube" in t:
            return 0.98
        if re.search(r"\b(play|watch)\s+.*\b(video|music|song)\b", t):
            return 0.72
        return super().matches(text)

    async def run(self, ctx: SkillContext) -> SkillResult:
        text = ctx.user_text or ""
        query = ctx.params.get("query")
        if not query:
            m = re.search(r"(?:youtube|you tube)(?:\s+for|\s+search)?\s+(.+)$", text, re.I)
            if m:
                query = m.group(1).strip(" .\"'")
            m2 = re.search(r"play\s+(.+?)\s+on\s+youtube", text, re.I)
            if m2:
                query = m2.group(1).strip(" .\"'")
            m3 = re.search(r"search\s+(?:on\s+)?youtube\s+(?:for\s+)?(.+)$", text, re.I)
            if m3:
                query = m3.group(1).strip(" .\"'")

        if query:
            url = f"https://www.youtube.com/results?search_query={quote_plus(query)}"
            msg = f"Playing video search for {query} on YouTube - embed + new tab opened, sir."
        else:
            url = "https://www.youtube.com"
            msg = "Opening YouTube - video player ready, sir."

        _open(url, dry_run=ctx.dry_run)
        return SkillResult(
            success=True,
            message=msg,
            skill=self.name,
            data={
                "url": url,
                "query": query,
                "type": "youtube",
                "action": "play_video",
                "embed": f"https://www.youtube.com/embed?listType=search&list={quote_plus(query or '')}",
            },
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
            if re.search(r"\bsend\b", t):
                return 0.2
            return 0.96
        return super().matches(text)

    async def run(self, ctx: SkillContext) -> SkillResult:
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
            data={"url": url, "type": "website"},
        )


class WebSearchSkill(Skill):
    name = "browser.search"
    description = "Search the web with the default browser. Opens search + preview."
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
            message=f"Searching the web for {query} - opened + preview, sir.",
            skill=self.name,
            data={"url": url, "query": query, "type": "website"},
        )
