"""
JARVIS OS - Agent Orchestrator
==============================

Central dispatcher for all autonomous agents.

Responsibilities:
- Route tasks to appropriate domain agents
- Manage agent lifecycle
- Coordinate multi-step workflows
- Enforce permissions and audit trails
"""

from __future__ import annotations

from typing import Any

from loguru import logger

from core.config import get_settings
from core.security import get_permission_manager, Permission, AuditEventType, get_audit_logger


class AgentOrchestrator:
    """Central hub for dispatching tasks to domain agents."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.pm = get_permission_manager()
        self.audit = get_audit_logger()
        self._agents: dict[str, Any] = {}
        logger.info("AgentOrchestrator initialized")

    def register_agent(self, name: str, agent: Any) -> None:
        """Register a domain agent."""
        self._agents[name] = agent
        logger.debug(f"Registered agent: {name}")

    async def dispatch(self, task: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        """Dispatch a task to the appropriate agent(s)."""
        self.pm.require(Permission.AUTOMATION_EXECUTE)

        self.audit.log_event(
            AuditEventType.AUTOMATION_ACTION,
            details={"task": task, "agents": list(self._agents.keys())},
        )

        # Simple keyword-based routing (will be replaced by LLM-based routing)
        task_lower = task.lower()
        if any(k in task_lower for k in ["browse", "web", "url", "site", "page"]):
            return {"agent": "browser", "status": "dispatched", "task": task}
        elif any(k in task_lower for k in ["code", "program", "script", "debug", "function"]):
            return {"agent": "coding", "status": "dispatched", "task": task}
        elif any(k in task_lower for k in ["learn", "train", "improve", "fine-tune"]):
            return {"agent": "learning", "status": "dispatched", "task": task}
        else:
            return {"agent": "general", "status": "dispatched", "task": task}

    def list_agents(self) -> list[str]:
        """List all registered agents."""
        return list(self._agents.keys())


_orchestrator: AgentOrchestrator | None = None


def get_orchestrator() -> AgentOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = AgentOrchestrator()
    return _orchestrator
