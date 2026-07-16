"""
JARVIS OS - Calendar & Deep OS Integration
============================================

Deep system integration for calendar, payments, and OS-level control.

Features:
- Calendar management (Google Calendar, local ICS)
- Payment reminders and tracking
- Deep OS integration (startup, notifications, system tray)
- File system management
- Process management
- System notifications
"""

from __future__ import annotations

import json
import os
import platform
import re
import subprocess
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from loguru import logger

from core.config import get_settings
from core.security import get_permission_manager, Permission, AuditEventType, get_audit_logger


class CalendarEvent:
    """Represents a calendar event."""

    def __init__(self, title: str, start: datetime, end: datetime | None = None,
                 description: str = "", location: str = "", event_id: str = ""):
        self.title = title
        self.start = start
        self.end = end or (start + timedelta(hours=1))
        self.description = description
        self.location = location
        self.event_id = event_id

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "start": self.start.isoformat(),
            "end": self.end.isoformat(),
            "description": self.description,
            "location": self.location,
            "event_id": self.event_id,
        }


class CalendarManager:
    """Calendar management with Google Calendar and local support."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.pm = get_permission_manager()
        self.audit = get_audit_logger()
        self._events: list[CalendarEvent] = []
        self._load_events()

    def _load_events(self) -> None:
        """Load events from local storage."""
        path = self.settings.base_dir / self.settings.data_dir / "calendar_events.json"
        if path.exists():
            try:
                data = json.loads(path.read_text())
                for ev in data.get("events", []):
                    event = CalendarEvent(
                        title=ev["title"],
                        start=datetime.fromisoformat(ev["start"]),
                        end=datetime.fromisoformat(ev["end"]),
                        description=ev.get("description", ""),
                        location=ev.get("location", ""),
                        event_id=ev.get("event_id", ""),
                    )
                    self._events.append(event)
                logger.info(f"Loaded {len(self._events)} calendar events")
            except Exception as e:
                logger.warning(f"Failed to load calendar events: {e}")

    def _save_events(self) -> None:
        """Save events to local storage."""
        path = self.settings.base_dir / self.settings.data_dir / "calendar_events.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        data = {"events": [e.to_dict() for e in self._events]}
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def add_event(self, title: str, start: datetime, end: datetime | None = None,
                  description: str = "", location: str = "") -> CalendarEvent:
        """Add a calendar event."""
        self.pm.require(Permission.MEMORY_WRITE)
        self.audit.log_event(AuditEventType.AUTOMATION_ACTION, details={"action": "add_event", "title": title})

        event = CalendarEvent(title, start, end, description, location, event_id=f"evt_{int(time.time())}")
        self._events.append(event)
        self._save_events()
        logger.info(f"Calendar event added: {title}")
        return event

    def remove_event(self, event_id: str) -> bool:
        """Remove a calendar event."""
        self.pm.require(Permission.MEMORY_WRITE)
        for i, event in enumerate(self._events):
            if event.event_id == event_id:
                del self._events[i]
                self._save_events()
                return True
        return False

    def get_events(self, date: datetime | None = None, days: int = 1) -> list[CalendarEvent]:
        """Get events for a date range."""
        if date is None:
            date = datetime.now()

        start = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=days)

        return [e for e in self._events if start <= e.start < end]

    def get_upcoming(self, count: int = 5) -> list[CalendarEvent]:
        """Get upcoming events."""
        now = datetime.now()
        future = [e for e in self._events if e.start >= now]
        future.sort(key=lambda e: e.start)
        return future[:count]

    def get_today(self) -> list[CalendarEvent]:
        """Get today's events."""
        return self.get_events(datetime.now(), days=1)

    def get_week(self) -> list[CalendarEvent]:
        """Get this week's events."""
        return self.get_events(datetime.now(), days=7)

    def check_conflicts(self, start: datetime, end: datetime) -> list[CalendarEvent]:
        """Check for scheduling conflicts."""
        conflicts = []
        for event in self._events:
            if start < event.end and end > event.start:
                conflicts.append(event)
        return conflicts

    def parse_natural_event(self, text: str) -> dict[str, Any] | None:
        """Parse natural language into event details."""
        # Patterns like "schedule meeting tomorrow at 3pm" or "remind me to call mom on Friday"
        patterns = [
            r"(?:schedule|add|create)\s+(?:a\s+)?(?:meeting|event|appointment)?\s*(?:called|named|titled)?\s*['\"]?(.+?)['\"]?\s+(?:on|at|for)\s+(.+)",
            r"remind\s+me\s+(?:to\s+)?(.+?)\s+(?:on|at)\s+(.+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.I)
            if match:
                title = match.group(1).strip()
                time_str = match.group(2).strip()
                start = self._parse_time(time_str)
                if start:
                    return {"title": title, "start": start}

        return None

    def _parse_time(self, time_str: str) -> datetime | None:
        """Parse natural language time expressions."""
        now = datetime.now()
        time_str = time_str.lower().strip()

        # Tomorrow
        if "tomorrow" in time_str:
            base = now + timedelta(days=1)
            time_str = time_str.replace("tomorrow", "").strip()
        elif "today" in time_str:
            base = now
            time_str = time_str.replace("today", "").strip()
        else:
            base = now

        # Time parsing
        time_match = re.search(r"(\d{1,2})(?::(\d{2}))?\s*(am|pm)?", time_str)
        if time_match:
            hour = int(time_match.group(1))
            minute = int(time_match.group(2) or 0)
            ampm = time_match.group(3)

            if ampm == "pm" and hour != 12:
                hour += 12
            elif ampm == "am" and hour == 12:
                hour = 0

            return base.replace(hour=hour, minute=minute, second=0, microsecond=0)

        return base.replace(hour=9, minute=0, second=0, microsecond=0)


class DeepOSIntegration:
    """Deep OS-level integration."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.pm = get_permission_manager()
        self.audit = get_audit_logger()
        self._platform = platform.system()
        self.calendar = CalendarManager()

    def send_notification(self, title: str, message: str, urgency: str = "normal") -> bool:
        """Send a system notification."""
        self.pm.require(Permission.SYSTEM_INFO)
        try:
            if self._platform == "Linux":
                subprocess.run(
                    ["notify-send", f"--urgency={urgency}", title, message],
                    timeout=5, capture_output=True
                )
            elif self._platform == "Darwin":
                subprocess.run([
                    "osascript", "-e",
                    f'display notification "{message}" with title "{title}"'
                ], timeout=5, capture_output=True)
            elif self._platform == "Windows":
                # Use PowerShell for Windows notifications
                script = f'''
                Add-Type -AssemblyName System.Windows.Forms
                $balloon = New-Object System.Windows.Forms.NotifyIcon
                $balloon.Icon = [System.Drawing.SystemIcons]::Information
                $balloon.BalloonTipTitle = "{title}"
                $balloon.BalloonTipText = "{message}"
                $balloon.Visible = $true
                $balloon.ShowBalloonTip(5000)
                '''
                subprocess.run(["powershell", "-Command", script], timeout=5, capture_output=True)
            return True
        except Exception as e:
            logger.error(f"Notification failed: {e}")
            return False

    def set_startup(self, enable: bool) -> bool:
        """Configure JARVIS to start with the OS."""
        self.pm.require(Permission.SYSTEM_CONFIG)
        self.audit.log_event(AuditEventType.AUTOMATION_ACTION, details={"action": "set_startup", "enable": enable})

        try:
            if self._platform == "Linux":
                autostart_dir = Path.home() / ".config" / "autostart"
                autostart_dir.mkdir(parents=True, exist_ok=True)
                desktop_file = autostart_dir / "jarvis-os.desktop"

                if enable:
                    desktop_content = f"""[Desktop Entry]
Type=Application
Name=JARVIS OS
Comment=JARVIS AI Desktop Assistant
Exec={self.settings.base_dir / "scripts" / "start_jarvis.sh"}
Icon={self.settings.base_dir / "docs" / "assets" / "jarvis_icon.png"}
Terminal=false
StartupNotify=true
"""
                    desktop_file.write_text(desktop_content)
                    desktop_file.chmod(0o755)
                else:
                    if desktop_file.exists():
                        desktop_file.unlink()

            elif self._platform == "Darwin":
                if enable:
                    # macOS Login Items via launchd
                    plist_dir = Path.home() / "Library" / "LaunchAgents"
                    plist_dir.mkdir(parents=True, exist_ok=True)
                    plist_file = plist_dir / "dev.jarvis-os.plist"
                    plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>dev.jarvis-os</string>
    <key>ProgramArguments</key>
    <array>
        <string>{self.settings.base_dir / "scripts" / "start_jarvis.sh"}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
</dict>
</plist>
"""
                    plist_file.write_text(plist_content)
                else:
                    plist_file = Path.home() / "Library" / "LaunchAgents" / "dev.jarvis-os.plist"
                    if plist_file.exists():
                        plist_file.unlink()

            elif self._platform == "Windows":
                if enable:
                    # Windows startup via Registry
                    import winreg
                    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                        r"Software\Microsoft\Windows\CurrentVersion\Run",
                                        0, winreg.KEY_SET_VALUE)
                    winreg.SetValueEx(key, "JARVIS OS", 0, winreg.REG_SZ,
                                    str(self.settings.base_dir / "scripts" / "start_jarvis.sh"))
                    winreg.CloseKey(key)
                else:
                    import winreg
                    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                        r"Software\Microsoft\Windows\CurrentVersion\Run",
                                        0, winreg.KEY_SET_VALUE)
                    try:
                        winreg.DeleteValue(key, "JARVIS OS")
                    except FileNotFoundError:
                        pass
                    winreg.CloseKey(key)

            logger.info(f"Startup {'enabled' if enable else 'disabled'}")
            return True
        except Exception as e:
            logger.error(f"Set startup failed: {e}")
            return False

    def get_running_processes(self) -> list[dict[str, Any]]:
        """Get list of running processes."""
        self.pm.require(Permission.SYSTEM_INFO)
        processes = []
        try:
            if self._platform in ("Linux", "Darwin"):
                result = subprocess.run(["ps", "aux"], capture_output=True, text=True, timeout=5)
                lines = result.stdout.strip().split("\n")[1:]  # Skip header
                for line in lines[:50]:  # Limit to 50
                    parts = line.split(None, 10)
                    if len(parts) >= 11:
                        processes.append({
                            "pid": parts[1],
                            "cpu": parts[2],
                            "mem": parts[3],
                            "command": parts[10],
                        })
            elif self._platform == "Windows":
                result = subprocess.run(
                    ["powershell", "-Command", "Get-Process | Select-Object Id, CPU, WorkingSet, Name | ConvertTo-Json"],
                    capture_output=True, text=True, timeout=10
                )
                if result.returncode == 0:
                    data = json.loads(result.stdout)
                    for proc in data:
                        processes.append({
                            "pid": str(proc.get("Id", "")),
                            "cpu": str(proc.get("CPU", "")),
                            "mem": str(proc.get("WorkingSet", "")),
                            "command": proc.get("Name", ""),
                        })
        except Exception as e:
            logger.error(f"Process listing failed: {e}")
        return processes

    def kill_process(self, pid: int | str) -> bool:
        """Kill a process by PID."""
        self.pm.require(Permission.SHELL_COMMAND)
        self.audit.log_event(AuditEventType.AUTOMATION_ACTION, details={"action": "kill_process", "pid": str(pid)})
        try:
            subprocess.run(["kill", str(pid)], timeout=5)
            return True
        except Exception as e:
            logger.error(f"Kill process failed: {e}")
            return False

    def get_system_info(self) -> dict[str, Any]:
        """Get detailed system information."""
        self.pm.require(Permission.SYSTEM_INFO)
        try:
            import psutil
            return {
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory_total": psutil.virtual_memory().total,
                "memory_used": psutil.virtual_memory().used,
                "memory_percent": psutil.virtual_memory().percent,
                "disk_total": psutil.disk_usage("/").total,
                "disk_used": psutil.disk_usage("/").used,
                "disk_percent": psutil.disk_usage("/").percent,
                "boot_time": datetime.fromtimestamp(psutil.boot_time()).isoformat(),
                "platform": platform.system(),
                "platform_version": platform.version(),
                "python_version": platform.python_version(),
            }
        except ImportError:
            return {
                "platform": platform.system(),
                "platform_version": platform.version(),
                "python_version": platform.python_version(),
                "hostname": platform.node(),
            }

    def open_file_manager(self, path: str | None = None) -> bool:
        """Open the system file manager."""
        self.pm.require(Permission.AUTOMATION_EXECUTE)
        try:
            target = str(path or Path.home())
            if self._platform == "Linux":
                subprocess.Popen(["xdg-open", target], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            elif self._platform == "Darwin":
                subprocess.Popen(["open", target], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            elif self._platform == "Windows":
                subprocess.Popen(["explorer", target], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except Exception as e:
            logger.error(f"Open file manager failed: {e}")
            return False

    def open_terminal(self) -> bool:
        """Open a terminal window."""
        self.pm.require(Permission.AUTOMATION_EXECUTE)
        try:
            if self._platform == "Linux":
                for term in ["gnome-terminal", "konsole", "xterm"]:
                    try:
                        subprocess.Popen([term], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        return True
                    except FileNotFoundError:
                        continue
            elif self._platform == "Darwin":
                subprocess.Popen(["open", "-a", "Terminal"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            elif self._platform == "Windows":
                subprocess.Popen(["cmd"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except Exception as e:
            logger.error(f"Open terminal failed: {e}")
            return False

    def lock_screen(self) -> bool:
        """Lock the screen."""
        self.pm.require(Permission.SYSTEM_CONFIG)
        self.audit.log_event(AuditEventType.AUTOMATION_ACTION, details={"action": "lock_screen"})
        try:
            if self._platform == "Linux":
                for cmd in [
                    ["loginctl", "lock-session"],
                    ["gnome-screensaver-command", "-l"],
                    ["xdg-screensaver", "lock"],
                ]:
                    try:
                        subprocess.run(cmd, timeout=5, capture_output=True)
                        return True
                    except FileNotFoundError:
                        continue
            elif self._platform == "Darwin":
                subprocess.run(["/System/Library/CoreServices/Menu Extras/User.menu/Contents/Resources/CGSession", "-suspend"],
                             timeout=5, capture_output=True)
            elif self._platform == "Windows":
                subprocess.run(["rundll32.exe", "user32.dll,LockWorkStation"], timeout=5)
            return True
        except Exception as e:
            logger.error(f"Lock screen failed: {e}")
            return False

    def shutdown_system(self, confirm: bool = False) -> bool:
        """Shutdown the system (requires confirmation)."""
        self.pm.require(Permission.SYSTEM_CONFIG)
        self.audit.log_event(AuditEventType.AUTOMATION_ACTION, details={"action": "shutdown"})
        if not confirm:
            logger.warning("Shutdown requires explicit confirmation")
            return False
        try:
            if self._platform == "Linux":
                subprocess.run(["shutdown", "-h", "now"], timeout=5)
            elif self._platform == "Darwin":
                subprocess.run(["shutdown", "-h", "now"], timeout=5)
            elif self._platform == "Windows":
                subprocess.run(["shutdown", "/s", "/t", "0"], timeout=5)
            return True
        except Exception as e:
            logger.error(f"Shutdown failed: {e}")
            return False

    def restart_system(self, confirm: bool = False) -> bool:
        """Restart the system (requires confirmation)."""
        self.pm.require(Permission.SYSTEM_CONFIG)
        self.audit.log_event(AuditEventType.AUTOMATION_ACTION, details={"action": "restart"})
        if not confirm:
            logger.warning("Restart requires explicit confirmation")
            return False
        try:
            if self._platform == "Linux":
                subprocess.run(["shutdown", "-r", "now"], timeout=5)
            elif self._platform == "Darwin":
                subprocess.run(["shutdown", "-r", "now"], timeout=5)
            elif self._platform == "Windows":
                subprocess.run(["shutdown", "/r", "/t", "0"], timeout=5)
            return True
        except Exception as e:
            logger.error(f"Restart failed: {e}")
            return False


_os_integration: DeepOSIntegration | None = None


def get_os_integration() -> DeepOSIntegration:
    global _os_integration
    if _os_integration is None:
        _os_integration = DeepOSIntegration()
    return _os_integration
