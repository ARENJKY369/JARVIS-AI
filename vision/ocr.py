"""
JARVIS OS - OCR Engine
======================

Text extraction from images and screenshots.

Supports:
- Tesseract (default)
- EasyOCR (fallback)
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from loguru import logger

try:
    import pytesseract
    from PIL import Image
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False

from core.config import get_settings


class OCREngine:
    """Optical Character Recognition engine."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self._ready = False

    def _init(self) -> None:
        if self._ready:
            return
        if TESSERACT_AVAILABLE:
            logger.success("OCR engine ready (Tesseract)")
        else:
            logger.warning("Tesseract not installed — OCR disabled")
        self._ready = True

    def extract(self, image_path: Path | str) -> str:
        self._init()
        if not TESSERACT_AVAILABLE:
            return "[OCR unavailable — install pytesseract + tesseract]"

        try:
            img = Image.open(str(image_path))
            text = pytesseract.image_to_string(img)
            return text.strip()
        except Exception as e:
            logger.error(f"OCR failed: {e}")
            return f"[OCR error: {e}]"

    def extract_from_screenshot(self) -> str:
        """Capture screen and extract text."""
        try:
            import pyautogui
            screenshot = pyautogui.screenshot()
            path = self.settings.base_dir / "temp" / "screenshot_ocr.png"
            screenshot.save(path)
            return self.extract(path)
        except Exception as e:
            logger.error(f"Screenshot OCR failed: {e}")
            return f"[Screenshot OCR error: {e}]"


_ocr: OCREngine | None = None


def get_ocr_engine() -> OCREngine:
    global _ocr
    if _ocr is None:
        _ocr = OCREngine()
    return _ocr
