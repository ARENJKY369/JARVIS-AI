"""
JARVIS OS - Calendar & Scheduling Skill
=========================================

Manage calendar events, reminders, and scheduling.
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta
from typing import Any

from loguru import logger

from core.security import Permission
from .base import Skill, SkillContext, SkillResult


class CalendarSkill(Skill):
    name = "calendar.manage"
    description = "Manage calendar events, reminders, and scheduling."
    permissions = [Permission.MEMORY_WRITE, Permission.MEMORY_READ]
    examples = [
        "schedule meeting tomorrow at 3pm",
        "what's on my calendar today",
        "add event called team standup at 9am",
        "remind me to call mom on Friday",
        "show this week's schedule",
        "cancel my 3pm meeting",
    ]

    def matches(self, text: str) -> float:
        t = (text or "").lower()
        keywords = [
            "schedule", "calendar", "event", "meeting", "remind",
            "appointment", "agenda", "plan", "what's on",
            "what is on", "upcoming", "today's schedule",
        ]
        if any(kw in t for kw in keywords):
            return 0.9
        return 0.0

    async def run(self, ctx: SkillContext) -> SkillResult:
        t = (ctx.user_text or "").lower()

        # View events
        if any(w in t for w in ["what's on", "what is on", "show", "view", "upcoming", "schedule"]):
            return self._view_events(t)

        # Cancel event
        if any(w in t for w in ["cancel", "delete", "remove"]):
            return self._cancel_event(t)

        # Add event
        return self._add_event(t)

    def _view_events(self, text: str) -> SkillResult:
        """View calendar events."""
        from automation.os_integration import get_os_integration
        cal = get_os_integration().calendar

        if "today" in text:
            events = cal.get_today()
            period = "today"
        elif "week" in text:
            events = cal.get_week()
            period = "this week"
        elif "tomorrow" in text:
            events = cal.get_events(datetime.now() + timedelta(days=1), days=1)
            period = "tomorrow"
        else:
            events = cal.get_upcoming(5)
            period = "upcoming"

        if not events:
            return SkillResult(True, f"Your calendar is clear for {period}, sir.", self.name, data={"events": []})

        event_list = []
        for ev in events:
            event_list.append(f"• {ev.title} at {ev.start.strftime('%I:%M %p')}")

        return SkillResult(
            True,
            f"{period.title()} you have {len(events)} event(s), sir:\n" + "\n".join(event_list),
            self.name,
            data={"events": [e.to_dict() for e in events]},
        )

    def _add_event(self, text: str) -> SkillResult:
        """Add a calendar event."""
        from automation.os_integration import get_os_integration
        cal = get_os_integration().calendar

        # Parse natural language
        parsed = cal.parse_natural_event(text)
        if parsed:
            event = cal.add_event(
                title=parsed["title"],
                start=parsed["start"],
            )
            return SkillResult(
                True,
                f"Scheduled '{event.title}' for {event.start.strftime('%A at %I:%M %p')}, sir.",
                self.name,
                data=event.to_dict(),
            )

        # Manual parsing fallback
        title_match = re.search(r"(?:called|named|titled)\s+['\"]?(.+?)['\"]?\s+(?:at|on)", text, re.I)
        time_match = re.search(r"(?:at|on)\s+(.+)$", text, re.I)

        if title_match and time_match:
            title = title_match.group(1).strip()
            start = cal._parse_time(time_match.group(1))
            if start:
                event = cal.add_event(title=title, start=start)
                return SkillResult(
                    True,
                    f"Scheduled '{event.title}' for {event.start.strftime('%A at %I:%M %p')}, sir.",
                    self.name,
                    data=event.to_dict(),
                )

        return SkillResult(False, "I couldn't parse that event, sir. Try: 'schedule meeting tomorrow at 3pm'", self.name, error="PARSE_ERROR")

    def _cancel_event(self, text: str) -> SkillResult:
        """Cancel an event."""
        from automation.os_integration import get_os_integration
        cal = get_os_integration().calendar

        # Find event to cancel
        events = cal.get_upcoming(10)
        for event in events:
            if event.title.lower() in text.lower():
                cal.remove_event(event.event_id)
                return SkillResult(True, f"Cancelled '{event.title}', sir.", self.name)

        return SkillResult(False, "I couldn't find that event to cancel, sir.", self.name, error="NOT_FOUND")


class ReminderSkill(Skill):
    name = "calendar.reminder"
    description = "Set reminders and alarms."
    permissions = [Permission.MEMORY_WRITE]
    examples = [
        "remind me to check email in 10 minutes",
        "set a reminder for 5pm",
        "remind me about the meeting tomorrow",
    ]

    def matches(self, text: str) -> float:
        t = (text or "").lower()
        if re.search(r"\bremind\s+me\b", t):
            return 0.92
        return 0.0

    async def run(self, ctx: SkillContext) -> SkillResult:
        t = ctx.user_text or ""

        # Parse reminder
        match = re.search(r"remind\s+me\s+(?:to\s+)?(.+?)\s+(?:in|at)\s+(.+)$", t, re.I)
        if match:
            task = match.group(1).strip()
            time_str = match.group(2).strip()

            from automation.os_integration import get_os_integration
            cal = get_os_integration().calendar

            # Parse time
            start = cal._parse_time(time_str)
            if not start:
                # Try relative time
                rel_match = re.search(r"(\d+)\s*(minutes?|hours?|mins?|hrs?)", time_str, re.I)
                if rel_match:
                    n = int(rel_match.group(1))
                    unit = rel_match.group(2).lower()
                    if unit.startswith("min"):
                        start = datetime.now() + timedelta(minutes=n)
                    else:
                        start = datetime.now() + timedelta(hours=n)

            if start:
                event = cal.add_event(title=f"Reminder: {task}", start=start)
                return SkillResult(
                    True,
                    f"Reminder set, sir. I'll remind you to {task} at {start.strftime('%I:%M %p')}.",
                    self.name,
                    data=event.to_dict(),
                )

        return SkillResult(False, "I couldn't parse that reminder, sir. Try: 'remind me to call mom in 10 minutes'", self.name, error="PARSE_ERROR")
