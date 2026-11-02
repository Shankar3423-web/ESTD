"""Document formatting and title sanitization for Step 8 Google Docs."""
from datetime import datetime, timezone
import re
from typing import Optional

from backend.step7_content_generation.schemas.generated_news import GeneratedNews


class DocumentFormatter:
    """Formats validated ESTD news into standardized Google Document titles and content."""

    @staticmethod
    def sanitize_title(
        title: str,
        article_id: Optional[int] = None,
        max_length: int = 150,
    ) -> str:
        """Create a deterministic, clean, human-readable Google Document title.

        Format: ESTD - <Title> (or with article ID suffix if disambiguation is required).
        """
        if not title or not title.strip():
            title = f"Untitled Article {article_id or ''}".strip()

        # Clean invalid characters and normalize whitespace
        cleaned = re.sub(r"[\r\n\t]+", " ", title)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        # Remove characters problematic in filenames or titles
        cleaned = re.sub(r'[\\/:*?"<>|]', "-", cleaned)

        prefix = "ESTD - "
        available_length = max_length - len(prefix)

        if len(cleaned) > available_length:
            cleaned = cleaned[:available_length - 3].rstrip() + "..."

        return f"{prefix}{cleaned}"

    @staticmethod
    def format_document_content(
        news: GeneratedNews,
        article_id: Optional[int] = None,
        original_published_at: Optional[str] = None,
    ) -> str:
        """Format the complete approved ESTD content into the standard template."""
        # Format generation date
        gen_date_str = (
            news.generated_at.strftime("%Y-%m-%d %H:%M:%S UTC")
            if hasattr(news, "generated_at") and news.generated_at
            else datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        )

        category_str = news.category.value if hasattr(news.category, "value") else str(news.category)
        source_url_str = str(news.source_url)
        pub_date_str = original_published_at or gen_date_str

        # Subtitle section if available
        subtitle_section = f"\nSubtitle:\n{news.subtitle.strip()}\n" if news.subtitle and news.subtitle.strip() else ""

        # Executive summary section
        summary_section = f"\nExecutive Summary:\n{news.summary.strip()}\n" if news.summary and news.summary.strip() else ""

        template = f"""ESTD NEWS

Title:
{news.title.strip()}
{subtitle_section}
Category:
{category_str}

Published:
{gen_date_str}
{summary_section}
--------------------------------

ARTICLE

{news.content.strip()}

--------------------------------

SOURCE INFORMATION

Original Source:
{news.source_name.strip()}

Original Article:
{source_url_str}

Original Publication Date:
{pub_date_str}
"""
        return template
