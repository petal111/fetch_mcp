# src/mcp_server_fetch/extractor.py
import readabilipy.simple_json
import markdownify


def extract_content_from_html(html: str) -> str:
    """Extract main content from HTML and convert to Markdown.

    Uses readabilipy to extract the main content area (stripping nav, ads,
    sidebars), then converts the simplified HTML to Markdown using markdownify.

    Args:
        html: Raw HTML content to process.

    Returns:
        Simplified Markdown version of the page content.
    """
    if not html or not html.strip():
        return "No content available."

    ret = readabilipy.simple_json.simple_json_from_html_string(
        html, use_readability=True
    )

    if not ret.get("content"):
        return "Page failed to be simplified from HTML."

    content = markdownify.markdownify(
        ret["content"],
        heading_style=markdownify.ATX,
    )
    return content
