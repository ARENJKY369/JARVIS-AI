"""
JARVIS OS - Vision & Camera Skill
===================================

Camera capture, face detection, screen reading, and environment analysis.
"""

from __future__ import annotations

import re
from typing import Any

from loguru import logger

from core.security import Permission
from .base import Skill, SkillContext, SkillResult


class VisionSkill(Skill):
    name = "vision.capture"
    description = "Camera capture, face detection, and screen reading."
    permissions = [Permission.VISION_CAPTURE, Permission.VISION_ANALYZE]
    examples = [
        "take a photo",
        "detect faces",
        "what's on my screen",
        "read my screen",
        "scan qr code",
        "analyze the room",
        "who is this",
    ]

    def matches(self, text: str) -> float:
        t = (text or "").lower()
        keywords = [
            "photo", "camera", "face", "detect", "screen",
            "read screen", "what's on", "scan", "qr",
            "analyze", "see", "who is", "recognize",
            "capture", "snapshot",
        ]
        if any(kw in t for kw in keywords):
            return 0.87
        return 0.0

    async def run(self, ctx: SkillContext) -> SkillResult:
        t = (ctx.user_text or "").lower()

        # Take photo
        if any(w in t for w in ["photo", "picture", "snapshot", "capture"]):
            return self._take_photo()

        # Face detection
        if "face" in t and ("detect" in t or "who" in t or "recognize" in t):
            return self._detect_faces()

        # Screen reading
        if any(w in t for w in ["screen", "what's on", "read"]):
            return self._read_screen()

        # QR scanning
        if "qr" in t or "scan" in t:
            return self._scan_qr()

        # Environment analysis
        if "analyze" in t or "room" in t:
            return self._analyze_environment()

        return SkillResult(False, "What would you like me to do with vision, sir?", self.name, error="UNKNOWN")

    def _take_photo(self) -> SkillResult:
        """Take a photo with the camera."""
        from vision.camera import get_camera
        cam = get_camera()
        cam.initialize()
        result = cam.capture_photo()
        if result.get("success"):
            return SkillResult(True, f"Photo captured, sir. Saved to {result['path']}.", self.name, data=result)
        return SkillResult(False, f"Photo capture failed: {result.get('error', 'unknown')}", self.name, error="CAPTURE_FAILED")

    def _detect_faces(self) -> SkillResult:
        """Detect faces in camera view."""
        from vision.camera import get_camera
        cam = get_camera()
        cam.initialize()
        faces = cam.detect_faces()
        if faces:
            return SkillResult(
                True,
                f"Detected {len(faces)} face(s), sir.",
                self.name,
                data={"faces": [f.to_dict() for f in faces]},
            )
        return SkillResult(True, "No faces detected, sir.", self.name, data={"faces": []})

    def _read_screen(self) -> SkillResult:
        """Read text from screen."""
        from vision.screen_understanding import get_screen_understanding
        su = get_screen_understanding()
        text = su.get_screen_text()
        if text:
            # Truncate for display
            display_text = text[:200] + "..." if len(text) > 200 else text
            return SkillResult(True, f"On screen, sir: {display_text}", self.name, data={"text": text})
        return SkillResult(True, "No readable text detected on screen, sir.", self.name)

    def _scan_qr(self) -> SkillResult:
        """Scan QR codes."""
        from vision.camera import get_camera
        cam = get_camera()
        cam.initialize()
        results = cam.scan_qr()
        if results:
            return SkillResult(True, f"Found {len(results)} QR code(s): {', '.join(results[:3])}", self.name, data={"results": results})
        return SkillResult(True, "No QR codes detected, sir.", self.name)

    def _analyze_environment(self) -> SkillResult:
        """Analyze the environment."""
        from vision.camera import get_camera
        cam = get_camera()
        cam.initialize()
        result = cam.analyze_environment()
        if result.get("success"):
            return SkillResult(
                True,
                f"Environment: {result.get('brightness_level', 'unknown')} lighting, "
                f"{result.get('faces_detected', 0)} face(s) detected, sir.",
                self.name,
                data=result,
            )
        return SkillResult(False, f"Analysis failed: {result.get('error', 'unknown')}", self.name, error="ANALYSIS_FAILED")
