"""
End-to-end quality matrix — every critical path must stay green.
This file is the automated backbone of the 10/10 quality scorecard.
"""

from __future__ import annotations

import base64
import io
import struct
import wave
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.app.main import create_app
from core.security import get_permission_manager, Permission
from skills.registry import get_skill_registry
import skills.registry as regmod


@pytest.fixture(scope="module")
def client():
    regmod._registry = None
    pm = get_permission_manager()
    for p in Permission:
        try:
            if not pm.has_permission(p):
                pm.grant(p, reason="quality-matrix")
        except Exception:
            pass
    return TestClient(create_app())


@pytest.fixture(autouse=True)
def _grants():
    pm = get_permission_manager()
    for p in Permission:
        try:
            if not pm.has_permission(p):
                pm.grant(p, reason="quality-matrix")
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Structure
# ---------------------------------------------------------------------------

REQUIRED_FILES = [
    "core/config/settings.py",
    "agents/orchestrator.py",
    "agents/planner.py",
    "agents/personality.py",
    "skills/work_ai.py",
    "voice/tts.py",
    "frontend/public/index.html",
    "docs/IRON_MAN_OS.md",
    "scripts/quality_gate.py",
    ".env.example",
]


def test_required_files_exist():
    root = Path(__file__).resolve().parents[2]
    missing = [f for f in REQUIRED_FILES if not (root / f).is_file()]
    assert not missing, f"Missing: {missing}"


# ---------------------------------------------------------------------------
# Skills
# ---------------------------------------------------------------------------

COMMAND_MATRIX = [
    ("Open YouTube", "browser.open_youtube"),
    ("Open Gmail", "browser.open_gmail"),
    ("ask chatgpt about robots", "work.ask_ai"),
    ("research black holes", "work.ask_ai"),
    ("help me write a resume", "work.ask_ai"),
    ("email demo@example.com saying Hello", "email.send"),
    ("set a timer for 2 minutes", "util.timer"),
    ("calculate 9*9", "util.calculate"),
    ("note ship the release", "util.note"),
    ("play jazz", "media.play"),
    ("System status", "system.status"),
    ("open whatsapp", "browser.open_site"),
    ("add contact Test email t@example.com", "contacts.add"),
]


@pytest.mark.parametrize("text,skill", COMMAND_MATRIX)
def test_skill_routing_matrix(text, skill):
    regmod._registry = None
    reg = get_skill_registry()
    matched = reg.match(text, threshold=0.42)
    assert matched is not None, f"No skill for: {text}"
    assert matched.name == skill, f"{text} → {matched.name}, expected {skill}"


def test_at_least_20_skills():
    regmod._registry = None
    reg = get_skill_registry()
    assert len(reg.list_skills()) >= 20


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------

GET_ENDPOINTS = [
    "/",
    "/api/v1/health",
    "/api/v1/ready",
    "/api/v1/system/status",
    "/api/v1/ai/health",
    "/api/v1/voice/status",
    "/api/v1/skills",
    "/console",
]


@pytest.mark.parametrize("path", GET_ENDPOINTS)
def test_get_endpoints_ok(client, path):
    r = client.get(path)
    assert r.status_code == 200, f"{path} → {r.status_code}"


def test_voice_command_chat(client):
    r = client.post(
        "/api/v1/voice/command",
        json={"text": "How are you?", "speak": False},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    assert body["response_text"]
    assert len(body["response_text"]) > 10


def test_voice_command_skill(client):
    r = client.post(
        "/api/v1/voice/command",
        json={"text": "calculate 10+5", "speak": False},
    )
    assert r.status_code == 200
    body = r.json()
    assert "15" in body["response_text"]


def test_voice_command_mission(client):
    r = client.post(
        "/api/v1/voice/command",
        json={"text": "open youtube and calculate 2+2", "speak": False},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    # multi mission or sequential handling
    assert body.get("skill") in ("mission.multi", "browser.open_youtube") or "2" in body[
        "response_text"
    ] or "Mission" in body["response_text"] or "YouTube" in body["response_text"]


def test_skills_execute_chatgpt(client):
    r = client.post(
        "/api/v1/skills/execute",
        json={"text": "ask chatgpt about testing", "dry_run": True, "speak": False},
    )
    assert r.status_code == 200
    assert r.json()["skill"] == "work.ask_ai"


def test_tts_audible(client):
    r = client.post("/api/v1/voice/speak", json={"text": "Quality ten out of ten."})
    assert r.status_code == 200
    data = r.json()
    raw = base64.b64decode(data["audio_base64"])
    assert len(raw) > 2000
    with wave.open(io.BytesIO(raw), "rb") as wf:
        frames = wf.readframes(wf.getnframes())
        samples = struct.unpack("<" + "h" * (len(frames) // 2), frames)
        peak = max(abs(s) for s in samples)
    assert peak > 1000, f"silent audio peak={peak}"


def test_console_html_has_jarvis(client):
    r = client.get("/console")
    assert r.status_code == 200
    assert b"JARVIS" in r.content
    assert b"voice" in r.content.lower() or b"command" in r.content.lower()


# ---------------------------------------------------------------------------
# Security
# ---------------------------------------------------------------------------

def test_permission_require_denies():
    from core.security.permissions import PermissionManager
    from core.config import get_settings

    # Fresh manager logic: revoke PLUGIN_EXECUTE if present
    pm = get_permission_manager()
    pm.revoke(Permission.PLUGIN_EXECUTE)
    assert not pm.has_permission(Permission.PLUGIN_EXECUTE)
    with pytest.raises(PermissionError):
        pm.require(Permission.PLUGIN_EXECUTE)


def test_settings_repr_safe():
    from core.config import get_settings

    r = repr(get_settings())
    assert "password" not in r.lower()
    assert "JARVIS" in r


# ---------------------------------------------------------------------------
# Personality
# ---------------------------------------------------------------------------

def test_personality_greeting():
    from agents.personality import conversational_reply

    r = conversational_reply("Hello")
    assert "sir" in r.lower()


def test_personality_help_mentions_chatgpt():
    from agents.personality import conversational_reply

    r = conversational_reply("what can you do")
    assert "chatgpt" in r.lower() or "youtube" in r.lower() or "email" in r.lower()
