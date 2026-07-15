"""
JARVIS OS - Coding Agent
========================

Intelligent code assistant with safe execution.

Features:
- Code generation via local LLM
- Syntax validation
- Sandboxed execution
"""

from __future__ import annotations

from typing import Any

from loguru import logger

from core.config import get_settings
from core.security import get_permission_manager, Permission, AuditEventType, get_audit_logger
from core.security.sandbox import Sandbox, SandboxConfig


class CodingAgent:
    """AI-powered coding assistant."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.pm = get_permission_manager()
        self.audit = get_audit_logger()

    async def generate(self, prompt: str, language: str = "python") -> str:
        self.pm.require(Permission.CODE_EXECUTE)
        self.audit.log_event(AuditEventType.AUTOMATION_ACTION, details={"action": "code_generate", "language": language})

        # In full implementation, this calls the LLM with a code-specific prompt
        return f"# Generated {language} code for: {prompt}\n# (Full implementation requires LLM code mode)"

    async def execute(self, code: str, language: str = "python") -> dict[str, Any]:
        self.pm.require(Permission.CODE_EXECUTE)
        self.audit.log_event(AuditEventType.SANDBOX_EXECUTION, details={"language": language, "code_length": len(code)})

        sandbox = Sandbox(SandboxConfig(timeout_seconds=30))
        if language == "python":
            # Write to temp file and execute via python command
            import tempfile
            import os

            temp_file = self.settings.base_dir / "temp" / "snippet.py"
            temp_file.write_text(code)
            result = await sandbox.execute_command("python", [str(temp_file)])
            return result.to_dict()
        else:
            return {"error": f"Language {language} not yet supported in sandbox"}


_coding_agent: CodingAgent | None = None


def get_coding_agent() -> CodingAgent:
    global _coding_agent
    if _coding_agent is None:
        _coding_agent = CodingAgent()
    return _coding_agent
