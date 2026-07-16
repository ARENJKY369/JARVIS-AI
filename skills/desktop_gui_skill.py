"""
JARVIS OS - Desktop GUI Automation Skill
==========================================

Full desktop control: click buttons, type text, manage windows,
find elements on screen, automate any GUI action.
"""

from __future__ import annotations

import re
from typing import Any

from loguru import logger

from core.security import Permission
from .base import Skill, SkillContext, SkillResult


class DesktopGUISkill(Skill):
    name = "desktop.gui"
    description = "Full desktop GUI automation: click, type, manage windows."
    permissions = [Permission.AUTOMATION_DESKTOP, Permission.VISION_CAPTURE]
    examples = [
        "click the OK button",
        "type hello world",
        "press enter",
        "take a screenshot",
        "find the submit button",
        "switch to chrome",
        "close this window",
        "scroll down",
    ]

    def matches(self, text: str) -> float:
        t = (text or "").lower()
        keywords = [
            "click", "type", "press", "enter", "tab",
            "screenshot", "find button", "find the",
            "switch to", "close window", "minimize",
            "maximize", "scroll", "drag", "move mouse",
            "double click", "right click", "hotkey",
            "window", "focus", "alt tab", "ctrl",
        ]
        if any(kw in t for kw in keywords):
            return 0.85
        return 0.0

    async def run(self, ctx: SkillContext) -> SkillResult:
        t = (ctx.user_text or "").lower()

        # Screenshot
        if "screenshot" in t:
            return self._screenshot(ctx)

        # Click element
        if "click" in t:
            return self._click_element(t, ctx)

        # Type text
        if "type" in t:
            return self._type_text(t, ctx)

        # Press key
        if "press" in t:
            return self._press_key(t, ctx)

        # Window management
        if any(w in t for w in ["switch to", "focus", "close window", "minimize", "maximize"]):
            return self._window_management(t, ctx)

        # Scroll
        if "scroll" in t:
            return self._scroll(t, ctx)

        # Find element
        if "find" in t:
            return self._find_element(t, ctx)

        return SkillResult(False, "What desktop action would you like, sir?", self.name, error="UNKNOWN")

    def _screenshot(self, ctx: SkillContext) -> SkillResult:
        """Take a screenshot."""
        from automation.desktop import get_desktop_gui
        gui = get_desktop_gui()
        try:
            path = gui.capture_screenshot()
            return SkillResult(True, f"Screenshot captured, sir. Saved to {path}.", self.name, data={"path": path})
        except Exception as e:
            return SkillResult(False, f"Screenshot failed: {e}", self.name, error=str(e))

    def _click_element(self, text: str, ctx: SkillContext) -> SkillResult:
        """Click an element on screen."""
        from vision.screen_understanding import get_screen_understanding
        su = get_screen_understanding()

        # Extract element to click
        element_text = self._extract_target(text)
        if element_text:
            element = su.find_element(element_text)
            if element:
                from automation.desktop import get_desktop_gui
                gui = get_desktop_gui()
                cx, cy = element.center()
                if not ctx.dry_run:
                    gui.click_at(cx, cy)
                return SkillResult(True, f"Clicked '{element_text}' at ({cx}, {cy}), sir.", self.name, data={"x": cx, "y": cy})
            return SkillResult(False, f"Could not find '{element_text}' on screen, sir.", self.name, error="NOT_FOUND")

        # Click at coordinates
        coord_match = re.search(r"(\d+)\s*,\s*(\d+)", text)
        if coord_match:
            x, y = int(coord_match.group(1)), int(coord_match.group(2))
            from automation.desktop import get_desktop_gui
            gui = get_desktop_gui()
            if not ctx.dry_run:
                gui.click_at(x, y)
            return SkillResult(True, f"Clicked at ({x}, {y}), sir.", self.name)

        return SkillResult(False, "What should I click, sir? Specify a button name or coordinates.", self.name, error="NO_TARGET")

    def _type_text(self, text: str, ctx: SkillContext) -> SkillResult:
        """Type text."""
        # Extract text to type
        match = re.search(r"type\s+['\"]?(.+?)['\"]?$", text, re.I)
        if match:
            text_to_type = match.group(1).strip()
            from automation.desktop import get_desktop_gui
            gui = get_desktop_gui()
            if not ctx.dry_run:
                gui.type_text(text_to_type)
            return SkillResult(True, f"Typed '{text_to_type}', sir.", self.name)
        return SkillResult(False, "What should I type, sir?", self.name, error="NO_TEXT")

    def _press_key(self, text: str, ctx: SkillContext) -> SkillResult:
        """Press a key or key combination."""
        from automation.desktop import get_desktop_gui
        gui = get_desktop_gui()

        # Hotkey combinations
        if "alt" in text and "tab" in text:
            if not ctx.dry_run:
                gui.hotkey("alt", "tab")
            return SkillResult(True, "Alt+Tab pressed, sir.", self.name)
        if "ctrl" in text and "c" in text:
            if not ctx.dry_run:
                gui.hotkey("ctrl", "c")
            return SkillResult(True, "Ctrl+C pressed, sir.", self.name)
        if "ctrl" in text and "v" in text:
            if not ctx.dry_run:
                gui.hotkey("ctrl", "v")
            return SkillResult(True, "Ctrl+V pressed, sir.", self.name)

        # Single key
        key_match = re.search(r"press\s+(\w+)", text, re.I)
        if key_match:
            key = key_match.group(1).lower()
            if not ctx.dry_run:
                gui.press_key(key)
            return SkillResult(True, f"Pressed '{key}', sir.", self.name)

        return SkillResult(False, "Which key should I press, sir?", self.name, error="NO_KEY")

    def _window_management(self, text: str, ctx: SkillContext) -> SkillResult:
        """Manage windows."""
        from automation.desktop import get_desktop_gui
        gui = get_desktop_gui()

        if "switch to" in text or "focus" in text:
            match = re.search(r"(?:switch to|focus)\s+(.+)$", text, re.I)
            if match:
                title = match.group(1).strip()
                if not ctx.dry_run:
                    gui.focus_window(title)
                return SkillResult(True, f"Switched to '{title}', sir.", self.name)

        if "close" in text:
            match = re.search(r"close\s+(?:the\s+)?(.+)$", text, re.I)
            if match:
                title = match.group(1).strip()
                if not ctx.dry_run:
                    gui.close_window(title)
                return SkillResult(True, f"Closed '{title}', sir.", self.name)

        if "minimize" in text:
            match = re.search(r"minimize\s+(?:the\s+)?(.+)$", text, re.I)
            if match:
                title = match.group(1).strip()
                if not ctx.dry_run:
                    gui.minimize_window(title)
                return SkillResult(True, f"Minimized '{title}', sir.", self.name)

        return SkillResult(False, "Which window should I manage, sir?", self.name, error="NO_WINDOW")

    def _scroll(self, text: str, ctx: SkillContext) -> SkillResult:
        """Scroll the screen."""
        from automation.desktop import get_desktop_gui
        gui = get_desktop_gui()

        direction = -1 if "down" in text else 1
        clicks = 3
        match = re.search(r"scroll\s+\w+\s+(\d+)", text, re.I)
        if match:
            clicks = int(match.group(1))

        if not ctx.dry_run:
            gui.scroll(clicks * direction)
        return SkillResult(True, f"Scrolled {'down' if direction < 0 else 'up'}, sir.", self.name)

    def _find_element(self, text: str, ctx: SkillContext) -> SkillResult:
        """Find an element on screen."""
        from vision.screen_understanding import get_screen_understanding
        su = get_screen_understanding()

        target = self._extract_target(text)
        if target:
            element = su.find_element(target)
            if element:
                return SkillResult(
                    True,
                    f"Found '{target}' at ({element.x}, {element.y}), sir.",
                    self.name,
                    data=element.to_dict(),
                )
            return SkillResult(False, f"Could not find '{target}' on screen, sir.", self.name, error="NOT_FOUND")

        return SkillResult(False, "What should I find, sir?", self.name, error="NO_TARGET")

    def _extract_target(self, text: str) -> str | None:
        """Extract target element name from text."""
        patterns = [
            r"(?:click|find|the)\s+(?:the\s+)?(\w+)\s+button",
            r"(?:click|find)\s+(?:the\s+)?(.+?)(?:\s+button)?$",
            r"(?:the\s+)?(\w+)\s+button",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.I)
            if match:
                return match.group(1).strip()
        return None
