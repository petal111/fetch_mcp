# tests/test_integration.py
import pytest
from mcp_server_fetch.server import create_app


@pytest.mark.asyncio
async def test_server_lists_tools():
    mcp = create_app(ignore_robots_txt=True)
    assert mcp is not None
    assert mcp.name == "mcp-fetch"


@pytest.mark.asyncio
async def test_server_with_all_options():
    mcp = create_app(
        ignore_robots_txt=True,
        user_agent="TestAgent/1.0",
        proxy_url=None,
        stealth=False,
        cookies_path=None,
    )
    assert mcp is not None
