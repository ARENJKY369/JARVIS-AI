"""Tests for skill registry + orchestrator (one-command actions)."""

from __future__ import annotations

import pytest

from skills.registry import get_skill_registry, SkillRegistry
from skills.base import SkillContext
from skills.browser import OpenYouTubeSkill, OpenGmailSkill
from agents.orchestrator import get_orchestrator
from core.security import get_permission_manager, Permission


@pytest.fixture(autouse=True)
def _grants():
    pm = get_permission_manager()
    for p in (
        Permission.AUTOMATION_BROWSER,
        Permission.AUTOMATION_EXECUTE,
        Permission.SHELL_COMMAND,
        Permission.SYSTEM_INFO,
    ):
        if not pm.has_permission(p):
            pm.grant(p, reason="test")


def test_youtube_match():
    reg = get_skill_registry()
    skill = reg.match("Open YouTube")
    assert skill is not None
    assert skill.name == "browser.open_youtube"


def test_gmail_match():
    reg = get_skill_registry()
    skill = reg.match("open gmail please")
    assert skill is not None
    assert skill.name == "browser.open_gmail"


@pytest.mark.asyncio
async def test_youtube_dry_run():
    skill = OpenYouTubeSkill()
    result = await skill.run(SkillContext(user_text="Open YouTube", dry_run=True))
    assert result.success
    assert "youtube" in result.data["url"]


@pytest.mark.asyncio
async def test_youtube_search_dry_run():
    skill = OpenYouTubeSkill()
    result = await skill.run(
        SkillContext(user_text="Open YouTube search lo-fi hip hop", dry_run=True)
    )
    assert result.success
    assert "search_query" in result.data["url"]


@pytest.mark.asyncio
async def test_orchestrator_handles_youtube():
    orch = get_orchestrator()
    result = await orch.handle("Open YouTube", dry_run=True)
    assert result.handled
    assert result.skill == "browser.open_youtube"
    assert "YouTube" in result.reply or "youtube" in result.reply.lower()


@pytest.mark.asyncio
async def test_orchestrator_chat_fallback():
    orch = get_orchestrator()
    result = await orch.handle("Tell me a fun fact about black holes")
    # Chat is always handled now (JARVIS personality)
    assert result.handled is True
    assert result.intent == "chat"
    assert result.reply
    assert "sir" in result.reply.lower() or len(result.reply) > 10


def test_api_skills():
    from fastapi.testclient import TestClient
    from backend.app.main import create_app

    app = create_app()
    client = TestClient(app)

    r = client.get("/api/v1/skills")
    assert r.status_code == 200
    body = r.json()
    assert body["count"] >= 4

    r = client.post(
        "/api/v1/skills/execute",
        json={"text": "Open YouTube", "dry_run": True, "speak": False},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["handled"] is True
    assert data["skill"] == "browser.open_youtube"
