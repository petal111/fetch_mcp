# tests/test_fetcher.py
import pytest
from mcp_server_fetch.fetcher import (
    BROWSER_HEADERS,
    FetchResult,
    needs_browser_fallback,
)


def test_browser_headers_contains_key_fields():
    assert "User-Agent" in BROWSER_HEADERS
    assert "Accept" in BROWSER_HEADERS
    assert "Accept-Language" in BROWSER_HEADERS
    # Accept-Encoding should NOT be set — let httpx handle decompression
    assert "Accept-Encoding" not in BROWSER_HEADERS


def test_needs_browser_fallback_short_content():
    html = "<html><body><div id='root'></div></body></html>"
    assert needs_browser_fallback(html, 200) is True


def test_needs_browser_fallback_normal_content():
    html = "<html><body><p>" + "x" * 500 + "</p></body></html>"
    assert needs_browser_fallback(html, 200) is False


def test_needs_browser_fallback_spa_shell():
    html = '<html><body><div id="root"></div></body></html>'
    assert needs_browser_fallback(html, 200) is True


def test_needs_browser_fallback_js_required_marker():
    html = "<html><body><noscript>Enable JavaScript</noscript></body></html>"
    assert needs_browser_fallback(html, 200) is True


def test_needs_browser_fallback_large_html_no_text():
    """Large HTML with only script/style content should trigger fallback."""
    html = "<html><head><script>var x = " + '"' + "a" * 10000 + '"' + ";</script></head><body></body></html>"
    assert needs_browser_fallback(html, 200) is True


def test_fetch_result_dataclass():
    result = FetchResult(content="hello", prefix="info: ", used_strategy="httpx")
    assert result.content == "hello"
    assert result.prefix == "info: "
    assert result.used_strategy == "httpx"
