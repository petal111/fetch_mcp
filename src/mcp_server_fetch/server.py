# src/mcp_server_fetch/server.py
from __future__ import annotations

from typing import Annotated

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.shared.exceptions import McpError
from mcp.types import (
    ErrorData,
    GetPromptResult,
    Prompt,
    PromptArgument,
    PromptMessage,
    TextContent,
    Tool,
    INVALID_PARAMS,
)
from pydantic import BaseModel, Field, AnyUrl

from mcp_server_fetch.extractor import extract_content_from_html
from mcp_server_fetch.fetcher import smart_fetch
from mcp_server_fetch.robots import check_may_fetch_url

DEFAULT_USER_AGENT_AUTONOMOUS = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/131.0.0.0 Safari/537.36"
)
DEFAULT_USER_AGENT_MANUAL = DEFAULT_USER_AGENT_AUTONOMOUS


class FetchParams(BaseModel):
    """Parameters for the fetch tool."""

    url: Annotated[AnyUrl, Field(description="URL to fetch")]
    max_length: Annotated[
        int,
        Field(default=5000, description="Maximum number of characters to return."),
    ]
    start_index: Annotated[
        int,
        Field(default=0, description="Start content from this character index."),
    ]
    raw: Annotated[
        bool,
        Field(default=False, description="Get raw content without markdown conversion."),
    ]
    force_browser: Annotated[
        bool,
        Field(default=False, description="Force use of headless browser."),
    ]


def create_server(
    ignore_robots_txt: bool = False,
    user_agent: str | None = None,
    proxy_url: str | None = None,
    stealth: bool = False,
    cookies_path: str | None = None,
) -> Server:
    """Create and configure the MCP fetch server."""
    server = Server("mcp-fetch")
    ua_autonomous = user_agent or DEFAULT_USER_AGENT_AUTONOMOUS
    ua_manual = user_agent or DEFAULT_USER_AGENT_MANUAL

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        return [
            Tool(
                name="fetch",
                description=(
                    "Fetches a URL from the internet and optionally extracts its contents as markdown. "
                    "This tool provides internet access — fetch the most up-to-date information from web pages."
                ),
                inputSchema=FetchParams.model_json_schema(),
            )
        ]

    @server.list_prompts()
    async def list_prompts() -> list[Prompt]:
        return [
            Prompt(
                name="fetch",
                description="Fetch a URL and extract its contents as markdown",
                arguments=[
                    PromptArgument(name="url", description="URL to fetch", required=True)
                ],
            )
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[TextContent]:
        if name != "fetch":
            raise McpError(ErrorData(code=INVALID_PARAMS, message=f"Unknown tool: {name}"))

        try:
            args = FetchParams(**arguments)
        except Exception as e:
            raise McpError(ErrorData(code=INVALID_PARAMS, message=str(e)))

        url = str(args.url)

        if not ignore_robots_txt:
            await check_may_fetch_url(url, ua_autonomous, proxy_url)

        result = await smart_fetch(
            url,
            user_agent=ua_autonomous,
            proxy_url=proxy_url,
            force_raw=args.raw,
            force_browser=args.force_browser,
            stealth=stealth,
            cookies_path=cookies_path,
        )

        content = result.content
        is_html = "<html" in content.lower() or "<!doctype html" in content.lower()

        if is_html and not args.raw:
            content = extract_content_from_html(content)

        # Truncation and pagination
        original_length = len(content)
        if args.start_index >= original_length:
            content = "No more content available."
        else:
            truncated = content[args.start_index: args.start_index + args.max_length]
            if not truncated:
                content = "No more content available."
            else:
                content = truncated
                actual_length = len(truncated)
                remaining = original_length - (args.start_index + actual_length)
                if actual_length == args.max_length and remaining > 0:
                    next_index = args.start_index + actual_length
                    content += (
                        f"\n\nContent truncated. Call the fetch tool with "
                        f"a start_index of {next_index} to get more content."
                    )

        prefix = result.prefix
        return [TextContent(type="text", text=f"{prefix}Contents of {url}:\n{content}")]

    @server.get_prompt()
    async def get_prompt(name: str, arguments: dict | None) -> GetPromptResult:
        if name != "fetch":
            raise McpError(ErrorData(code=INVALID_PARAMS, message=f"Unknown prompt: {name}"))

        if not arguments or "url" not in arguments:
            raise McpError(ErrorData(code=INVALID_PARAMS, message="URL is required"))

        url = arguments["url"]
        try:
            result = await smart_fetch(
                url,
                user_agent=ua_manual,
                proxy_url=proxy_url,
                stealth=stealth,
                cookies_path=cookies_path,
            )
            content = result.content
            is_html = "<html" in content.lower()
            if is_html:
                content = extract_content_from_html(content)
        except McpError as e:
            return GetPromptResult(
                description=f"Failed to fetch {url}",
                messages=[
                    PromptMessage(
                        role="user",
                        content=TextContent(type="text", text=str(e)),
                    )
                ],
            )

        return GetPromptResult(
            description=f"Contents of {url}",
            messages=[
                PromptMessage(
                    role="user",
                    content=TextContent(type="text", text=result.prefix + content),
                )
            ],
        )

    return server


async def run_server(
    transport: str = "stdio",
    port: int = 8080,
    ignore_robots_txt: bool = False,
    user_agent: str | None = None,
    proxy_url: str | None = None,
    stealth: bool = False,
    cookies_path: str | None = None,
) -> None:
    """Create and run the MCP fetch server with the specified transport."""
    server = create_server(
        ignore_robots_txt=ignore_robots_txt,
        user_agent=user_agent,
        proxy_url=proxy_url,
        stealth=stealth,
        cookies_path=cookies_path,
    )
    options = server.create_initialization_options()

    if transport == "sse":
        from mcp_server_fetch.transport import run_sse
        await run_sse(server, options, port)
    else:
        async with stdio_server() as (read_stream, write_stream):
            await server.run(read_stream, write_stream, options, raise_exceptions=False)
