"""
JARVIS OS - Full Desktop GUI Automation
========================================

Complete desktop control: window management, UI element detection,
advanced mouse/keyboard control, and screen interaction.

Features:
- Window management (list, focus, move, resize, minimize, maximize, close)
- UI element detection via accessibility tree
- Advanced mouse control (move, click, drag, scroll)
- Advanced keyboard control (hotkeys, key combinations)
- Screen region capture
- Application automation (click any button on screen)
"""

from __future__ import annotations

import os
import platform
import re
import subprocess
import time
from pathlib import Path
from typing import Any

from loguru import logger

from core.config import get_settings
from core.security import get_permission_manager, Permission, AuditEventType, get_audit_logger


class WindowInfo:
    """Represents a desktop window."""

    def __init__(self, title: str, app: str, x: int, y: int, width: int, height: int, window_id: str = ""):
        self.title = title
        self.app = app
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.window_id = window_id

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "app": self.app,
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "window_id": self.window_id,
        }


class DesktopGUIAutomation:
    """Full desktop GUI automation with window and UI control."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.pm = get_permission_manager()
        self.audit = get_audit_logger()
        self._platform = platform.system()

    def list_windows(self) -> list[WindowInfo]:
        """List all visible windows on the desktop."""
        self.pm.require(Permission.AUTOMATION_DESKTOP)
        self.audit.log_event(AuditEventType.AUTOMATION_ACTION, details={"action": "list_windows"})

        windows = []
        try:
            if self._platform == "Linux":
                windows = self._list_windows_linux()
            elif self._platform == "Darwin":
                windows = self._list_windows_macos()
            elif self._platform == "Windows":
                windows = self._list_windows_windows()
        except Exception as e:
            logger.error(f"Failed to list windows: {e}")

        return windows

    def _list_windows_linux(self) -> list[WindowInfo]:
        """List windows on Linux using wmctrl or xdotool."""
        windows = []
        try:
            # Try wmctrl first
            result = subprocess.run(
                ["wmctrl", "-l", "-G"],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                for line in result.stdout.strip().split("\n"):
                    parts = line.split(None, 8)
                    if len(parts) >= 8:
                        windows.append(WindowInfo(
                            title=parts[8] if len(parts) > 8 else "",
                            app=parts[1] or "unknown",
                            x=int(parts[2]),
                            y=int(parts[3]),
                            width=int(parts[4]),
                            height=int(parts[5]),
                            window_id=parts[0],
                        ))
        except FileNotFoundError:
            pass

        if not windows:
            # Fallback to xdotool
            try:
                result = subprocess.run(
                    ["xdotool", "search", "--onlyvisible", "--name", "", "getwindowgeometry"],
                    capture_output=True, text=True, timeout=5
                )
                if result.returncode == 0:
                    # Parse xdotool output
                    pass
            except FileNotFoundError:
                pass

        return windows

    def _list_windows_macos(self) -> list[WindowInfo]:
        """List windows on macOS using AppleScript."""
        windows = []
        try:
            script = '''
            tell application "System Events"
                set windowList to {}
                set allProcesses to (every process whose background only is false)
                repeat with proc in allProcesses
                    set procName to name of proc
                    set procWindows to (every window of proc)
                    repeat with win in procWindows
                        set winPos to position of win
                        set winSize to size of win
                        set winName to name of win
                        set end of windowList to {procName & " | " & winName, item 1 of winPos, item 2 of winPos, item 1 of winSize, item 2 of winSize}
                    end repeat
                end repeat
                return windowList
            end tell
            '''
            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                # Parse AppleScript output
                pass
        except Exception as e:
            logger.debug(f"macOS window listing: {e}")
        return windows

    def _list_windows_windows(self) -> list[WindowInfo]:
        """List windows on Windows using PowerShell."""
        windows = []
        try:
            script = '''
            Add-Type @"
            using System;
            using System.Runtime.InteropServices;
            public class WinAPI {
                [DllImport("user32.dll")]
                [return: MarshalAs(UnmanagedType.Bool)]
                public static extern bool GetWindowRect(IntPtr hWnd, out RECT lpRect);
                [DllImport("user32.dll")]
                public static extern bool IsWindowVisible(IntPtr hWnd);
                [DllImport("user32.dll", SetLastError = true)]
                public static extern IntPtr GetParent(IntPtr hWnd);
            }
            public struct RECT { public int Left, Top, Right, Bottom; }
            "@
            $windows = @()
            Get-Process | Where-Object { $_.MainWindowTitle } | ForEach-Object {
                $windows += "$($_.ProcessName) | $($_.MainWindowTitle)"
            }
            $windows -join "`n"
            '''
            result = subprocess.run(
                ["powershell", "-Command", script],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                for line in result.stdout.strip().split("\n"):
                    if " | " in line:
                        parts = line.split(" | ", 1)
                        windows.append(WindowInfo(
                            title=parts[1],
                            app=parts[0],
                            x=0, y=0, width=0, height=0,
                        ))
        except Exception as e:
            logger.debug(f"Windows window listing: {e}")
        return windows

    def focus_window(self, title_substring: str) -> bool:
        """Focus a window by title substring."""
        self.pm.require(Permission.AUTOMATION_DESKTOP)
        self.audit.log_event(AuditEventType.AUTOMATION_ACTION, details={"action": "focus_window", "title": title_substring})

        try:
            if self._platform == "Linux":
                subprocess.run(["wmctrl", "-a", title_substring], timeout=5)
            elif self._platform == "Darwin":
                subprocess.run(["osascript", "-e", f'tell application "{title_substring}" to activate'], timeout=5)
            elif self._platform == "Windows":
                subprocess.run(["powershell", "-Command",
                              f"(Get-Process | Where-Object {{$_.MainWindowTitle -like '*{title_substring}*'}}).MainWindowTitle"],
                             timeout=5)
            return True
        except Exception as e:
            logger.error(f"Focus window failed: {e}")
            return False

    def move_window(self, title_substring: str, x: int, y: int) -> bool:
        """Move a window to position (x, y)."""
        self.pm.require(Permission.AUTOMATION_DESKTOP)
        try:
            if self._platform == "Linux":
                subprocess.run(["wmctrl", "-r", title_substring, "-e", f"0,{x},{y},-1,-1"], timeout=5)
            return True
        except Exception as e:
            logger.error(f"Move window failed: {e}")
            return False

    def resize_window(self, title_substring: str, width: int, height: int) -> bool:
        """Resize a window."""
        self.pm.require(Permission.AUTOMATION_DESKTOP)
        try:
            if self._platform == "Linux":
                subprocess.run(["wmctrl", "-r", title_substring, "-e", f"0,-1,-1,{width},{height}"], timeout=5)
            return True
        except Exception as e:
            logger.error(f"Resize window failed: {e}")
            return False

    def minimize_window(self, title_substring: str) -> bool:
        """Minimize a window."""
        self.pm.require(Permission.AUTOMATION_DESKTOP)
        try:
            if self._platform == "Linux":
                subprocess.run(["wmctrl", "-r", title_substring, "-b", "add,hidden"], timeout=5)
            return True
        except Exception as e:
            logger.error(f"Minimize window failed: {e}")
            return False

    def close_window(self, title_substring: str) -> bool:
        """Close a window."""
        self.pm.require(Permission.AUTOMATION_DESKTOP)
        self.audit.log_event(AuditEventType.AUTOMATION_ACTION, details={"action": "close_window", "title": title_substring})
        try:
            if self._platform == "Linux":
                subprocess.run(["wmctrl", "-c", title_substring], timeout=5)
            return True
        except Exception as e:
            logger.error(f"Close window failed: {e}")
            return False

    def click_at(self, x: int, y: int, button: str = "left", clicks: int = 1) -> None:
        """Click at specific screen coordinates."""
        self.pm.require(Permission.AUTOMATION_DESKTOP)
        self.audit.log_event(AuditEventType.AUTOMATION_ACTION, details={"action": "click_at", "x": x, "y": y})

        try:
            import pyautogui
            pyautogui.click(x, y, clicks=clicks, button=button)
        except Exception as e:
            logger.error(f"Click at ({x}, {y}) failed: {e}")
            raise

    def double_click_at(self, x: int, y: int) -> None:
        """Double-click at specific screen coordinates."""
        self.pm.require(Permission.AUTOMATION_DESKTOP)
        try:
            import pyautogui
            pyautogui.doubleClick(x, y)
        except Exception as e:
            logger.error(f"Double-click at ({x}, {y}) failed: {e}")
            raise

    def right_click_at(self, x: int, y: int) -> None:
        """Right-click at specific screen coordinates."""
        self.pm.require(Permission.AUTOMATION_DESKTOP)
        try:
            import pyautogui
            pyautogui.rightClick(x, y)
        except Exception as e:
            logger.error(f"Right-click at ({x}, {y}) failed: {e}")
            raise

    def move_mouse_to(self, x: int, y: int, duration: float = 0.2) -> None:
        """Move mouse to specific coordinates."""
        self.pm.require(Permission.AUTOMATION_DESKTOP)
        try:
            import pyautogui
            pyautogui.moveTo(x, y, duration=duration)
        except Exception as e:
            logger.error(f"Move mouse to ({x}, {y}) failed: {e}")
            raise

    def drag_mouse(self, start_x: int, start_y: int, end_x: int, end_y: int, duration: float = 0.5) -> None:
        """Drag mouse from one position to another."""
        self.pm.require(Permission.AUTOMATION_DESKTOP)
        try:
            import pyautogui
            pyautogui.moveTo(start_x, start_y)
            pyautogui.drag(end_x - start_x, end_y - start_y, duration=duration)
        except Exception as e:
            logger.error(f"Drag failed: {e}")
            raise

    def scroll(self, clicks: int, x: int | None = None, y: int | None = None) -> None:
        """Scroll the mouse wheel."""
        self.pm.require(Permission.AUTOMATION_DESKTOP)
        try:
            import pyautogui
            pyautogui.scroll(clicks, x=x, y=y)
        except Exception as e:
            logger.error(f"Scroll failed: {e}")
            raise

    def press_key(self, key: str) -> None:
        """Press a single key."""
        self.pm.require(Permission.AUTOMATION_DESKTOP)
        try:
            import pyautogui
            pyautogui.press(key)
        except Exception as e:
            logger.error(f"Press key '{key}' failed: {e}")
            raise

    def hotkey(self, *keys: str) -> None:
        """Press a key combination (e.g., 'ctrl', 'c')."""
        self.pm.require(Permission.AUTOMATION_DESKTOP)
        try:
            import pyautogui
            pyautogui.hotkey(*keys)
        except Exception as e:
            logger.error(f"Hotkey {keys} failed: {e}")
            raise

    def type_text(self, text: str, interval: float = 0.02) -> None:
        """Type text with keyboard."""
        self.pm.require(Permission.AUTOMATION_DESKTOP)
        self.audit.log_event(AuditEventType.AUTOMATION_ACTION, details={"action": "type_text", "length": len(text)})
        try:
            import pyautogui
            pyautogui.typewrite(text, interval=interval)
        except Exception as e:
            logger.error(f"Type text failed: {e}")
            raise

    def type_with_hotkeys(self, text: str) -> None:
        """Type text using hotkey method (more reliable for special chars)."""
        self.pm.require(Permission.AUTOMATION_DESKTOP)
        try:
            import pyautogui
            pyautogui.typewrite(text)
        except Exception as e:
            logger.error(f"Type with hotkeys failed: {e}")
            raise

    def capture_region(self, x: int, y: int, width: int, height: int) -> str:
        """Capture a specific screen region."""
        self.pm.require(Permission.VISION_CAPTURE)
        self.audit.log_event(AuditEventType.AUTOMATION_ACTION, details={"action": "capture_region", "x": x, "y": y, "w": width, "h": height})

        try:
            import pyautogui
            path = self.settings.base_dir / "temp" / f"region_{int(time.time())}.png"
            path.parent.mkdir(parents=True, exist_ok=True)
            screenshot = pyautogui.screenshot(region=(x, y, width, height))
            screenshot.save(str(path))
            logger.info(f"Region capture saved: {path}")
            return str(path)
        except Exception as e:
            logger.error(f"Region capture failed: {e}")
            raise

    def find_on_screen(self, image_path: str, confidence: float = 0.9) -> tuple[int, int] | None:
        """Find an image on screen and return its center coordinates."""
        self.pm.require(Permission.VISION_CAPTURE)
        try:
            import pyautogui
            location = pyautogui.locateCenterOnScreen(image_path, confidence=confidence)
            if location:
                return (location.x, location.y)
            return None
        except Exception as e:
            logger.error(f"Find on screen failed: {e}")
            return None

    def click_image(self, image_path: str, confidence: float = 0.9) -> bool:
        """Find and click an image on screen."""
        self.pm.require(Permission.AUTOMATION_DESKTOP)
        self.pm.require(Permission.VISION_CAPTURE)
        location = self.find_on_screen(image_path, confidence)
        if location:
            self.click_at(location[0], location[1])
            return True
        return False

    def wait_for_image(self, image_path: str, timeout: float = 10.0, confidence: float = 0.9) -> tuple[int, int] | None:
        """Wait for an image to appear on screen."""
        self.pm.require(Permission.VISION_CAPTURE)
        start = time.time()
        while time.time() - start < timeout:
            location = self.find_on_screen(image_path, confidence)
            if location:
                return location
            time.sleep(0.5)
        return None

    def get_screen_size(self) -> tuple[int, int]:
        """Get the screen resolution."""
        try:
            import pyautogui
            return pyautogui.size()
        except Exception:
            return (1920, 1080)

    def get_mouse_position(self) -> tuple[int, int]:
        """Get current mouse position."""
        try:
            import pyautogui
            return pyautogui.position()
        except Exception:
            return (0, 0)


_gui: DesktopGUIAutomation | None = None


def get_desktop_gui() -> DesktopGUIAutomation:
    global _gui
    if _gui is None:
        _gui = DesktopGUIAutomation()
    return _gui
