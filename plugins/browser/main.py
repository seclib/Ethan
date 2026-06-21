"""Browser Plugin — Web automation via Playwright.

Capabilities:
  - browse_web       : Navigate and interact with web pages
  - extract_content  : Extract text and structured content
  - take_screenshot  : Capture page screenshots
  - fill_forms       : Fill and submit web forms
  - click_elements   : Click on page elements
  - navigate_url     : Navigate to URLs
  - execute_javascript: Execute JavaScript in page context
"""

import asyncio
import base64
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class BrowserPlugin:
    """Web browser automation plugin using Playwright."""

    def __init__(self, config: dict[str, Any] | None = None):
        self.config = config or {}
        self._browser = None
        self._context = None
        self._page = None
        self._playwright = None

    async def initialize(self) -> None:
        """Initialize Playwright browser."""
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            raise ImportError(
                "Playwright is required for the browser plugin. "
                "Install: pip install playwright && playwright install chromium"
            )

        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(
            headless=self.config.get("headless", True),
        )
        self._context = await self._browser.new_context(
            viewport=self.config.get("viewport", {"width": 1280, "height": 720}),
            user_agent=self.config.get(
                "user_agent",
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
            ),
        )
        self._page = await self._context.new_page()
        logger.info("Browser plugin initialized")

    async def navigate(self, url: str) -> dict[str, Any]:
        """Navigate to a URL and return page info."""
        if not self._page:
            await self.initialize()

        timeout = self.config.get("timeout", 30000)
        await self._page.goto(url, wait_until="networkidle", timeout=timeout)

        return {
            "url": self._page.url,
            "title": await self._page.title(),
            "status": "success",
        }

    async def extract_content(self, selector: str | None = None) -> str:
        """Extract text content from the page."""
        if not self._page:
            return ""

        if selector:
            element = await self._page.query_selector(selector)
            if element:
                return await element.inner_text()
            return f"Selector '{selector}' not found"

        return await self._page.content()

    async def extract_text(self) -> str:
        """Extract visible text from the page."""
        if not self._page:
            return ""
        return await self._page.evaluate("document.body.innerText")

    async def screenshot(self, path: str | None = None) -> str:
        """Take a screenshot. Returns base64 or saves to path."""
        if not self._page:
            return ""

        if path:
            await self._page.screenshot(path=path, full_page=True)
            return f"Screenshot saved to {path}"

        screenshot_bytes = await self._page.screenshot(full_page=True)
        return base64.b64encode(screenshot_bytes).decode("utf-8")

    async def click(self, selector: str) -> bool:
        """Click an element by selector."""
        if not self._page:
            return False

        try:
            await self._page.click(selector, timeout=5000)
            return True
        except Exception as e:
            logger.error(f"Click failed: {e}")
            return False

    async def fill(self, selector: str, value: str) -> bool:
        """Fill a form field."""
        if not self._page:
            return False

        try:
            await self._page.fill(selector, value, timeout=5000)
            return True
        except Exception as e:
            logger.error(f"Fill failed: {e}")
            return False

    async def evaluate(self, script: str) -> Any:
        """Execute JavaScript in page context."""
        if not self._page:
            return None
        return await self._page.evaluate(script)

    async def search(self, query: str, engine: str = "google") -> list[dict[str, str]]:
        """Search the web and return results."""
        search_urls = {
            "google": f"https://www.google.com/search?q={query}",
            "bing": f"https://www.bing.com/search?q={query}",
            "duckduckgo": f"https://duckduckgo.com/?q={query}",
        }

        url = search_urls.get(engine, search_urls["google"])
        await self.navigate(url)

        # Extract search results
        results = []
        try:
            links = await self._page.query_selector_all("a[href^='http']")
            for link in links[:10]:
                href = await link.get_attribute("href")
                text = await link.inner_text()
                if text and href:
                    results.append({"title": text.strip(), "url": href})
        except Exception:
            pass

        return results

    async def close(self) -> None:
        """Close the browser."""
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
        self._browser = None
        self._context = None
        self._page = None
        self._playwright = None
        logger.info("Browser plugin closed")


# Plugin entrypoint
plugin = BrowserPlugin

__all__ = ["BrowserPlugin", "plugin"]