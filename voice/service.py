"""
JARVIS OS - Voice Service (Tony Stark mode)
===========================================

Every utterance → orchestrator (skills + human JARVIS personality) → speak.
"""

from __future__ import annotations

import base64
import re
import time
from dataclasses import dataclass
from typing import Any

from loguru import logger

from core.config import get_settings, Settings
from core.security import get_audit_logger, AuditEventType, get_permission_manager, Permission

from .tts import SpeechResult
from .piper_tts import synthesize_auto, tts_status


@dataclass
class TranscriptionResult:
    text: str
    duration_ms: float
    confidence: float = 0.85
    engine: str = "fallback"
    success: bool = True
    message: str | None = None


@dataclass
class VoiceCommandResult:
    transcript: str
    response_text: str
    audio_base64: str | None
    duration_ms: float
    intent: str
    success: bool = True
    message: str | None = None
    data_uri: str | None = None
    skill: str | None = None


class VoiceService:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.audit = get_audit_logger()
        self._whisper = None
        self._whisper_ready = False
        self._initialized = False

    async def initialize(self) -> None:
        if self._initialized:
            return
        try:
            from faster_whisper import WhisperModel  # type: ignore

            self._whisper = WhisperModel(
                self.settings.voice.stt_model,
                device=self.settings.voice.device,
                compute_type="int8",
            )
            self._whisper_ready = True
            logger.success(f"Whisper STT ready (model={self.settings.voice.stt_model})")
        except Exception as exc:
            logger.info(f"Whisper unavailable ({exc}); browser STT / text input")
            self._whisper_ready = False
        self._initialized = True

    def synthesize(
        self,
        text: str,
        *,
        voice: str | None = None,
        rate: float = 0.95,
    ) -> SpeechResult:
        pm = get_permission_manager()
        pm.require(Permission.VOICE_SPEAK)

        from voice.tts import resolve_voice_id

        voice_profile = resolve_voice_id(
            voice or self.settings.ui.default_voice or "jarvis"
        )
        start = time.perf_counter()
        # Only force settings pitch for classic jarvis; other profiles keep their F0
        pitch_override = None
        if voice_profile == "jarvis":
            pitch_override = self.settings.voice.pitch_hz
        result = synthesize_auto(
            text,
            voice=voice_profile,
            sample_rate=self.settings.voice.sample_rate,
            rate=rate if rate != 0.95 else self.settings.voice.speaking_rate,
            base_f0=pitch_override,
        )
        elapsed = (time.perf_counter() - start) * 1000
        self.audit.log_event(
            AuditEventType.AUTOMATION_ACTION,
            details={
                "type": "voice_synthesize",
                "engine": result.engine,
                "voice": voice_profile,
                "chars": len(text or ""),
                "duration_ms": result.duration_ms,
                "synth_ms": round(elapsed, 1),
            },
        )
        return result

    def list_voices(self) -> list[dict]:
        """Selectable TTS profiles (male + female)."""
        from voice.tts import list_voices

        return list_voices()

    def transcribe(
        self, audio_base64: str | None = None, *, hint: str | None = None
    ) -> TranscriptionResult:
        pm = get_permission_manager()
        pm.require(Permission.VOICE_LISTEN)
        start = time.perf_counter()

        if hint and hint.strip():
            text, engine, conf = hint.strip(), "web-speech-api", 0.92
        elif self._whisper_ready and self._whisper and audio_base64:
            try:
                import tempfile
                import os

                raw = base64.b64decode(audio_base64)
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                    tmp.write(raw)
                    path = tmp.name
                try:
                    segments, _info = self._whisper.transcribe(path, beam_size=1)
                    text = " ".join(s.text.strip() for s in segments).strip()
                    engine, conf = "faster-whisper", 0.9
                finally:
                    os.unlink(path)
            except Exception as exc:
                logger.warning(f"Whisper failed: {exc}")
                text, engine, conf = "", "error", 0.0
        else:
            text = hint.strip() if hint else ""
            engine, conf = "fallback", 0.5 if text else 0.0

        success = bool(text)
        message = f"Transcribed via {engine}" if success else "No speech detected."
        dur = (time.perf_counter() - start) * 1000
        return TranscriptionResult(
            text=text or "",
            duration_ms=dur,
            confidence=conf,
            engine=engine,
            success=success,
            message=message,
        )

    def detect_intent(self, text: str) -> str:
        # Kept for API compatibility — orchestrator owns real routing now
        return "orchestrator"

    async def handle_command(
        self,
        *,
        text: str | None = None,
        audio_base64: str | None = None,
        speak: bool = True,
        voice: str | None = None,
    ) -> VoiceCommandResult:
        start = time.perf_counter()

        if text and text.strip():
            transcript = text.strip()
            tr_engine = "text"
        else:
            tr = self.transcribe(audio_base64, hint=None)
            transcript = tr.text
            tr_engine = tr.engine

        if not transcript:
            msg = "I didn't catch that, sir. One more time, if you please."
            audio_b64 = data_uri = None
            if speak:
                speech = self.synthesize(msg, voice=voice)
                audio_b64, data_uri = speech.audio_base64, speech.data_uri
            return VoiceCommandResult(
                transcript="",
                response_text=msg,
                audio_base64=audio_b64,
                duration_ms=(time.perf_counter() - start) * 1000,
                intent="none",
                success=False,
                message="Empty transcript",
                data_uri=data_uri,
            )

        # Universal path: multi-step mission planner → skills / chat
        from agents.planner import get_planner

        planner = get_planner()
        mission = await planner.run(transcript, session_id="voice")
        response = mission.reply
        # Primary skill = first action step, or chat
        skill = None
        intent = "mission" if mission.multi else "chat"
        if mission.steps:
            skill = mission.steps[0].skill
            if not mission.multi and skill:
                intent = (skill.split(".")[0] if skill else "chat")
            elif mission.multi:
                skill = "mission.multi"
                intent = "mission"

        audio_b64 = data_uri = None
        if speak and response:
            speech = self.synthesize(response, voice=voice)
            audio_b64, data_uri = speech.audio_base64, speech.data_uri

        return VoiceCommandResult(
            transcript=transcript,
            response_text=response,
            audio_base64=audio_b64,
            duration_ms=(time.perf_counter() - start) * 1000,
            intent=intent,
            success=True,
            message=f"Handled via {skill or intent}, stt={tr_engine}, steps={len(mission.steps)}",
            data_uri=data_uri,
            skill=skill,
        )

    def health(self) -> dict[str, Any]:
        ts = tts_status()
        active = "piper" if ts.get("piper_ready") else "jarvis-formant"
        try:
            from skills.registry import get_skill_registry

            n_skills = len(get_skill_registry().list_skills())
        except Exception:
            n_skills = 0
        return {
            "status": "operational",
            "mode": "tony_stark",
            "personality": "JARVIS butler",
            "skills_loaded": n_skills,
            "tts": {
                "engine": active,
                "available": True,
                "formant": True,
                "piper": ts,
            },
            "stt": {
                "engine": "faster-whisper" if self._whisper_ready else "web-speech-api+fallback",
                "whisper_ready": self._whisper_ready,
            },
            "sample_rate": self.settings.voice.sample_rate,
            "default_voice": self.settings.ui.default_voice,
            "voices": self.list_voices(),
            "email_configured": self.settings.email.is_configured(),
        }


_voice_service: VoiceService | None = None


def get_voice_service() -> VoiceService:
    global _voice_service
    if _voice_service is None:
        _voice_service = VoiceService()
    return _voice_service


__all__ = [
    "VoiceService",
    "get_voice_service",
    "TranscriptionResult",
    "VoiceCommandResult",
]
