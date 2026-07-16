"""
JARVIS OS - Smart Home Skill
=============================

Control IoT devices, lights, switches, and scenes.
"""

from __future__ import annotations

import re
from typing import Any

from loguru import logger

from core.security import Permission
from .base import Skill, SkillContext, SkillResult


class SmartHomeSkill(Skill):
    name = "smart_home.control"
    description = "Control smart home devices: lights, switches, scenes."
    permissions = [Permission.AUTOMATION_EXECUTE]
    examples = [
        "turn on the living room light",
        "turn off bedroom light",
        "set kitchen light to 50%",
        "activate movie scene",
        "turn on the fan",
        "smart home status",
    ]

    def matches(self, text: str) -> float:
        t = (text or "").lower()
        # Use word-boundary matching to avoid false positives (e.g., "ac" matching "black")
        keywords = [
            "turn on", "turn off", "switch on", "switch off",
            "light", "lamp", "bulb", "fan", "thermostat",
            "scene", "brightness", "dim", "smart home", "iot",
            "living room", "bedroom", "kitchen", "bathroom",
        ]
        # Check multi-word phrases first (substring match is fine)
        multi_word = ["turn on", "turn off", "switch on", "switch off", "smart home", "living room", "bedroom", "kitchen", "bathroom"]
        for kw in multi_word:
            if kw in t:
                return 0.88
        # Check single words with word boundaries
        words = set(re.findall(r'\b\w+\b', t))
        single_word = {"light", "lamp", "bulb", "fan", "thermostat", "scene", "brightness", "dim", "iot"}
        if words & single_word:
            return 0.88
        # Special handling for "ac" (air conditioning) - only match as standalone word
        if re.search(r'\bac\b', t) or re.search(r'\bair con', t) or re.search(r'\baircondition', t):
            return 0.88
        return 0.0

    async def run(self, ctx: SkillContext) -> SkillResult:
        t = (ctx.user_text or "").lower()

        # Status check
        if "status" in t:
            from automation.smart_home import get_smart_home
            sh = get_smart_home()
            status = sh.get_status()
            return SkillResult(
                True,
                f"Smart home status: {status['total_devices']} devices. "
                f"{status['lights']} lights, {status['switches']} switches, "
                f"{status['sensors']} sensors, sir.",
                self.name,
                data=status,
            )

        # Scene activation
        scene_match = re.search(r"activate\s+(?:the\s+)?(.+)\s+scene", t)
        if scene_match:
            scene_name = scene_match.group(1).strip()
            from automation.smart_home import get_smart_home
            sh = get_smart_home()
            result = sh.activate_scene(scene_name)
            if result.get("success"):
                return SkillResult(True, f"Scene '{scene_name}' activated, sir.", self.name, data=result)
            return SkillResult(False, f"Could not activate scene '{scene_name}', sir.", self.name, error="SCENE_FAILED")

        # Light control
        action = None
        if any(w in t for w in ["turn on", "switch on"]):
            action = "on"
        elif any(w in t for w in ["turn off", "switch off"]):
            action = "off"
        elif "brightness" in t or "%" in t or "dim" in t:
            action = "brightness"
        elif "toggle" in t:
            action = "toggle"

        if action:
            # Extract device name
            device_name = self._extract_device_name(t)
            if not device_name:
                return SkillResult(False, "Which device shall I control, sir?", self.name, error="NO_DEVICE")

            from automation.smart_home import get_smart_home
            sh = get_smart_home()

            if action == "brightness":
                brightness = self._extract_brightness(t)
                result = sh.control_light(device_name, "brightness", brightness=brightness)
            else:
                result = sh.control_light(device_name, action)

            if result.get("success"):
                return SkillResult(True, f"Done, sir. {device_name} turned {action}.", self.name, data=result)
            return SkillResult(False, f"Could not control {device_name}, sir. ({result.get('error', 'unknown')})", self.name, error="CONTROL_FAILED")

        return SkillResult(False, "What would you like me to control, sir?", self.name, error="UNKNOWN")

    def _extract_device_name(self, text: str) -> str | None:
        """Extract device name from text."""
        patterns = [
            r"(?:the\s+)?(?:living room|bedroom|kitchen|bathroom|office|garage|hallway)\s+(?:light|lamp|fan|switch)",
            r"(?:the\s+)?(\w+)\s+(?:light|lamp|fan|switch)",
            r"(?:light|lamp|fan|switch)\s+(?:in\s+)?(?:the\s+)?(\w+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.I)
            if match:
                return match.group(0).strip()
        # Generic extraction
        for word in text.split():
            if word not in ["turn", "on", "off", "the", "to", "set", "switch", "toggle", "brightness", "dim", "%", "of"]:
                return word
        return None

    def _extract_brightness(self, text: str) -> int:
        """Extract brightness percentage."""
        match = re.search(r"(\d+)\s*%", text)
        if match:
            return int(match.group(1)) * 255 // 100
        if "full" in text or "max" in text:
            return 255
        if "half" in text:
            return 128
        if "low" in text or "dim" in text:
            return 50
        return 128
