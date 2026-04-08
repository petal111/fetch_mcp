# src/mcp_server_fetch/robots.py
from __future__ import annotations

from urllib.parse import urlparse, urlunparse

from mcp.shared.exceptions import McpError
from mcp.types import ErrorData, INTERNAL_ERROR
from protego import Protego


def get_robots_txt_url(url: str) -> str:
    """Derive the robots.txt URL for a given page URL.

    Args:
        url: The page URL to derive robots.txt for.

    Returns:
        The robots.txt URL (e.g. "https://example.com/robots.txt").
    """
    parsed = urlparse(url)
    return urlunparse((parsed.scheme, parsed.netloc, "/robots.txt", "", "", ""))


async def check_may_fetch_url(
    url: str,
    user_agent: str,
    proxy_url: str | None = None,
) -> None:
    """Check if autonomous fetching is allowed by the site's robots.txt.

    Raises McpError if fetching is not allowed or robots.txt cannot be reached.

    Args:
        url: The URL to check.
        user_agent: The User-Agent string to check against.
        proxy_url: Optional proxy URL.

    Raises:
        McpError: If robots.txt forbids fetching or cannot be reached.
    """
    import httpx

    robots_url = get_robots_txt_url(url)

    async with httpx.AsyncClient(proxy=proxy_url) as client:
        try:
            response = await client.get(
                robots_url,
                follow_redirects=True,
                headers={"User-Agent": user_agent},
                timeout=10,
            )
        except httpx.HTTPError:
            raise McpError(
                ErrorData(
                    code=INTERNAL_ERROR,
                    message=f"Failed to fetch robots.txt {robots_url} due to a connection issue",
                )
            )

        if response.status_code in (401, 403):
            raise McpError(
                ErrorData(
                    code=INTERNAL_ERROR,
                    message=f"When fetching robots.txt ({robots_url}), received status {response.status_code}. "
                    "Autonomous fetching is not allowed. Try using the fetch prompt for manual fetching.",
                )
            )

        if 400 <= response.status_code < 500:
            return  # No robots.txt found, assume allowed

        robot_txt = response.text
        processed = "\n".join(
            line for line in robot_txt.splitlines() if not line.strip().startswith("#")
        )
        parser = Protego.parse(processed)
        if not parser.can_fetch(str(url), user_agent):
            raise McpError(
                ErrorData(
                    code=INTERNAL_ERROR,
                    message=f"The site's robots.txt ({robots_url}) specifies that autonomous fetching "
                    f"is not allowed for {user_agent}.\n{url}\n\n{robot_txt}\n\n"
                    "The assistant must let the user know it failed to view the page. "
                    "The user can try manually fetching by using the fetch prompt.",
                )
            )
