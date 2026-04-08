# tests/test_robots.py
import pytest
from mcp_server_fetch.robots import get_robots_txt_url


def test_robots_url_from_https():
    url = "https://example.com/page/article"
    result = get_robots_txt_url(url)
    assert result == "https://example.com/robots.txt"


def test_robots_url_from_http():
    url = "http://test.org/path?q=1"
    result = get_robots_txt_url(url)
    assert result == "http://test.org/robots.txt"


def test_robots_url_preserves_scheme():
    url = "https://sub.domain.com/deep/path"
    result = get_robots_txt_url(url)
    assert result == "https://sub.domain.com/robots.txt"
