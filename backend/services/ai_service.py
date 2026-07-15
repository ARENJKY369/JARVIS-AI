"""
JARVIS OS - Advanced AI Service (v2 — Tony Stark mode)
======================================================

Local Ollama when available; otherwise a high-fidelity JARVIS
personality fallback that still feels human and present.
"""

from __future__ import annotations

import asyncio
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Deque

from loguru import logger

try:
    from ollama import AsyncClient

    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False
    AsyncClient = None  # type: ignore

from core.config import get_settings, Settings
from core.security import get_audit_logger, AuditEventType
from agents.personality import (
    JARVIS_SYSTEM_PROMPT,
    conversational_reply,
    jarvis_wrap,
    build_ollama_messages,
)


@dataclass
class ChatResult:
    response: str
    model: str
    duration_ms: float
    tokens_used: int | None = None
    success: bool = True
    error: str | None = None


@dataclass
class Conversation:
    messages: Deque[dict] = field(default_factory=lambda: deque(maxlen=20))
    session_id: str = "default"

    def add(self, role: str, content: str) -> None:
        self.messages.append({"role": role, "content": content})

    def get_context(self, max_messages: int = 10) -> list[dict]:
        return list(self.messages)[-max_messages:]


class AIService:
    """The brain — JARVIS personality first."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.audit = get_audit_logger()
        self._client: AsyncClient | None = None
        self._initialized = False
        self._ollama_reachable = False
        self._conversations: dict[str, Conversation] = {}

        if OLLAMA_AVAILABLE:
            self._client = AsyncClient(host=self.settings.ai.ollama_host)

    async def initialize(self) -> None:
        if self._initialized:
            return
        if not OLLAMA_AVAILABLE or not self._client:
            logger.warning("Ollama not available — JARVIS personality fallback active.")
            self._initialized = True
            return
        try:
            await asyncio.wait_for(self._client.list(), timeout=2.5)
            self._ollama_reachable = True
            logger.success(f"✅ Ollama connected: {self.settings.ai.ollama_host}")
        except Exception as e:
            logger.warning(f"Ollama unreachable ({e}) — personality fallback.")
            self._ollama_reachable = False
        self._initialized = True

    def _get_or_create_conversation(self, session_id: str = "default") -> Conversation:
        if session_id not in self._conversations:
            self._conversations[session_id] = Conversation(session_id=session_id)
        return self._conversations[session_id]

    async def chat(
        self,
        message: str,
        *,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        session_id: str = "default",
        use_memory: bool = True,
    ) -> ChatResult:
        await self.initialize()

        model = model or self.settings.ai.default_model
        temperature = temperature if temperature is not None else self.settings.ai.temperature
        max_tokens = max_tokens or self.settings.ai.max_tokens

        start = time.perf_counter()
        conv = self._get_or_create_conversation(session_id)

        if use_memory:
            conv.add("user", message)
            try:
                from backend.services.memory_service import get_memory_service

                mem = get_memory_service()
                mem.store(session_id, f"[user] {message}")
            except Exception:
                pass

        if self._ollama_reachable and self._client:
            try:
                history = conv.get_context() if use_memory else []
                # history already includes the user msg we just added — drop last for builder
                prior = list(history)[:-1] if history else []
                messages = build_ollama_messages(prior, message)

                resp = await self._client.chat(
                    model=model,
                    messages=messages,
                    options={
                        "temperature": temperature,
                        "num_predict": max_tokens,
                    },
                )
                content = resp["message"]["content"].strip()
                content = jarvis_wrap(content)

                if use_memory:
                    conv.add("assistant", content)

                dur = (time.perf_counter() - start) * 1000
                self.audit.log_event(
                    AuditEventType.AUTOMATION_ACTION,
                    details={"ai": "real", "model": model},
                )
                return ChatResult(
                    response=content,
                    model=model,
                    duration_ms=dur,
                    tokens_used=len(content.split()),
                )
            except Exception as exc:
                logger.warning(f"Real LLM failed: {exc}. Personality fallback.")
                self._ollama_reachable = False

        dur = (time.perf_counter() - start) * 1000
        fallback = conversational_reply(message)
        if use_memory:
            conv.add("assistant", fallback)

        self.audit.log_event(
            AuditEventType.AUTOMATION_ACTION, details={"ai": "jarvis_personality"}
        )
        return ChatResult(
            response=fallback,
            model="jarvis-personality-v2",
            duration_ms=dur,
            tokens_used=len(fallback.split()),
        )

    async def list_models(self) -> list[str]:
        await self.initialize()
        if self._ollama_reachable and self._client:
            try:
                data = await self._client.list()
                return [m["name"] for m in data.get("models", [])]
            except Exception:
                pass
        return [self.settings.ai.default_model, "jarvis-personality-v2"]

    async def health_check(self) -> dict[str, Any]:
        await self.initialize()
        return {
            "ollama_connected": self._ollama_reachable,
            "default_model": self.settings.ai.default_model,
            "conversations_active": len(self._conversations),
            "mode": "real" if self._ollama_reachable else "jarvis_personality",
            "personality": "tony_stark_butler",
            "memory_enabled": True,
            "system_prompt_loaded": True,
        }


_ai_service: AIService | None = None


def get_ai_service() -> AIService:
    global _ai_service
    if _ai_service is None:
        _ai_service = AIService()
    return _ai_service
