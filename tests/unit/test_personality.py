"""JARVIS personality + everyday skills."""

from __future__ import annotations

import pytest

from agents.personality import conversational_reply, style_skill_reply, time_of_day_greeting
from agents.orchestrator import get_orchestrator
from skills.registry import get_skill_registry
from skills.base import SkillContext
from core.security import get_permission_manager, Permission


@pytest.fixture(autouse=True)
def _grants():
    pm = get_permission_manager()
    for p in Permission:
        if not pm.has_permission(p):
            try:
                pm.grant(p, reason="test")
            except Exception:
                pass


def test_greeting_is_human():
    r = conversational_reply("Hello JARVIS")
    assert "sir" in r.lower()
    assert len(r) > 20


def test_how_are_you():
    r = conversational_reply("How are you?")
    assert "sir" in r.lower() or "operational" in r.lower()


def test_style_skill():
    s = style_skill_reply("Opening YouTube.")
    assert "sir" in s.lower() or s.startswith("Certainly") or "Opening" in s


@pytest.mark.asyncio
async def test_play_music_skill():
    reg = get_skill_registry()
    skill = reg.match("play lo-fi hip hop")
    assert skill is not None
    assert skill.name == "media.play"
    result = await skill.run(SkillContext(user_text="play lo-fi hip hop", dry_run=True))
    assert result.success


@pytest.mark.asyncio
async def test_timer_skill():
    reg = get_skill_registry()
    skill = reg.match("set a timer for 10 minutes")
    assert skill is not None
    result = await skill.run(
        SkillContext(user_text="set a timer for 10 minutes", dry_run=True)
    )
    assert result.success
    assert result.data.get("seconds") == 600


@pytest.mark.asyncio
async def test_calculate():
    reg = get_skill_registry()
    skill = reg.match("calculate 12 * 8")
    assert skill is not None
    result = await skill.run(SkillContext(user_text="calculate 12 * 8"))
    assert result.success
    assert "96" in result.message


@pytest.mark.asyncio
async def test_note():
    reg = get_skill_registry()
    skill = reg.match("note buy milk")
    assert skill is not None
    result = await skill.run(SkillContext(user_text="note buy milk", dry_run=True))
    assert result.success


@pytest.mark.asyncio
async def test_open_whatsapp():
    reg = get_skill_registry()
    skill = reg.match("open whatsapp")
    assert skill is not None
    assert skill.name == "browser.open_site"


@pytest.mark.asyncio
async def test_universal_orchestrator():
    orch = get_orchestrator()
    # Action
    r1 = await orch.handle("Open YouTube", dry_run=True)
    assert r1.handled and r1.skill == "browser.open_youtube"
    # Chat
    r2 = await orch.handle("I had a long day")
    assert r2.handled and r2.reply
    # Math
    r3 = await orch.handle("calculate 7+5")
    assert r3.handled and "12" in r3.reply


def test_many_skills_registered():
    reg = get_skill_registry()
    assert len(reg.list_skills()) >= 15


def test_api_voice_chat_human():
    from fastapi.testclient import TestClient
    from backend.app.main import create_app

    client = TestClient(create_app())
    r = client.post(
        "/api/v1/voice/command",
        json={"text": "How are you feeling today?", "speak": False},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["success"]
    assert body["response_text"]
    assert "sir" in body["response_text"].lower() or len(body["response_text"]) > 15
