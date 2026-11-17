"""URL slug generation utility for ESTD articles."""
import hashlib
import re
import unicodedata
from typing import Optional


def generate_slug(title: str, unique_suffix: Optional[str] = None) -> str:
    """Generate a clean, SEO-friendly, unique URL slug from an article headline.
    
    Args:
        title: The headline or title of the news article.
        unique_suffix: Optional unique identifier (e.g. article ID or URL hash).
            If omitted, a 6-character hex hash of the normalized title is appended.
            
    Returns:
        A lowercase, hyphen-separated slug string (max 120 chars).
    """
    if not title or not title.strip():
        base = "news-article"
    else:
        # Normalize unicode characters (e.g. accents, smart quotes)
        normalized = unicodedata.normalize("NFKD", title.strip())
        ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
        # Replace non-alphanumeric characters with hyphens
        clean_text = re.sub(r"[^\w\s-]", "", ascii_text).strip().lower()
        # Collapse whitespace and multiple hyphens
        base = re.sub(r"[-\s]+", "-", clean_text)
        # Limit slug base length to 75 characters without cutting words awkwardly
        if len(base) > 75:
            base = base[:75].rsplit("-", 1)[0]
        if not base:
            base = "news-article"

    if unique_suffix and str(unique_suffix).strip():
        suffix = str(unique_suffix).strip().lower()
    else:
        suffix = hashlib.sha256(title.encode("utf-8")).hexdigest()[:6]

    return f"{base}-{suffix}".strip("-")

