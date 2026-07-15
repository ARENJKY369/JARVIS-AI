"""
JARVIS OS - Work / Research AI Skills
=====================================

Let you offload work to AI tools with one command:

  "ask chatgpt about quantum computing"
  "ask chatgpt how to write a resignation email"
  "research climate change"
  "explain recursion"
  "summarize this: <paste text>"
  "help me write a cover letter for Google"
  "google how to fix python import error"

Strategy:
  1. Prefer local Ollama (JARVIS brain) for a spoken answer when available
  2. Always open ChatGPT / Gemini / Claude / Perplexity / Google with the
     query prefilled so you can continue the deep work in the browser
  3. Copy the prompt to clipboard / save a work note for convenience
"""

from __future__ import annotations

import re
import webbrowser
from datetime import datetime
from pathlib import Path
from urllib.parse import quote, quote_plus

from loguru import logger

from core.config import get_settings
from core.security import Permission
from .base import Skill, SkillContext, SkillResult


# Providers we can open in the browser
_PROVIDERS: dict[str, str] = {
    "chatgpt": "https://chatgpt.com/?q={q}",
    "chat gpt": "https://chatgpt.com/?q={q}",
    "gpt": "https://chatgpt.com/?q={q}",
    "openai": "https://chatgpt.com/?q={q}",
    "gemini": "https://gemini.google.com/app?q={q}",
    "bard": "https://gemini.google.com/app?q={q}",
    "claude": "https://claude.ai/new?q={q}",
    "perplexity": "https://www.perplexity.ai/search?q={q}",
    "google": "https://www.google.com/search?q={q}",
}


def _extract_query(text: str) -> tuple[str, str]:
    """
    Return (provider, query).
    provider defaults to chatgpt for 'ask/research/explain' style commands.
    """
    t = (text or "").strip()
    low = t.lower()

    # Explicit provider
    for name in sorted(_PROVIDERS.keys(), key=len, reverse=True):
        # "ask chatgpt about X" / "ask chatgpt X" / "open chatgpt and ask X"
        pat = rf"\b(?:ask|query|use|open)\s+{re.escape(name)}\b(?:\s+(?:about|for|to|on|regarding))?\s*(.+)$"
        m = re.search(pat, t, re.I)
        if m and m.group(1).strip():
            return name if name != "chat gpt" else "chatgpt", m.group(1).strip()

        # "chatgpt: question" / "chatgpt - question"
        pat2 = rf"\b{re.escape(name)}\s*[:\-–]\s*(.+)$"
        m2 = re.search(pat2, t, re.I)
        if m2 and m2.group(1).strip():
            return name if name != "chat gpt" else "chatgpt", m2.group(1).strip()

    # "research X" / "look up X" / "find out about X"
    m = re.search(
        r"\b(?:research|look\s*up|find\s+out\s+about|investigate)\s+(.+)$",
        t,
        re.I,
    )
    if m:
        return "chatgpt", m.group(1).strip()

    # "explain X" / "what is X" / "how do I X" / "how to X"
    m = re.search(
        r"\b(?:explain|define|what\s+is|what's|how\s+do\s+i|how\s+to|help\s+me\s+(?:with|write|draft|create|understand))\s+(.+)$",
        t,
        re.I,
    )
    if m:
        return "chatgpt", m.group(1).strip()

    # "summarize this: ..." / "summarise ..."
    m = re.search(r"\bsummari[sz]e(?:\s+this)?\s*[:\-]?\s*(.+)$", t, re.I)
    if m:
        return "chatgpt", f"Please summarize the following clearly:\n\n{m.group(1).strip()}"

    # "write a/an ..." / "draft a ..."
    m = re.search(r"\b(?:write|draft|compose)\s+(?:a|an|the|my)?\s*(.+)$", t, re.I)
    if m and not re.search(r"\b(email|mail|note)\b", low):
        return "chatgpt", f"Please write {m.group(1).strip()}"

    # "ask about X" without provider
    m = re.search(r"\bask(?:\s+about)?\s+(.+)$", t, re.I)
    if m:
        return "chatgpt", m.group(1).strip()

    # "google X" already handled somewhat by search skill — but catch here too
    m = re.search(r"\bgoogle\s+(.+)$", t, re.I)
    if m:
        return "google", m.group(1).strip()

    return "chatgpt", t


def _open_provider(provider: str, query: str, dry_run: bool = False) -> str:
    key = provider.lower().strip()
    if key == "chat gpt":
        key = "chatgpt"
    template = _PROVIDERS.get(key, _PROVIDERS["chatgpt"])
    url = template.format(q=quote_plus(query))
    if not dry_run:
        try:
            webbrowser.open(url, new=2)
        except Exception as exc:
            logger.warning(f"Browser open failed: {exc}")
    return url


def _save_work_prompt(query: str, provider: str, answer: str | None = None) -> Path:
    settings = get_settings()
    folder = settings.base_dir / settings.data_dir / "work_prompts"
    folder.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = folder / f"ask_{ts}.txt"
    body = (
        f"Time: {datetime.now().isoformat()}\n"
        f"Provider: {provider}\n"
        f"Query:\n{query}\n"
    )
    if answer:
        body += f"\n--- Local JARVIS answer ---\n{answer}\n"
    path.write_text(body, encoding="utf-8")
    return path


class AskChatGPTSkill(Skill):
    """
    One command: ask ChatGPT (or Gemini/Claude/Perplexity) about anything.

    Opens the AI site with your question and optionally answers locally first.
    """

    name = "work.ask_ai"
    description = (
        "Ask ChatGPT / Gemini / Claude / Perplexity about any work topic. "
        "Opens the tool with your question prefilled; also answers locally if Ollama is available."
    )
    permissions = [Permission.AUTOMATION_BROWSER]
    examples = [
        "ask chatgpt about quantum computing",
        "ask chatgpt how to write a resignation email",
        "ask gemini about machine learning",
        "research climate change",
        "explain recursion in python",
        "help me write a cover letter",
        "summarize this: long text here",
        "ask about stock market basics",
    ]

    def matches(self, text: str) -> float:
        t = (text or "").lower()
        # Strong: explicit AI provider ask
        if re.search(
            r"\b(ask|query|use)\s+(chat\s*gpt|chatgpt|gpt|openai|gemini|claude|perplexity|bard)\b",
            t,
        ):
            return 0.98
        if re.search(r"\b(chat\s*gpt|chatgpt|gemini|claude|perplexity)\s*[:\-]", t):
            return 0.96
        # Research / explain / help me write (work tasks)
        if re.search(r"\bhelp\s+me\s+(write|draft|create|with|understand)\b", t):
            return 0.94
        if re.search(
            r"\b(research|look\s*up|investigate|explain|define)\b",
            t,
        ):
            if re.search(r"\b(timer|note that|open youtube)\b", t):
                return 0.15
            return 0.9
        if re.search(r"\b(write|draft)\s+(a|an|the)?\s*(professional\s+)?(email|letter|essay|report|resume|cover letter)\b", t):
            return 0.92
        if re.search(r"\b(what is|what's|how do i|how to)\b", t) and len(t.split()) >= 3:
            # Avoid "what is the time"
            if re.search(r"\b(time|date|day|status)\b", t):
                return 0.1
            return 0.82
        if re.search(r"\bsummari[sz]e\b", t):
            return 0.9
        if re.search(r"\bask about\b", t) or re.match(r"^ask\s+\w+", t):
            return 0.88
        return 0.0

    async def run(self, ctx: SkillContext) -> SkillResult:
        provider, query = _extract_query(ctx.user_text or "")
        if ctx.params.get("query"):
            query = str(ctx.params["query"])
        if ctx.params.get("provider"):
            provider = str(ctx.params["provider"])

        query = (query or "").strip()
        if not query or len(query) < 2:
            return SkillResult(
                success=False,
                message="What should I ask, sir? Example: ask chatgpt about machine learning.",
                skill=self.name,
                error="MISSING_QUERY",
            )

        # Local answer only when real Ollama is connected (avoid weak fallback noise)
        local_answer: str | None = None
        try:
            from backend.services.ai_service import get_ai_service

            ai = get_ai_service()
            await ai.initialize()
            if getattr(ai, "_ollama_reachable", False):
                prompt = (
                    f"Answer this clearly and helpfully in under 100 words "
                    f"as JARVIS assisting with work. Be concrete.\n\n{query}"
                )
                result = await ai.chat(prompt, session_id="work", use_memory=False)
                local_answer = result.response
        except Exception as exc:
            logger.debug(f"Local AI answer skipped: {exc}")

        url = _open_provider(provider, query, dry_run=ctx.dry_run)
        path = None
        if not ctx.dry_run:
            path = _save_work_prompt(query, provider, local_answer)

        pretty_map = {
            "chatgpt": "ChatGPT",
            "gpt": "ChatGPT",
            "openai": "ChatGPT",
            "gemini": "Gemini",
            "bard": "Gemini",
            "claude": "Claude",
            "perplexity": "Perplexity",
            "google": "Google",
        }
        pretty = pretty_map.get(provider.lower(), provider.title())

        q_short = query[:90] + ("…" if len(query) > 90 else "")
        if local_answer:
            spoken = local_answer.strip()
            if len(spoken) > 350:
                spoken = spoken[:350].rsplit(" ", 1)[0] + "…"
            msg = (
                f"Certainly, sir. Quick take: {spoken} "
                f"I've opened {pretty} with: \"{q_short}\" for a deeper answer."
            )
        else:
            msg = (
                f"Certainly, sir. Opening {pretty} with your question: \"{q_short}\". "
                f"Continue the work there — I've saved the prompt for you."
            )

        return SkillResult(
            success=True,
            message=msg,
            skill=self.name,
            data={
                "provider": provider,
                "query": query,
                "url": url,
                "local_answer": local_answer,
                "saved": str(path) if path else None,
                "dry_run": ctx.dry_run,
            },
        )


class OpenChatGPTSkill(Skill):
    """Just open ChatGPT (no query) — 'open chatgpt'."""

    name = "work.open_chatgpt"
    description = "Open ChatGPT in the browser."
    permissions = [Permission.AUTOMATION_BROWSER]
    examples = ["open chatgpt", "open chat gpt", "launch chatgpt"]

    def matches(self, text: str) -> float:
        t = (text or "").lower()
        if re.search(r"\bopen\s+(chat\s*gpt|chatgpt|gpt)\b", t):
            # If there's a question after, prefer ask skill
            if re.search(r"\b(about|how|what|why|write|explain)\b", t):
                return 0.5
            return 0.95
        return 0.0

    async def run(self, ctx: SkillContext) -> SkillResult:
        url = "https://chatgpt.com"
        if not ctx.dry_run:
            webbrowser.open(url, new=2)
        return SkillResult(
            True,
            "Opening ChatGPT, sir.",
            self.name,
            data={"url": url},
        )
