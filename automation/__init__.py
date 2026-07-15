"""
JARVIS OS - Automation Engine
=============================

Safe desktop and browser automation.

Components:
- Desktop automation (PyAutoGUI)
- Browser automation (Playwright)
"""

from .desktop import DesktopAutomation, get_desktop_automation

__all__ = ["DesktopAutomation", "get_desktop_automation"]
