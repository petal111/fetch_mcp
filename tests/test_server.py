# tests/test_server.py
import pytest
from mcp_server_fetch.server import create_app


def test_create_app_returns_fastmcp():
    mcp = create_app(ignore_robots_txt=True)
    assert mcp is not None
    assert mcp.name == "mcp-fetch"


def test_create_app_with_custom_user_agent():
    mcp = create_app(
        ignore_robots_txt=True,
        user_agent="TestAgent/1.0",
    )
    assert mcp is not None


def test_create_app_with_all_options():
    mcp = create_app(
        ignore_robots_txt=True,
        user_agent="TestAgent/1.0",
        proxy_url="http://proxy:8080",
        stealth=True,
        cookies_path="/tmp/cookies.json",
    )
    assert mcp is not None
