"""Tests for email skill + contact book + parser."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from skills.email_skill import parse_email_command, EmailSkill, save_draft
from skills.base import SkillContext
from memory.contacts import ContactBook
from agents.orchestrator import get_orchestrator
from core.security import get_permission_manager, Permission
from core.config import get_settings, _clear_settings_cache


@pytest.fixture(autouse=True)
def _grants(tmp_path, monkeypatch):
    pm = get_permission_manager()
    for p in (
        Permission.AUTOMATION_BROWSER,
        Permission.NETWORK_ACCESS,
        Permission.MEMORY_WRITE,
        Permission.MEMORY_READ,
        Permission.VOICE_SPEAK,
    ):
        if not pm.has_permission(p):
            pm.grant(p, reason="test")


def test_parse_email_saying():
    p = parse_email_command("email Mom saying I will be late")
    assert p["to"] and "mom" in p["to"].lower()
    assert p["body"] and "late" in p["body"].lower()


def test_parse_email_address():
    p = parse_email_command(
        "send email to alice@example.com subject Hello body How are you"
    )
    assert p["to"] == "alice@example.com" or "alice@example.com" in (p["to"] or "")
    assert p["mode"] == "send"


def test_parse_draft():
    p = parse_email_command("draft email to bob@test.com saying meeting at five")
    assert p["mode"] == "draft"
    assert p["body"]


@pytest.mark.asyncio
async def test_email_skill_draft_with_address(tmp_path, monkeypatch):
    # Point drafts at temp via monkeypatch of settings data dir is heavy;
    # skill still works — just assert success path for known email
    skill = EmailSkill()
    result = await skill.run(
        SkillContext(
            user_text="email alice@example.com saying Hello from unit test",
            dry_run=True,
        )
    )
    assert result.success
    assert "alice@example.com" in result.message or result.data.get("to") == "alice@example.com"


@pytest.mark.asyncio
async def test_email_unknown_contact():
    skill = EmailSkill()
    result = await skill.run(
        SkillContext(user_text="email ZzxqUnknown saying hi", dry_run=False)
    )
    # Should fail gracefully with guidance
    assert result.success is False
    assert result.error in ("UNKNOWN_CONTACT", "MISSING_TO") or "don't have" in result.message.lower() or "draft" in result.message.lower()


@pytest.mark.asyncio
async def test_orchestrator_email():
    orch = get_orchestrator()
    r = await orch.handle("email test@example.com saying Hello JARVIS", dry_run=True)
    assert r.handled
    assert r.skill == "email.send"


def test_contact_book_upsert(tmp_path):
    path = tmp_path / "contacts.json"
    book = ContactBook(path=path)
    book.upsert("Mom", email="mom@example.com")
    name, email = book.resolve_email("Mom")
    assert email == "mom@example.com"
    assert name == "Mom"
    # alias
    book.upsert("Mom", email="mom@example.com", aliases=["mother", "mum"])
    _, email2 = book.resolve_email("mum")
    assert email2 == "mom@example.com"


def test_api_email_skill():
    from fastapi.testclient import TestClient
    from backend.app.main import create_app

    app = create_app()
    client = TestClient(app)

    r = client.post(
        "/api/v1/skills/execute",
        json={
            "text": "email demo@example.com saying Hello from JARVIS API",
            "dry_run": True,
            "speak": False,
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert data["handled"] is True
    assert data["skill"] == "email.send"
