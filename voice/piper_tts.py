"""
JARVIS OS - Optional Piper Neural TTS Adapter
=============================================

Uses piper-tts when installed + a local .onnx voice model.
Falls back gracefully so the formant engine remains the default.

Install:
    pip install piper-tts
    python scripts/download_piper_voice.py

Env / settings:
    JARVIS_VOICE_TTS_ENGINE=auto|piper|formant
    JARVIS_VOICE_TTS_MODEL=en_GB-alan-medium
    JARVIS_VOICE_PIPER_MODEL_PATH=/path/to/model.onnx
"""

from __future__ import annotations

import base64
import io
import wave
from pathlib import Path
from typing import Any

from loguru import logger

from core.config import get_settings
from .tts import SpeechResult, synthesize_speech


def _find_piper_model() -> Path | None:
    settings = get_settings()
    if settings.voice.piper_model_path:
        p = Path(settings.voice.piper_model_path)
        if p.is_file():
            return p

    models_root = settings.base_dir / settings.models_dir / "piper"
    name = settings.voice.tts_model  # e.g. en_GB-alan-medium
    candidates = [
        models_root / f"{name}.onnx",
        models_root / name / f"{name}.onnx",
        models_root / name / "model.onnx",
    ]
    # Also scan one level
    if models_root.is_dir():
        for p in models_root.rglob("*.onnx"):
            if name.replace("-", "") in p.stem.replace("-", "") or name in str(p):
                candidates.insert(0, p)
    for c in candidates:
        if c.is_file():
            return c
    # Any onnx under piper/
    if models_root.is_dir():
        found = list(models_root.rglob("*.onnx"))
        if found:
            return found[0]
    return None


def piper_available() -> bool:
    try:
        import piper  # noqa: F401
    except ImportError:
        try:
            from piper import PiperVoice  # noqa: F401
        except ImportError:
            return False
    return _find_piper_model() is not None


def synthesize_with_piper(text: str, *, voice: str = "jarvis") -> SpeechResult | None:
    """
    Try Piper neural TTS. Returns None if unavailable so caller can fall back.
    """
    model_path = _find_piper_model()
    if model_path is None:
        return None

    try:
        # piper-tts API variants across versions
        try:
            from piper import PiperVoice
        except ImportError:
            from piper.voice import PiperVoice  # type: ignore

        voice_model = PiperVoice.load(str(model_path))
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            voice_model.synthesize(text, wf)

        raw = buf.getvalue()
        if len(raw) < 100:
            return None
        # Read rate
        with wave.open(io.BytesIO(raw), "rb") as r:
            rate = r.getframerate()
            nframes = r.getnframes()
            duration_ms = (nframes / max(rate, 1)) * 1000.0

        b64 = base64.b64encode(raw).decode("ascii")
        return SpeechResult(
            audio_bytes=raw,
            audio_base64=b64,
            duration_ms=duration_ms,
            sample_rate=rate,
            text=text,
            success=True,
            message=f"Piper neural TTS ({model_path.name})",
            engine="piper",
        )
    except Exception as exc:
        logger.warning(f"Piper synthesis failed: {exc}")
        return None


def synthesize_auto(
    text: str,
    *,
    voice: str = "jarvis",
    sample_rate: int = 22050,
    rate: float = 0.95,
    volume: float = 0.9,
    base_f0: float | None = None,
) -> SpeechResult:
    """
    Engine selector:
      - formant: always
      - piper: try piper only
      - auto: piper if ready else formant
    """
    settings = get_settings()
    engine = (settings.voice.tts_engine or "auto").lower()

    if engine in ("piper", "auto"):
        result = synthesize_with_piper(text, voice=voice)
        if result is not None:
            return result
        if engine == "piper":
            logger.warning("Piper requested but unavailable — falling back to formant")

    # Pass through base_f0 only when provided; profile F0 is used otherwise
    # (do NOT force settings.pitch_hz onto female / non-jarvis voices)
    return synthesize_speech(
        text,
        voice=voice,
        sample_rate=sample_rate,
        rate=rate,
        volume=volume,
        base_f0=base_f0,
    )


def tts_status() -> dict[str, Any]:
    settings = get_settings()
    model = _find_piper_model()
    return {
        "configured_engine": settings.voice.tts_engine,
        "piper_package": _piper_pkg(),
        "piper_model": str(model) if model else None,
        "piper_ready": model is not None and _piper_pkg(),
        "formant_ready": True,
        "active_fallback": "formant",
        "recommended_model": settings.voice.tts_model,
    }


def _piper_pkg() -> bool:
    try:
        import piper  # noqa: F401

        return True
    except ImportError:
        try:
            from piper import PiperVoice  # noqa: F401

            return True
        except ImportError:
            return False


__all__ = [
    "synthesize_auto",
    "synthesize_with_piper",
    "piper_available",
    "tts_status",
]
