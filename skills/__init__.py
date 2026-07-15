"""
JARVIS OS - Skills Package
==========================

Skills are discrete, permission-gated abilities JARVIS can perform
from a single voice or text command.

Example:
    "Open YouTube"  → skills.browser.open_url
    "Open VS Code"  → skills.apps.launch
"""

from .base import Skill, SkillResult, SkillContext
from .registry import SkillRegistry, get_skill_registry

__all__ = [
    "Skill",
    "SkillResult",
    "SkillContext",
    "SkillRegistry",
    "get_skill_registry",
]
