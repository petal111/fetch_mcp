# src/mcp_server_fetch/fetcher.py
from __future__ import annotations

import json
import random
import re
from dataclasses import dataclass
from typing import Any

import httpx
from mcp.shared.exceptions import McpError
from mcp.types import ErrorData, INTERNAL_ERROR

BROWSER_HEADERS: dict[str, str] = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
    "Cache-Control": "max-age=0",
}

_MIN_CONTENT_LENGTH = 200

_SPA_MARKERS = [
    '<div id="root"></div>',
    '<div id="app"></div>',
    '<div id="__next"></div>',
    "<noscript>",
    'id="__nuxt"',
]


@dataclass
class FetchResult:
    """Result of a fetch operation."""
    content: str
    prefix: str
    used_strategy: str  # "httpx", "playwright", "stealth"


def needs_browser_fallback(html: str, min_length: int = _MIN_CONTENT_LENGTH) -> bool:
    """Determine if the HTML content indicates a need for browser fallback."""
    if len(html.strip()) < min_length:
        return True

    lower = html.lower()
    for marker in _SPA_MARKERS:
        if marker.lower() in lower:
            marker_pos = lower.find(marker.lower())
            surrounding = html[max(0, marker_pos - 200): marker_pos + 500]
            text_content = surrounding.replace(marker, "")
            text_only = re.sub(r"<[^>]+>", "", text_content).strip()
            if len(text_only) < min_length:
                return True

    return False


def _load_cookies(cookies_path: str | None) -> list[dict[str, Any]]:
    """Load cookies from a JSON file."""
    if not cookies_path:
        return []
    with open(cookies_path, encoding="utf-8") as f:
        return json.load(f)


async def _fetch_with_httpx(
    url: str,
    user_agent: str | None = None,
    proxy_url: str | None = None,
    cookies: list[dict[str, Any]] | None = None,
    extra_headers: dict[str, str] | None = None,
) -> tuple[str, str]:
    """Fetch URL using httpx with browser-like headers."""
    headers = {**BROWSER_HEADERS}
    if user_agent:
        headers["User-Agent"] = user_agent
    if extra_headers:
        headers.update(extra_headers)

    async with httpx.AsyncClient(proxy=proxy_url, follow_redirects=True) as client:
        try:
            response = await client.get(url, headers=headers, timeout=30)
        except httpx.HTTPError as e:
            raise McpError(
                ErrorData(code=INTERNAL_ERROR, message=f"Failed to fetch {url}: {e!r}")
            )

        if response.status_code >= 400:
            raise McpError(
                ErrorData(
                    code=INTERNAL_ERROR,
                    message=f"Failed to fetch {url} — status code {response.status_code}",
                )
            )

        content_type = response.headers.get("content-type", "")
        return response.text, f"Content type: {content_type}\n"


async def _fetch_with_playwright(
    url: str,
    stealth: bool = False,
    user_agent: str | None = None,
    proxy_url: str | None = None,
    cookies: list[dict[str, Any]] | None = None,
    extra_headers: dict[str, str] | None = None,
) -> tuple[str, str]:
    """Fetch URL using Playwright headless browser."""
    from playwright.async_api import async_playwright

    try:
        async with async_playwright() as pw:
            browser_args: list[str] = []
            if stealth:
                browser_args.extend([
                    "--disable-blink-features=AutomationControlled",
                ])

            launch_kwargs: dict[str, Any] = {"headless": True}
            if browser_args:
                launch_kwargs["args"] = browser_args
            if proxy_url:
                launch_kwargs["proxy"] = {"server": proxy_url}

            browser = await pw.chromium.launch(**launch_kwargs)
            context_kwargs: dict[str, Any] = {}
            if user_agent:
                context_kwargs["user_agent"] = user_agent
            if extra_headers:
                context_kwargs["extra_http_headers"] = extra_headers

            context = await browser.new_context(**context_kwargs)

            if cookies:
                await context.add_cookies(cookies)

            if stealth:
                await _inject_stealth(context)

            page = await context.new_page()
            await page.goto(url, wait_until="networkidle", timeout=30000)
            await page.wait_for_timeout(1000)
            content = await page.content()
            await browser.close()
            return content, ""

    except Exception as e:
        raise McpError(
            ErrorData(
                code=INTERNAL_ERROR,
                message=f"Playwright failed to fetch {url}: {e!r}",
            )
        )


async def _inject_stealth(context) -> None:
    """Inject stealth scripts to avoid bot detection."""
    await context.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
        Object.defineProperty(navigator, 'languages', { get: () => ['zh-CN', 'zh', 'en'] });
        Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
        window.chrome = { runtime: {} };
    """)


async def smart_fetch(
    url: str,
    user_agent: str | None = None,
    proxy_url: str | None = None,
    force_raw: bool = False,
    force_browser: bool = False,
    stealth: bool = False,
    cookies_path: str | None = None,
    extra_headers: dict[str, str] | None = None,
) -> FetchResult:
    """Fetch a URL using the three-tier strategy with automatic fallback.

    Strategy: httpx (L1) -> Playwright (L2) -> Playwright+Stealth (L3)
    """
    cookies = _load_cookies(cookies_path)
    errors: list[str] = []

    if force_browser or stealth:
        strategy = "stealth" if stealth else "playwright"
        try:
            html, prefix = await _fetch_with_playwright(
                url, stealth=stealth, user_agent=user_agent,
                proxy_url=proxy_url, cookies=cookies, extra_headers=extra_headers,
            )
            return FetchResult(content=html, prefix=prefix, used_strategy=strategy)
        except McpError as e:
            raise McpError(
                ErrorData(
                    code=INTERNAL_ERROR,
                    message=f"Browser fetch ({strategy}) failed for {url}: {e}",
                )
            )

    # L1: httpx
    try:
        content, prefix = await _fetch_with_httpx(
            url, user_agent=user_agent, proxy_url=proxy_url,
            cookies=cookies, extra_headers=extra_headers,
        )

        if force_raw:
            return FetchResult(content=content, prefix=prefix, used_strategy="httpx")

        content_type = prefix.lower()
        is_html = "<html" in content.lower() or "text/html" in content_type

        if not is_html:
            return FetchResult(content=content, prefix=prefix, used_strategy="httpx")

        if not needs_browser_fallback(content):
            return FetchResult(content=content, prefix=prefix, used_strategy="httpx")

    except McpError as e:
        errors.append(f"L1 (httpx): {e}")

    # L2: Playwright
    try:
        html, prefix = await _fetch_with_playwright(
            url, stealth=False, user_agent=user_agent,
            proxy_url=proxy_url, cookies=cookies, extra_headers=extra_headers,
        )
        if html and not needs_browser_fallback(html):
            return FetchResult(content=html, prefix=prefix, used_strategy="playwright")
    except McpError as e:
        errors.append(f"L2 (playwright): {e}")

    # L3: Playwright + Stealth
    try:
        html, prefix = await _fetch_with_playwright(
            url, stealth=True, user_agent=user_agent,
            proxy_url=proxy_url, cookies=cookies, extra_headers=extra_headers,
        )
        if html:
            return FetchResult(content=html, prefix=prefix, used_strategy="stealth")
    except McpError as e:
        errors.append(f"L3 (stealth): {e}")

    # All strategies failed
    error_summary = "\n".join(errors)
    raise McpError(
        ErrorData(
            code=INTERNAL_ERROR,
            message=f"All fetch strategies failed for {url}:\n{error_summary}",
        )
    )
