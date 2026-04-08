# src/mcp_server_fetch/extractor.py
import re

import readabilipy.simple_json
import markdownify


def _extract_images_from_html(html: str) -> list[tuple[str, str]]:
    """Extract (alt, src) pairs from all <img> tags in HTML."""
    images = []
    for match in re.finditer(r"<img\s[^>]*>", html, re.IGNORECASE):
        tag = match.group(0)
        src_match = re.search(r'\bsrc=["\']([^"\']+)["\']', tag, re.IGNORECASE)
        alt_match = re.search(r'\balt=["\']([^"\']*)["\']', tag, re.IGNORECASE)
        if src_match:
            src = src_match.group(1).replace("&amp;", "&")
            alt = alt_match.group(1) if alt_match else ""
            images.append((alt, src))
    return images


def extract_content_from_html(html: str) -> str:
    """Extract main content from HTML and convert to Markdown.

    Uses readabilipy to extract the main content area (stripping nav, ads,
    sidebars), then converts the simplified HTML to Markdown using markdownify.
    Preserves image references as ![alt](url) in the output.

    Args:
        html: Raw HTML content to process.

    Returns:
        Simplified Markdown version of the page content with image URLs.
    """
    if not html or not html.strip():
        return "No content available."

    # Collect images from the original HTML before readabilipy strips them
    original_images = _extract_images_from_html(html)

    ret = readabilipy.simple_json.simple_json_from_html_string(
        html, use_readability=True
    )

    if not ret.get("content"):
        return "Page failed to be simplified from HTML."

    content = markdownify.markdownify(
        ret["content"],
        heading_style=markdownify.ATX,
    )

    # Check if readabilipy preserved any images in the markdown
    md_images = re.findall(r"!\[.*?\]\((.*?)\)", content)
    if md_images or not original_images:
        return content

    # readabilipy stripped all images — re-inject them from the original HTML
    image_lines = []
    for alt, src in original_images:
        image_lines.append(f"![{alt}]({src})")

    if image_lines:
        images_section = "\n\n".join(image_lines)
        content = content.rstrip() + "\n\n---\n\n## Images\n\n" + images_section + "\n"

    return content
