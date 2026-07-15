"""
JARVIS OS - Browser Agent
=========================

Intelligent web browsing and data extraction.

Uses Playwright for reliable, modern browser automation.
"""

from __future__ import annotations

from typing import Any

from loguru import logger

from core.config import get_settings
from core.security import get_permission_manager, Permission, AuditEventType, get_audit_logger


class BrowserAgent:
    """Sandboxed browser automation agent."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.pm = get_permission_manager()
        self.audit = get_audit_logger()
        self._playwright: Any = None
        self._browser: Any = None

    async def start(self) -> None:
        self.pm.require(Permission.AUTOMATION_BROWSER)
        try:
            from playwright.async_api import async_playwright
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(headless=True)
            logger.success("Browser agent started")
        except ImportError:
            logger.warning("Playwright not installed — browser agent disabled")
        except Exception as e:
            logger.error(f"Browser start failed: {e}")

    async def navigate(self, url: str) -> dict[str, Any]:
        self.pm.require(Permission.AUTOMATION_BROWSER)
        self.audit.log_event(AuditEventType.AUTOMATION_ACTION, details={"action": "navigate", "url": url})

        if self._browser is None:
            return {"error": "Browser not started"}

        page = await self._browser.new_page()
        try:
            response = await page.goto(url, wait_until="networkidle")
            title = await page.title()
            content = await page.content()
            return {
                "url": url,
                "title": title,
                "status": response.status if response else 0,
                "content_length": len(content),
            }
        finally:
            await page.close()

    async def close(self) -> None:
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
        logger.info("Browser agent closed")


_browser_agent: BrowserAgent | None = None


async def get_browser_agent() -> BrowserAgent:
    global _browser_agent
    if _browser_agent is None:
        _browser_agent = BrowserAgent()
        await _browser_agent.start()
    return _browser_agent
