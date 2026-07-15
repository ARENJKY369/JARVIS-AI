"""
JARVIS OS - Coding Agent
========================

Code generation, review, and execution agent.

Features:
- Generate code from natural language
- Review and refactor existing code
- Safe execution in sandbox
"""

from .agent import CodingAgent, get_coding_agent

__all__ = ["CodingAgent", "get_coding_agent"]
