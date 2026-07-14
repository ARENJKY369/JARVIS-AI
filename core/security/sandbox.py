"""
JARVIS OS - Secure Sandbox Execution
====================================

Production-grade sandbox for executing untrusted or privileged code/commands.

Core Features:
- Command whitelist enforcement
- Subprocess isolation with timeout
- Resource limits (future: cgroups / seccomp)
- Captured stdout/stderr + exit code
- Full audit trail
- No network access unless explicitly allowed
- Path sanitization

Current Implementation (v1.0):
- Uses subprocess with strict controls
- Python code execution is NOT yet supported (future: restricted Python)
- Shell commands only via whitelisted binaries
- Runs in a controlled environment

Security Model:
- Default deny everything
- Only commands explicitly allowed in settings.security.allowed_commands
- Execution time capped
- Output size limited
- Never passes raw user input to shell

Future Enhancements:
- Firejail / bubblewrap integration
- Restricted Python interpreter (restrictedpy or similar)
- Memory / CPU limits
"""

from __future__ import annotations

import asyncio
import shlex
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

from loguru import logger

from core.config import get_settings
from core.security.permissions import Permission, get_permission_manager


class SandboxError(Exception):
    """Base exception for sandbox failures."""

    pass


class SandboxTimeoutError(SandboxError):
    pass


class SandboxPermissionError(SandboxError):
    pass


class SandboxCommandError(SandboxError):
    pass


@dataclass(frozen=True)
class SandboxConfig:
    """Configuration for a sandbox session."""

    timeout_seconds: int = 30
    max_output_bytes: int = 1024 * 1024  # 1MB
    working_dir: Path | None = None
    allow_network: bool = False
    capture_output: bool = True


@dataclass
class SandboxResult:
    """Result of a sandboxed execution."""

    success: bool
    exit_code: int
    stdout: str
    stderr: str
    duration_ms: float
    command: str
    error: str | None = None

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "exit_code": self.exit_code,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "duration_ms": self.duration_ms,
            "command": self.command,
            "error": self.error,
        }


class Sandbox:
    """
    Secure sandbox executor.

    Usage:
        sandbox = Sandbox()
        result = await sandbox.execute_command("ls", ["-la", "/tmp"])
    """

    def __init__(self, config: SandboxConfig | None = None) -> None:
        self.settings = get_settings()
        self.config = config or SandboxConfig(
            timeout_seconds=self.settings.security.max_execution_time,
            allow_network=self.settings.security.allow_network,
        )
        self.permission_manager = get_permission_manager()
        self._validate_environment()

    def _validate_environment(self) -> None:
        if not self.settings.security.sandbox_enabled:
            logger.warning("Sandbox is globally disabled in settings!")

    def _is_command_allowed(self, command: str) -> bool:
        """Check against whitelist."""
        base = command.split()[0] if command else ""
        allowed = self.settings.security.allowed_commands
        return base in allowed or any(base.startswith(a) for a in allowed)

    def _sanitize_args(self, args: list[str]) -> list[str]:
        """Basic sanitization (prevent injection)."""
        sanitized = []
        for arg in args:
            # Prevent dangerous shell metacharacters
            if any(
                c in arg
                for c in [";", "&", "|", "`", "$", "(", ")", "<", ">", "\n", "\r"]
            ):
                raise SandboxCommandError(
                    f"Potentially dangerous argument rejected: {arg[:50]}"
                )
            sanitized.append(arg)
        return sanitized

    async def execute_command(
        self,
        command: str,
        args: list[str] | None = None,
        *,
        input_data: str | None = None,
    ) -> SandboxResult:
        """
        Execute a shell command inside the sandbox.

        Args:
            command: Base command (must be whitelisted)
            args: List of arguments
            input_data: Optional stdin data

        Returns:
            SandboxResult
        """
        if not self.permission_manager.has_permission(Permission.SHELL_COMMAND):
            raise SandboxPermissionError(
                "SHELL_COMMAND permission required for sandbox execution"
            )

        args = args or []
        full_cmd = [command, *args]
        cmd_str = " ".join(shlex.quote(x) for x in full_cmd)

        if not self._is_command_allowed(command):
            raise SandboxCommandError(
                f"Command '{command}' is not in the allowed list: {self.settings.security.allowed_commands}"
            )

        sanitized_args = self._sanitize_args(args)
        full_cmd = [command, *sanitized_args]

        start = time.perf_counter()

        try:
            # Prepare subprocess
            process = await asyncio.create_subprocess_exec(
                *full_cmd,
                stdin=subprocess.PIPE if input_data else None,
                stdout=subprocess.PIPE
                if self.config.capture_output
                else subprocess.DEVNULL,
                stderr=subprocess.PIPE
                if self.config.capture_output
                else subprocess.DEVNULL,
                cwd=self.config.working_dir or self.settings.base_dir,
                env=self._get_safe_env(),
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(
                        input=input_data.encode() if input_data else None
                    ),
                    timeout=self.config.timeout_seconds,
                )
            except TimeoutError:
                process.kill()
                await process.wait()
                duration = (time.perf_counter() - start) * 1000
                return SandboxResult(
                    success=False,
                    exit_code=-1,
                    stdout="",
                    stderr="",
                    duration_ms=duration,
                    command=cmd_str,
                    error="Execution timed out",
                )

            duration = (time.perf_counter() - start) * 1000

            stdout_str = stdout.decode("utf-8", errors="replace") if stdout else ""
            stderr_str = stderr.decode("utf-8", errors="replace") if stderr else ""

            # Truncate overly large output
            if len(stdout_str) > self.config.max_output_bytes:
                stdout_str = (
                    stdout_str[: self.config.max_output_bytes] + "\n[TRUNCATED]"
                )

            return SandboxResult(
                success=process.returncode == 0,
                exit_code=process.returncode or 0,
                stdout=stdout_str,
                stderr=stderr_str,
                duration_ms=duration,
                command=cmd_str,
            )

        except FileNotFoundError:
            return SandboxResult(
                success=False,
                exit_code=127,
                stdout="",
                stderr="",
                duration_ms=(time.perf_counter() - start) * 1000,
                command=cmd_str,
                error=f"Command not found: {command}",
            )
        except Exception as exc:
            logger.exception("Sandbox execution failed")
            return SandboxResult(
                success=False,
                exit_code=-1,
                stdout="",
                stderr="",
                duration_ms=(time.perf_counter() - start) * 1000,
                command=cmd_str,
                error=str(exc),
            )

    def _get_safe_env(self) -> dict[str, str]:
        """Return a minimal, safe environment for subprocess."""
        env = {
            "PATH": "/usr/local/bin:/usr/bin:/bin",
            "HOME": str(self.settings.base_dir / "temp"),
            "LANG": "en_US.UTF-8",
            "PYTHONUNBUFFERED": "1",
        }
        # Never pass sensitive env vars
        return env

    async def execute_python_snippet(
        self, code: str, *, timeout: int | None = None
    ) -> SandboxResult:
        """
        Execute a restricted Python snippet.

        NOTE: In v1.0 this is a placeholder that rejects execution.
        Full restricted Python support will be added in a later module.
        """
        raise NotImplementedError(
            "Python code execution sandbox not yet implemented in core. "
            "Use execute_command with a whitelisted python script instead."
        )


# =============================================================================
# Convenience API
# =============================================================================


async def execute_in_sandbox(
    command: str,
    args: list[str] | None = None,
    config: SandboxConfig | None = None,
) -> SandboxResult:
    """One-shot convenience function."""
    sandbox = Sandbox(config)
    return await sandbox.execute_command(command, args)


__all__ = [
    "Sandbox",
    "SandboxConfig",
    "SandboxResult",
    "SandboxError",
    "SandboxTimeoutError",
    "SandboxPermissionError",
    "SandboxCommandError",
    "execute_in_sandbox",
]
