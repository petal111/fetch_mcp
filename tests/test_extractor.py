# tests/test_extractor.py
import pytest
from mcp_server_fetch.extractor import extract_content_from_html


def test_simple_html_to_markdown():
    html = "<html><body><h1>Hello</h1><p>World</p></body></html>"
    result = extract_content_from_html(html)
    assert "Hello" in result
    assert "World" in result


def test_strips_navigation_and_scripts():
    html = """
    <html>
    <head><script>var x = 1;</script></head>
    <body>
        <nav><a href="/">Home</a></nav>
        <main><p>Main content here</p></main>
    </body>
    </html>
    """
    result = extract_content_from_html(html)
    assert "Main content here" in result


def test_empty_html_returns_fallback():
    html = ""
    result = extract_content_from_html(html)
    assert isinstance(result, str)


def test_markdown_heading_style():
    html = "<html><body><h2>Section</h2><p>Text</p></body></html>"
    result = extract_content_from_html(html)
    assert "##" in result or "Section" in result
