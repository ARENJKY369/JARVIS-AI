"""
JARVIS OS - Browser Agent
=========================

Web automation and research agent.

Features:
- Headless browser control (Playwright)
- Page navigation and scraping
- Form filling
"""

from .agent import BrowserAgent, get_browser_agent

__all__ = ["BrowserAgent", "get_browser_agent"]
