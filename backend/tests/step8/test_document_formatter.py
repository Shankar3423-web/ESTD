"""Unit tests for DocumentFormatter title sanitization and template formatting."""
from datetime import datetime, timezone
import pytest

from backend.common.constants.categories import ESTDCategory
from backend.step7_content_generation.schemas.generated_news import GeneratedNews
from backend.step8_gdrive_output.services.document_formatter import DocumentFormatter


class TestDocumentFormatter:
    """Test title sanitization and document structure formatting."""

    def test_sanitize_title_standard(self):
        """Standard valid title prefixes correctly."""
        title = "OpenAI Introduces New AI Model"
        result = DocumentFormatter.sanitize_title(title)
        assert result == "ESTD - OpenAI Introduces New AI Model"

    def test_sanitize_title_handles_special_characters(self):
        """Special characters like quotes, colons, slashes are sanitized."""
        title = 'Quantum Computing: "Breakthrough" in 2026/2027?'
        result = DocumentFormatter.sanitize_title(title)
        assert result == "ESTD - Quantum Computing- -Breakthrough- in 2026-2027-"

    def test_sanitize_title_normalizes_whitespace(self):
        """Whitespace and newlines are collapsed."""
        title = "  SpaceX   Launches \n Starship \t Orbital Flight  "
        result = DocumentFormatter.sanitize_title(title)
        assert result == "ESTD - SpaceX Launches Starship Orbital Flight"

    def test_sanitize_title_truncates_long_titles(self):
        """Extremely long titles are truncated deterministically with ellipsis."""
        long_title = "A" * 200
        result = DocumentFormatter.sanitize_title(long_title, max_length=100)
        assert len(result) <= 100
        assert result.startswith("ESTD - AAAA")
        assert result.endswith("...")

    def test_sanitize_title_empty_fallback(self):
        """Empty titles fallback cleanly to untitled format."""
        assert DocumentFormatter.sanitize_title("", article_id=42) == "ESTD - Untitled Article 42"
        assert DocumentFormatter.sanitize_title("   ", article_id=99) == "ESTD - Untitled Article 99"

    def test_format_document_content_contains_all_sections(self):
        """Formatted Google Document content adheres strictly to required ESTD layout."""
        news = GeneratedNews(
            title="Next-Generation Clean Energy Breakthrough",
            subtitle="Commercial fusion approaches economic viability",
            category=ESTDCategory.DEVELOPMENTS,
            summary="Scientists achieve net-positive energy yield exceeding previous records.",
            content="Researchers at the National Ignition Facility demonstrated sustained reaction output over several consecutive attempts, demonstrating reproducibility and economic viability for baseline clean power generation.",
            source_name="Science Daily",
            source_url="https://sciencedaily.com/articles/fusion-energy-2026",
            generated_at=datetime(2026, 10, 6, 12, 0, 0, tzinfo=timezone.utc),
        )

        formatted = DocumentFormatter.format_document_content(
            news=news,
            article_id=101,
            original_published_at="2026-10-06 08:30:00 UTC",
        )

        assert "ESTD NEWS" in formatted
        assert "Title:\nNext-Generation Clean Energy Breakthrough" in formatted
        assert "Subtitle:\nCommercial fusion approaches economic viability" in formatted
        assert "Category:\nDevelopments" in formatted
        assert "ARTICLE" in formatted
        assert news.content in formatted
        assert "SOURCE INFORMATION" in formatted
        assert "Original Source:\nScience Daily" in formatted
        assert "Original Article:\nhttps://sciencedaily.com/articles/fusion-energy-2026" in formatted
        assert "Original Publication Date:\n2026-10-06 08:30:00 UTC" in formatted
