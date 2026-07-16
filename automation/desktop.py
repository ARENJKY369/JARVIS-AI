"""
JARVIS OS - Desktop Automation
==============================

Safe, sandboxed desktop interactions.

Features:
- Mouse/keyboard control
- Screenshot capture
- Application launching (sandboxed)
"""

from __future__ import annotations

from typing import Any

from loguru import logger

from core.config import get_settings
from core.security import get_permission_manager, Permission, AuditEventType, get_audit_logger


class DesktopAutomation:
    """Controlled desktop automation interface."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.pm = get_permission_manager()
        self.audit = get_audit_logger()

    def capture_screenshot(self) -> str:
        self.pm.require(Permission.VISION_CAPTURE)
        self.audit.log_event(AuditEventType.AUTOMATION_ACTION, details={"action": "screenshot"})

        try:
            import pyautogui
            path = self.settings.base_dir / "temp" / "screenshot.png"
            pyautogui.screenshot(str(path))
            logger.info(f"Screenshot saved: {path}")
            return str(path)
        except Exception as e:
            logger.error(f"Screenshot failed: {e}")
            raise

    def type_text(self, text: str, interval: float = 0.01) -> None:
        self.pm.require(Permission.AUTOMATION_DESKTOP)
        self.audit.log_event(AuditEventType.AUTOMATION_ACTION, details={"action": "type_text", "length": len(text)})

        try:
            import pyautogui
            pyautogui.typewrite(text, interval=interval)
        except Exception as e:
            logger.error(f"Type text failed: {e}")
            raise

    def click(self, x: int, y: int) -> None:
        self.pm.require(Permission.AUTOMATION_DESKTOP)
        self.audit.log_event(AuditEventType.AUTOMATION_ACTION, details={"action": "click", "x": x, "y": y})

        try:
            import pyautogui
            pyautogui.click(x, y)
        except Exception as e:
            logger.error(f"Click failed: {e}")
            raise


_desktop: DesktopAutomation | None = None


def get_desktop_automation() -> DesktopAutomation:
    global _desktop
    if _desktop is None:
        _desktop = DesktopAutomation()
    return _desktop
