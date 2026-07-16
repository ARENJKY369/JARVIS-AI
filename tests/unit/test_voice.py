"""
Unit tests for JARVIS OS voice subsystem (TTS + command pipeline).
"""

from __future__ import annotations

import base64
import struct
import wave
import io

import pytest

from voice.tts import synthesize_speech, text_to_phonemes, SpeechResult
from voice.service import VoiceService, get_voice_service
from core.security import get_permission_manager, Permission
from core.config import _clear_settings_cache


def _wav_is_valid(data: bytes) -> tuple[bool, int, int]:
    """Return (ok, nframes, framerate) for a WAV blob."""
    bio = io.BytesIO(data)
    with wave.open(bio, "rb") as wf:
        return True, wf.getnframes(), wf.getframerate()


def test_phoneme_conversion_basic():
    phones = text_to_phonemes("Hello JARVIS")
    assert "HH" in phones or "EH" in phones
    assert any(p in phones for p in ("JH", "AA", "R", "V"))
    assert phones  # non-empty


def test_synthesize_produces_real_wav():
    result = synthesize_speech("Good evening, sir.")
    assert isinstance(result, SpeechResult)
    assert result.success
    assert result.duration_ms > 100
    assert len(result.audio_bytes) > 1000  # not a stub
    assert len(result.audio_base64) > 100
    assert result.data_uri.startswith("data:audio/wav;base64,")

    ok, nframes, rate = _wav_is_valid(result.audio_bytes)
    assert ok
    assert rate == 22050
    assert nframes > 1000

    # Decoded base64 must match raw bytes
    assert base64.b64decode(result.audio_base64) == result.audio_bytes


def test_synthesize_not_silent():
    """Audio must contain non-zero samples (actual sound)."""
    result = synthesize_speech("JARVIS online.")
    bio = io.BytesIO(result.audio_bytes)
    with wave.open(bio, "rb") as wf:
        frames = wf.readframes(wf.getnframes())
    # 16-bit little-endian samples
    samples = struct.unpack("<" + "h" * (len(frames) // 2), frames)
    peak = max(abs(s) for s in samples)
    assert peak > 500, f"Audio appears silent (peak={peak})"


def test_empty_text_returns_silence():
    result = synthesize_speech("   ")
    assert result.success
    assert result.duration_ms >= 50


def test_voice_profiles():
    a = synthesize_speech("Status report.", voice="jarvis")
    b = synthesize_speech("Status report.", voice="friday")
    assert a.success and b.success
    # Different profiles should produce different waveforms
    assert a.audio_bytes != b.audio_bytes


def test_female_voices_differ_from_male():
    from voice.tts import list_voices, resolve_voice_id

    catalog = list_voices()
    assert any(v["gender"] == "female" for v in catalog)
    assert any(v["gender"] == "male" for v in catalog)
    assert resolve_voice_id("friday") == "friday"
    assert resolve_voice_id("female") == "friday"

    male = synthesize_speech("Hello, systems online.", voice="jarvis")
    female = synthesize_speech("Hello, systems online.", voice="friday")
    assert male.success and female.success
    assert male.audio_bytes != female.audio_bytes
    assert "friday" in (female.engine or "") or female.duration_ms > 100


def test_all_voice_profiles_synthesize():
    from voice.tts import VOICE_PROFILES

    for vid in VOICE_PROFILES:
        r = synthesize_speech("At your service.", voice=vid)
        assert r.success, vid
        assert len(r.audio_bytes) > 1000, vid


def test_voice_service_synthesize():
    _clear_settings_cache()
    pm = get_permission_manager()
    if not pm.has_permission(Permission.VOICE_SPEAK):
        pm.grant(Permission.VOICE_SPEAK, reason="test")

    svc = VoiceService()
    result = svc.synthesize("At your service, sir.")
    assert result.success
    assert len(result.audio_base64) > 100
    peak_ok, _, _ = _wav_is_valid(result.audio_bytes)
    assert peak_ok


@pytest.mark.asyncio
async def test_voice_command_pipeline():
    pm = get_permission_manager()
    for p in (Permission.VOICE_SPEAK, Permission.VOICE_LISTEN):
        if not pm.has_permission(p):
            pm.grant(p, reason="test")

    svc = get_voice_service()
    await svc.initialize()
    result = await svc.handle_command(text="Hello JARVIS", speak=True)
    assert result.success
    assert result.response_text
    assert result.audio_base64
    low = result.response_text.lower()
    assert "sir" in low or "jarvis" in low or "online" in low or "morning" in low or "evening" in low


@pytest.mark.asyncio
async def test_voice_command_status():
    pm = get_permission_manager()
    pm.grant(Permission.VOICE_SPEAK, reason="test")
    svc = get_voice_service()
    result = await svc.handle_command(text="system status", speak=True)
    assert result.success
    assert result.audio_base64
    assert result.response_text


def test_api_voice_endpoints():
    """Full FastAPI smoke for voice routes."""
    from fastapi.testclient import TestClient
    from backend.app.main import create_app

    app = create_app()
    client = TestClient(app)

    # Status
    r = client.get("/api/v1/voice/status")
    assert r.status_code == 200
    body = r.json()
    assert body["tts"]["available"] is True
    assert body["tts"]["engine"] == "jarvis-formant"

    # Synthesize
    r = client.post(
        "/api/v1/voice",
        json={"action": "synthesize", "text": "Good evening, sir."},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["success"] is True
    assert data["audio_base64"]
    assert data["data_uri"]
    assert data["duration_ms"] > 100
    # Must not be the old stub (tiny silent wav)
    assert len(data["audio_base64"]) > 200

    # Speak
    r = client.post("/api/v1/voice/speak", json={"text": "JARVIS online."})
    assert r.status_code == 200
    assert "jarvis-formant" in (r.json().get("engine") or "")

    # Raw WAV
    r = client.post("/api/v1/voice/speak.wav", json={"text": "Hello."})
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("audio/wav")
    assert len(r.content) > 1000
    ok, _, _ = _wav_is_valid(r.content)
    assert ok

    # Demo
    r = client.get("/api/v1/voice/demo")
    assert r.status_code == 200
    assert r.json()["audio_base64"]

    # Command
    r = client.post(
        "/api/v1/voice/command",
        json={"text": "What time is it?", "speak": True},
    )
    assert r.status_code == 200
    cmd = r.json()
    assert cmd["success"] is True
    assert cmd["audio_base64"]
    assert cmd["response_text"]
    assert any(x in cmd["response_text"].lower() for x in ("time", ":", "sir", "clock"))

    # Console UI
    r = client.get("/console")
    assert r.status_code == 200
    assert b"JARVIS" in r.content
