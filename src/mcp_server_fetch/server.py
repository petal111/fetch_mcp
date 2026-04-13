# src/mcp_server_fetch/server.py
from __future__ import annotations

import contextlib
import logging
import os
from typing import Annotated

from mcp.server.fastmcp import FastMCP
from pydantic import Field

from mcp_server_fetch.extractor import extract_content_from_html
from mcp_server_fetch.fetcher import smart_fetch
from mcp_server_fetch.robots import check_may_fetch_url

logger = logging.getLogger(__name__)

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/131.0.0.0 Safari/537.36"
)


def create_app(
    ignore_robots_txt: bool = False,
    user_agent: str | None = None,
    proxy_url: str | None = None,
    stealth: bool = False,
    cookies_path: str | None = None,
    stateless_http: bool = True,
) -> FastMCP:
    """Create and configure the MCP fetch server using FastMCP."""
    ua = user_agent or DEFAULT_USER_AGENT

    mcp = FastMCP(
        "mcp-fetch",
        stateless_http=stateless_http,
        json_response=True,
    )

    @mcp.tool()
    async def fetch(
        url: Annotated[str, Field(description="URL to fetch")],
        max_length: Annotated[
            int,
            Field(default=5000, description="Maximum number of characters to return."),
        ] = 5000,
        start_index: Annotated[
            int,
            Field(default=0, description="Start content from this character index."),
        ] = 0,
        raw: Annotated[
            bool,
            Field(
                default=False, description="Get raw content without markdown conversion."
            ),
        ] = False,
        force_browser: Annotated[
            bool,
            Field(default=False, description="Force use of headless browser."),
        ] = False,
    ) -> str:
        """Fetches a URL from the internet and optionally extracts its contents as markdown.

        This tool provides internet access — fetch the most up-to-date information from web pages.
        """
        if not ignore_robots_txt:
            await check_may_fetch_url(url, ua, proxy_url)

        result = await smart_fetch(
            url,
            user_agent=ua,
            proxy_url=proxy_url,
            force_raw=raw,
            force_browser=force_browser,
            stealth=stealth,
            cookies_path=cookies_path,
        )

        content = result.content
        is_html = "<html" in content.lower() or "<!doctype html" in content.lower()

        if is_html and not raw:
            content = extract_content_from_html(content)

        # Truncation and pagination
        original_length = len(content)
        if start_index >= original_length:
            content = "No more content available."
        else:
            truncated = content[start_index : start_index + max_length]
            if not truncated:
                content = "No more content available."
            else:
                content = truncated
                actual_length = len(truncated)
                remaining = original_length - (start_index + actual_length)
                if actual_length == max_length and remaining > 0:
                    next_index = start_index + actual_length
                    content += (
                        f"\n\nContent truncated. Call the fetch tool with "
                        f"a start_index of {next_index} to get more content."
                    )

        prefix = result.prefix
        # For SPA fallback, append a context-aware note based on extracted content quality
        if result.used_strategy == "httpx-spa-fallback" and not raw:
            if original_length < 500:
                prefix += (
                    "NOTE: This is a JavaScript-rendered page (SPA) and no browser "
                    "was available to render it. The extracted content below is "
                    "extremely limited (navigation elements only). "
                    "Do NOT fabricate or infer the actual page content. "
                    "Inform the user that this page could not be properly fetched.\n\n"
                )
            else:
                prefix += (
                    "NOTE: This page was detected as JavaScript-rendered (SPA). "
                    "The content below was extracted from raw HTML without browser "
                    "rendering — some dynamic content may be missing.\n\n"
                )
        return f"{prefix}Contents of {url}:\n{content}"

    return mcp


def run_server(
    transport: str = "stdio",
    port: int = 8080,
    ignore_robots_txt: bool = False,
    user_agent: str | None = None,
    proxy_url: str | None = None,
    stealth: bool = False,
    cookies_path: str | None = None,
) -> None:
    """Create and run the MCP fetch server with the specified transport."""
    # Only enable stateless_http for HTTP transports;
    # STDIO platforms (e.g. ModelScope MCP Hub) may not support it.
    is_http = transport in ("streamable-http", "sse")
    mcp = create_app(
        ignore_robots_txt=ignore_robots_txt,
        user_agent=user_agent,
        proxy_url=proxy_url,
        stealth=stealth,
        cookies_path=cookies_path,
        stateless_http=is_http,
    )

    if transport in ("streamable-http", "sse"):
        import uvicorn
        from starlette.applications import Starlette
        from starlette.middleware import Middleware
        from starlette.middleware.cors import CORSMiddleware
        from starlette.responses import JSONResponse
        from starlette.routing import Mount, Route

        async def health_check(request):
            return JSONResponse({"status": "ok"})

        if transport == "streamable-http":
            asgi_app = mcp.streamable_http_app()
        else:
            asgi_app = mcp.sse_app()

        @contextlib.asynccontextmanager
        async def lifespan(app: Starlette):
            async with mcp.session_manager.run():
                yield

        _cors_origins = os.environ.get("CORS_ORIGINS", "*").split(",")
        middleware = [
            Middleware(
                CORSMiddleware,
                allow_origins=_cors_origins,
                allow_methods=["GET", "POST", "OPTIONS"],
                allow_headers=["Content-Type", "Authorization", "Accept"],
                expose_headers=["Mcp-Session-Id"],
            )
        ]

        app = Starlette(
            routes=[
                Route("/health", health_check),
                Mount("/", app=asgi_app),
            ],
            middleware=middleware,
            lifespan=lifespan,
        )

        logger.info(f"Starting MCP Fetch Server ({transport}) on 0.0.0.0:{port}")
        uvicorn.run(app, host="0.0.0.0", port=port)
    else:
        mcp.run(transport="stdio")
