# tests/test_integration.py
import pytest
from mcp_server_fetch.server import create_server


@pytest.mark.asyncio
async def test_server_lists_tools():
    server = create_server(ignore_robots_txt=True)
    assert server is not None
    assert server.name == "mcp-fetch"


@pytest.mark.asyncio
async def test_server_with_all_options():
    server = create_server(
        ignore_robots_txt=True,
        user_agent="TestAgent/1.0",
        proxy_url=None,
        stealth=False,
        cookies_path=None,
    )
    assert server is not None
