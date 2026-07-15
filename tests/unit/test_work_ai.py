"""Tests for ChatGPT / work AI skills."""

from __future__ import annotations

import pytest

from skills.work_ai import AskChatGPTSkill, OpenChatGPTSkill, _extract_query
from skills.base import SkillContext
from skills.registry import get_skill_registry
from agents.orchestrator import get_orchestrator
from core.security import get_permission_manager, Permission


@pytest.fixture(autouse=True)
def _grants():
    pm = get_permission_manager()
    for p in (
        Permission.AUTOMATION_BROWSER,
        Permission.VOICE_SPEAK,
        Permission.SYSTEM_INFO,
    ):
        if not pm.has_permission(p):
            pm.grant(p, reason="test")


def test_extract_ask_chatgpt():
    p, q = _extract_query("ask chatgpt about quantum computing")
    assert "chatgpt" in p or p == "gpt"
    assert "quantum" in q.lower()


def test_extract_research():
    p, q = _extract_query("research climate change impacts")
    assert p == "chatgpt"
    assert "climate" in q.lower()


def test_extract_help_write():
    p, q = _extract_query("help me write a cover letter for Google")
    assert "cover" in q.lower() or "write" in q.lower()


def test_match_ask():
    reg = get_skill_registry()
    skill = reg.match("ask chatgpt about black holes")
    assert skill is not None
    assert skill.name == "work.ask_ai"


@pytest.mark.asyncio
async def test_ask_skill_dry_run():
    skill = AskChatGPTSkill()
    result = await skill.run(
        SkillContext(
            user_text="ask chatgpt about machine learning basics",
            dry_run=True,
        )
    )
    assert result.success
    assert "chatgpt.com" in (result.data.get("url") or "")
    assert "machine learning" in (result.data.get("query") or "").lower()


@pytest.mark.asyncio
async def test_open_chatgpt():
    skill = OpenChatGPTSkill()
    result = await skill.run(SkillContext(user_text="open chatgpt", dry_run=True))
    assert result.success


@pytest.mark.asyncio
async def test_orchestrator_ask():
    orch = get_orchestrator()
    r = await orch.handle("ask chatgpt about python decorators", dry_run=True)
    assert r.handled
    assert r.skill == "work.ask_ai"


def test_api_ask():
    from fastapi.testclient import TestClient
    from backend.app.main import create_app

    client = TestClient(create_app())
    r = client.post(
        "/api/v1/skills/execute",
        json={
            "text": "ask chatgpt about the solar system",
            "dry_run": True,
            "speak": False,
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert data["handled"] is True
    assert data["skill"] == "work.ask_ai"
