"""
JARVIS OS - Autonomous Agents Package
=====================================

Domain-specific autonomous agents that extend JARVIS capabilities.

Agents:
- Orchestrator: Central task dispatcher
- BrowserAgent: Web automation and research
- CodingAgent: Code generation, review, and execution
- LearningAgent: Continuous model improvement
"""

from .orchestrator import AgentOrchestrator, get_orchestrator

__all__ = ["AgentOrchestrator", "get_orchestrator"]
