"""ArticleExtractor coordinating metadata and content extraction from HTML."""
from typing import Any, Dict
from bs4 import BeautifulSoup

from backend.step2_article_extraction.exceptions.extraction_exceptions import (
    ContentExtractionError,
    EmptyWebpageError,
)
from backend.step2_article_extraction.extractors.content_extractor import ContentExtractor
from backend.step2_article_extraction.extractors.metadata_extractor import MetadataExtractor


class ArticleExtractor:
    """Orchestrates parsing of HTML documents into structured article attributes."""

    def __init__(self):
        self.metadata_extractor = MetadataExtractor()
        self.content_extractor = ContentExtractor()

    def extract(self, html: str, url: str) -> Dict[str, Any]:
        """Extract article metadata and body from raw HTML.

        Args:
            html: Raw HTML string of the webpage.
            url: The source URL of the article.

        Returns:
            Dictionary containing extracted article attributes:
            - content: Full article body text
            - title: Article title/headline (if found)
            - canonical_url: Canonical URL
            - author: Extracted author (if found)
            - published_at: ISO 8601 published date (if found)
            - image_url: Lead image URL (if found)
            - source_name: Extracted publisher name (if found)

        Raises:
            EmptyWebpageError: If HTML is empty.
            ContentExtractionError: If no article body could be extracted.
        """
        if not html or not html.strip():
            raise EmptyWebpageError(url)

        # Parse with standard html.parser
        soup = BeautifulSoup(html, "html.parser")

        # Extract metadata
        meta = self.metadata_extractor.extract(soup, original_url=url)

        # Pre-extract JSON-LD to assist content extraction
        json_ld = self.metadata_extractor._extract_json_ld(soup)

        # Extract core body content
        content = self.content_extractor.extract(soup, json_ld=json_ld, url=url)

        return {
            "content": content,
            "title": meta.get("title"),
            "canonical_url": meta.get("canonical_url") or url,
            "author": meta.get("author"),
            "published_at": meta.get("published_at"),
            "image_url": meta.get("image_url"),
            "source_name": meta.get("source_name"),
        }
