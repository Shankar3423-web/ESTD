"""HTML cleaner module for converting HTML markup to clean article text."""
import html
import re
from typing import Optional
from bs4 import BeautifulSoup, Comment

# Tags whose entire subtree should be discarded
DISCARD_TAGS = {
    "script",
    "style",
    "noscript",
    "iframe",
    "svg",
    "canvas",
    "form",
    "button",
    "input",
    "select",
    "textarea",
    "nav",
    "footer",
    "header",
    "aside",
    "video",
    "audio",
    "template",
}

# Block tags that should introduce newlines
BLOCK_TAGS = {
    "p",
    "div",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "li",
    "blockquote",
    "article",
    "section",
    "tr",
    "pre",
}


class HTMLCleaner:
    """Extracts clean text from HTML markup while preserving article structure."""

    _HTML_TAG_RE = re.compile(r"<[^>]+>")

    @classmethod
    def contains_html(cls, text: str) -> bool:
        """Quickly check if the string likely contains HTML tags."""
        return bool(cls._HTML_TAG_RE.search(text))

    def clean(self, raw_content: Optional[str]) -> str:
        """Convert HTML string to clean, plain text.

        Preserves paragraph breaks and unescapes entities safely.
        Never crashes on malformed HTML.
        """
        if not raw_content:
            return ""

        if not isinstance(raw_content, str):
            raw_content = str(raw_content)

        # Quick check: if no tags present, just unescape HTML entities and return
        if not self.contains_html(raw_content):
            return html.unescape(raw_content)

        try:
            soup = BeautifulSoup(raw_content, "html.parser")

            # Remove HTML comments
            for comment in soup.find_all(string=lambda t: isinstance(t, Comment)):
                comment.extract()

            # Remove non-content tags and their children
            for tag in soup.find_all(DISCARD_TAGS):
                tag.decompose()

            # Decompose common ad/cookie/social noise containers by class or id
            for tag in soup.find_all(attrs={"class": re.compile(r"\b(ad-banner|ad-slot|ad-container|advertisement|cookie-notice|cookie-banner|social-share|share-box)\b", re.IGNORECASE)}):
                tag.decompose()
            for tag in soup.find_all(attrs={"id": re.compile(r"\b(ad-banner|ad-slot|ad-container|advertisement|cookie-notice|cookie-banner)\b", re.IGNORECASE)}):
                tag.decompose()

            # Replace <br> tags with newline
            for br in soup.find_all(["br", "hr"]):
                br.replace_with("\n")

            # Append newlines to block tags to preserve paragraph structure
            for block in soup.find_all(BLOCK_TAGS):
                block.append("\n\n")

            # Extract text
            cleaned_text = soup.get_text()

            # Unescape any residual HTML entities
            cleaned_text = html.unescape(cleaned_text)

            return cleaned_text

        except Exception:
            # Fallback for catastrophic parser errors: strip tags via regex
            fallback_text = self._HTML_TAG_RE.sub(" ", raw_content)
            return html.unescape(fallback_text)
