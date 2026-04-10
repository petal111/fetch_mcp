# src/mcp_server_fetch/extractor.py
import re

import readabilipy.simple_json
import markdownify


def _replace_images_with_placeholders(html: str) -> tuple[str, list[tuple[str, str]]]:
    """Replace <img> tags with text placeholders that survive readabilipy.

    Returns:
        Tuple of (modified HTML, list of (alt, src) tuples in order).
    """
    images = []
    placeholder_map = {}

    def _replacer(match: re.Match) -> str:
        idx = len(images)
        tag = match.group(0)
        src_match = re.search(r'\bsrc=["\']([^"\']+)["\']', tag, re.IGNORECASE)
        alt_match = re.search(r'\balt=["\']([^"\']*)["\']', tag, re.IGNORECASE)
        if src_match:
            src = src_match.group(1).replace("&amp;", "&")
            alt = alt_match.group(1) if alt_match else ""
            images.append((alt, src))
            placeholder = f"IMGPLACEHOLDER{idx}END"
            placeholder_map[placeholder] = idx
            return f" {placeholder} "
        return tag

    modified = re.sub(r"<img\s[^>]*>", _replacer, html, flags=re.IGNORECASE)
    return modified, images


def _restore_image_placeholders(md: str, images: list[tuple[str, str]]) -> str:
    """Replace __IMG_N__ placeholders back with ![alt](url) markdown."""
    for idx, (alt, src) in enumerate(images):
        placeholder = f"IMGPLACEHOLDER{idx}END"
        md = md.replace(placeholder, f"![{alt}]({src})")
    return md


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
    Preserves image references as ![alt](url) inline at their original positions.

    Args:
        html: Raw HTML content to process.

    Returns:
        Simplified Markdown version of the page content with inline images.
    """
    if not html or not html.strip():
        return "No content available."

    # Replace <img> tags with text placeholders so readabilipy preserves them
    html, images = _replace_images_with_placeholders(html)

    ret = readabilipy.simple_json.simple_json_from_html_string(
        html, use_readability=True
    )

    if not ret.get("content"):
        return "Page failed to be simplified from HTML."

    content = markdownify.markdownify(
        ret["content"],
        heading_style=markdownify.ATX,
    )

    # Restore placeholders as inline markdown images
    content = _restore_image_placeholders(content, images)

    return content
