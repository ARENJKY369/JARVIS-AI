"""
JARVIS OS - Wake Word Detection
================================

Always-on wake word detection using openWakeWord or Vosk.

Features:
- Continuous listening for "Hey JARVIS" / "JARVIS"
- Multiple wake word support
- Low CPU usage
- Configurable sensitivity
- Callback-based activation
"""

from __future__ import annotations

import collections
import threading
import time
from typing import Any, Callable

from loguru import logger

from core.config import get_settings
from core.security import get_permission_manager, Permission, AuditEventType, get_audit_logger


class WakeWordDetector:
    """Always-on wake word detection engine."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.pm = get_permission_manager()
        self.audit = get_audit_logger()
        self._engine: str = "none"
        self._detector: Any = None
        self._running = False
        self._thread: threading.Thread | None = None
        self._callbacks: list[Callable[[], None]] = []
        self._wake_words = ["hey jarvis", "jarvis", "hey j.a.r.v.i.s"]
        self._sensitivity = 0.5
        self._cooldown = 2.0  # seconds between activations
        self._last_activation = 0.0
        self._audio_buffer = collections.deque(maxlen=16000)  # 1 second at 16kHz

    def initialize(self) -> bool:
        """Initialize the wake word detection engine."""
        self.pm.require(Permission.VOICE_LISTEN)

        # Try openWakeWord first (best accuracy)
        try:
            import openwakeword
            from openwakeword.model import Model
            self._detector = Model(wakeword_models=["hey_jarvis"])
            self._engine = "openwakeword"
            logger.success("Wake word engine ready (openWakeWord)")
            return True
        except ImportError:
            logger.debug("openWakeWord not available")

        # Fallback to Vosk Kaldi
        try:
            import vosk
            import pyaudio

            model = vosk.Model(model_name="vosk-model-small-en-us-0.15")
            self._detector = vosk.KaldiRecognizer(model, 16000)
            self._engine = "vosk"
            logger.success("Wake word engine ready (Vosk)")
            return True
        except ImportError:
            logger.debug("Vosk not available")

        # Fallback: browser-based detection (manual trigger)
        self._engine = "browser"
        logger.info("Wake word: browser-based (manual trigger via console)")
        return True

    def start(self) -> None:
        """Start continuous wake word listening."""
        if self._running:
            return

        self.pm.require(Permission.VOICE_LISTEN)
        self.audit.log_event(AuditEventType.AUTOMATION_ACTION, details={"action": "wake_word_start"})

        if self._engine == "browser":
            logger.info("Wake word: using browser-based trigger (click mic in console)")
            return

        self._running = True
        self._thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._thread.start()
        logger.info("Wake word detection started")

    def stop(self) -> None:
        """Stop wake word listening."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=3)
        self.audit.log_event(AuditEventType.AUTOMATION_ACTION, details={"action": "wake_word_stop"})
        logger.info("Wake word detection stopped")

    def _listen_loop(self) -> None:
        """Main listening loop running in background thread."""
        try:
            import pyaudio

            audio = pyaudio.PyAudio()
            stream = audio.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=16000,
                input=True,
                frames_per_buffer=1024,
            )

            while self._running:
                try:
                    data = stream.read(1024, exception_on_overflow=False)
                    self._audio_buffer.extend(data)

                    if self._engine == "openwakeword":
                        self._check_openwakeword(data)
                    elif self._engine == "vosk":
                        self._check_vosk(data)
                except Exception as e:
                    logger.debug(f"Audio read error: {e}")
                    time.sleep(0.1)

            stream.stop_stream()
            stream.close()
            audio.terminate()
        except ImportError:
            logger.warning("pyaudio not available — wake word disabled")
        except Exception as e:
            logger.error(f"Wake word listen loop error: {e}")

    def _check_openwakeword(self, audio_data: bytes) -> None:
        """Check audio with openWakeWord."""
        try:
            import numpy as np
            audio_array = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
            prediction = self._detector.predict(audio_array)
            for wakeword, score in prediction.items():
                if score > self._sensitivity:
                    self._trigger()
                    break
        except Exception as e:
            logger.debug(f"openWakeWord check error: {e}")

    def _check_vosk(self, audio_data: bytes) -> None:
        """Check audio with Vosk."""
        try:
            if self._detector.AcceptWaveform(audio_data):
                result = self._detector.Result()
                text = result.lower() if isinstance(result, str) else ""
                for ww in self._wake_words:
                    if ww in text:
                        self._trigger()
                        break
        except Exception as e:
            logger.debug(f"Vosk check error: {e}")

    def _trigger(self) -> None:
        """Trigger wake word activation."""
        now = time.time()
        if now - self._last_activation < self._cooldown:
            return

        self._last_activation = now
        self.audit.log_event(AuditEventType.AUTOMATION_ACTION, details={"action": "wake_word_triggered"})
        logger.info("Wake word detected!")

        for callback in self._callbacks:
            try:
                callback()
            except Exception as e:
                logger.error(f"Wake word callback error: {e}")

    def on_wake(self, callback: Callable[[], None]) -> None:
        """Register a callback for when wake word is detected."""
        self._callbacks.append(callback)

    def set_sensitivity(self, value: float) -> None:
        """Set detection sensitivity (0.0 to 1.0)."""
        self._sensitivity = max(0.0, min(1.0, value))

    def set_wake_words(self, words: list[str]) -> None:
        """Set custom wake words."""
        self._wake_words = [w.lower() for w in words]

    def get_status(self) -> dict[str, Any]:
        """Get wake word detector status."""
        return {
            "engine": self._engine,
            "running": self._running,
            "wake_words": self._wake_words,
            "sensitivity": self._sensitivity,
            "callbacks": len(self._callbacks),
        }

    def process_audio_chunk(self, audio_data: bytes) -> bool:
        """Process a single audio chunk (for browser-based detection)."""
        if self._engine == "openwakeword":
            self._check_openwakeword(audio_data)
        elif self._engine == "vosk":
            self._check_vosk(audio_data)
        return False


_wake_word: WakeWordDetector | None = None


def get_wake_word_detector() -> WakeWordDetector:
    global _wake_word
    if _wake_word is None:
        _wake_word = WakeWordDetector()
    return _wake_word
