"""
JARVIS OS - Computer Vision Pipeline
====================================

Screen understanding, OCR, and object detection.

Components:
- OCR: pytesseract / easyocr
- Screen capture and analysis
"""

from .ocr import OCREngine, get_ocr_engine

__all__ = ["OCREngine", "get_ocr_engine"]
