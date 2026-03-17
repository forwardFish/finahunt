from __future__ import annotations

import asyncio
from collections import defaultdict
from collections.abc import Awaitable, Callable
from time import monotonic
from typing import Any
from urllib.parse import urlparse

from playwright.async_api import Browser, BrowserContext, Page, Playwright, async_playwright

from skills.fetch.html import HtmlSnapshot


class PlaywrightFetcher:
    def __init__(self, *, headless: bool, timeout_ms: int, user_agent: str | None = None) -> None:
        self.headless = headless
        self.timeout_ms = timeout_ms
        self.user_agent = user_agent
        self._playwright: Playwright | None = None
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None
        self._last_hit_at: dict[str, float] = defaultdict(float)

    async def __aenter__(self) -> "PlaywrightFetcher":
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(
            headless=self.headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--no-sandbox",
            ],
        )
        self._context = await self._browser.new_context(user_agent=self.user_agent)
        await self._context.add_init_script(
            """
            Object.defineProperty(navigator, 'webdriver', {
              get: () => undefined,
            });
            """
        )
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        if self._context is not None:
            await self._context.close()
        if self._browser is not None:
            await self._browser.close()
        if self._playwright is not None:
            await self._playwright.stop()

    async def fetch_snapshot(
        self,
        url: str,
        *,
        wait_until: str,
        rate_limit_seconds: float,
        timeout_ms: int | None = None,
    ) -> HtmlSnapshot:
        await self._respect_rate_limit(url, rate_limit_seconds)
        if self._context is None:
            raise RuntimeError("PlaywrightFetcher is not initialized")
        page = await self._context.new_page()
        try:
            await page.goto(url, wait_until=wait_until, timeout=timeout_ms or self.timeout_ms)
            await page.wait_for_load_state("networkidle", timeout=timeout_ms or self.timeout_ms)
            html = await page.content()
            return HtmlSnapshot(url=url, html=html)
        finally:
            await page.close()

    async def fetch_with_retry(
        self,
        builder: Callable[[], Awaitable[HtmlSnapshot]],
        *,
        retry_count: int,
        retry_delay_seconds: float = 1.0,
    ) -> HtmlSnapshot:
        last_error: Exception | None = None
        for attempt in range(retry_count + 1):
            try:
                return await builder()
            except Exception as exc:  # pragma: no cover - network failures depend on runtime
                last_error = exc
                if attempt >= retry_count:
                    break
                await asyncio.sleep(retry_delay_seconds * (attempt + 1))
        raise RuntimeError(f"fetch_failed_after_retry:{last_error}") from last_error

    async def _respect_rate_limit(self, url: str, rate_limit_seconds: float) -> None:
        if rate_limit_seconds <= 0:
            return
        host = urlparse(url).netloc
        last_hit_at = self._last_hit_at.get(host, 0.0)
        elapsed = monotonic() - last_hit_at
        wait_seconds = rate_limit_seconds - elapsed
        if wait_seconds > 0:
            await asyncio.sleep(wait_seconds)
        self._last_hit_at[host] = monotonic()
