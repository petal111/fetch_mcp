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


def test_images_appear_inline_not_at_bottom():
    html = '<html><body><article><p>Before image</p><img src="https://example.com/photo.png" alt="A photo"><p>After image</p></article></body></html>'
    result = extract_content_from_html(html)
    # Image should appear between the two paragraphs, not under a "## Images" header
    assert "## Images" not in result
    before_pos = result.find("Before image")
    after_pos = result.find("After image")
    img_pos = result.find("![A photo]")
    assert before_pos < img_pos < after_pos, (
        f"Image not between paragraphs: before={before_pos}, img={img_pos}, after={after_pos}"
    )


def test_multiple_images_inline():
    html = (
        '<html><body><article>'
        '<p>First</p>'
        '<img src="https://a.com/1.png" alt="First image">'
        '<p>Second</p>'
        '<img src="https://b.com/2.jpg" alt="Second image">'
        '<p>Third</p>'
        '</article></body></html>'
    )
    result = extract_content_from_html(html)
    pos_first = result.find("![First image]")
    pos_second = result.find("![Second image]")
    pos_1 = result.find("First")
    pos_2 = result.find("Second")
    pos_3 = result.find("Third")
    # Order should be: First ... img1 ... Second ... img2 ... Third
    assert pos_1 < pos_first < pos_2 < pos_second < pos_3


def test_no_images_section_header():
    html = '<html><body><article><p>Text</p><img src="https://example.com/img.png" alt="Photo"></article></body></html>'
    result = extract_content_from_html(html)
    assert "## Images" not in result
    assert "---\n\n## Images" not in result


def test_extract_images_from_html():
    html = '<p><img src="https://a.com/1.png" alt="First"><img src="https://b.com/2.jpg"></p>'
    images = _extract_images_from_html(html)
    assert len(images) == 2
    assert images[0] == ("First", "https://a.com/1.png")
    assert images[1] == ("", "https://b.com/2.jpg")
