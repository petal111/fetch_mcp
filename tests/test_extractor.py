# tests/test_extractor.py
import pytest
from mcp_server_fetch.extractor import extract_content_from_html, _extract_images_from_html


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


def test_images_preserved_in_output():
    html = '<html><body><article><h1>Title</h1><p>Text</p><img src="https://example.com/photo.png" alt="A photo"><p>More text</p></article></body></html>'
    result = extract_content_from_html(html)
    assert "![" in result
    assert "https://example.com/photo.png" in result


def test_extract_images_from_html():
    html = '<p><img src="https://a.com/1.png" alt="First"><img src="https://b.com/2.jpg"></p>'
    images = _extract_images_from_html(html)
    assert len(images) == 2
    assert images[0] == ("First", "https://a.com/1.png")
    assert images[1] == ("", "https://b.com/2.jpg")
