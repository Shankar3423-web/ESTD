"""Integration tests validating the pipeline contract between Step 1 NewsItem and Step 2 ExtractedArticle."""
from unittest.mock import AsyncMock, patch
import pytest

from backend.step1_source_collection.models.news_item import NewsItem
from backend.step2_article_extraction.models import (
    ExtractedArticle,
    ExtractionMethod,
    ExtractionStatus,
)
from backend.step2_article_extraction.services.extraction_service import (
    ExtractionService,
)


@pytest.mark.asyncio
async def test_step1_to_step2_preserves_all_metadata_on_extract(valid_article_html):
    """Verify that every Step 1 metadata field is preserved in the resulting ExtractedArticle."""
    step1_item = NewsItem(
        title="Frontier AI Model Released",
        description="Brief summary from Step 1 news aggregator.",
        url="https://frontier.example.com/models/2026",
        source_name="VentureBeat",
        source_type="gnews",
        author="Tech Reporter",
        published_at="2026-09-30T08:00:00Z",
        category="Artificial Intelligence",
        image_url="https://frontier.example.com/thumb.png",
        collected_at="2026-09-30T08:30:00Z",
    )

    with patch(
        "backend.step2_article_extraction.fetchers.article_fetcher.ArticleFetcher.fetch_html",
        new_callable=AsyncMock,
    ) as mock_fetch:
        mock_fetch.return_value = valid_article_html

        service = ExtractionService()
        result: ExtractedArticle = await service.extract_article(step1_item)

        # 1. Preserved Step 1 fields
        assert result.category == step1_item.category
        assert result.source_type == step1_item.source_type
        assert result.url == step1_item.url
        assert result.collected_at == step1_item.collected_at
        assert result.description == step1_item.description

        # 2. Step 2 added fields
        assert result.content is not None
        assert len(result.content) > 100
        assert result.extraction_status == ExtractionStatus.EXTRACTED
        assert result.extraction_method == ExtractionMethod.ARTICLE_WEB_EXTRACTION
        assert result.extracted_at is not None
        assert result.error_message is None


@pytest.mark.asyncio
async def test_step1_to_step2_preserves_all_metadata_on_existing_content():
    """Verify that when Step 1 already provides full content, all fields are preserved and no scrape happens."""
    full_content = (
        "European space agencies have officially inaugurated a new constellation of low-orbit "
        "atmospheric monitoring satellites equipped with high-resolution spectroscopic sensors. "
        "The multi-year project aims to deliver real-time greenhouse gas dissipation maps with unprecedented "
        "spatial resolution to assist international climate mitigation and verification protocols."
    )
    step1_item = NewsItem(
        title="Atmospheric Satellite Constellation Launched",
        description=full_content,
        url="https://space.example.com/satellites",
        source_name="ESA Bulletin",
        source_type="rss",
        author="ESA Mission Team",
        published_at="2026-09-29T12:00:00Z",
        category="Science",
        image_url="https://space.example.com/sat.jpg",
        collected_at="2026-09-29T12:30:00Z",
    )

    with patch(
        "backend.step2_article_extraction.fetchers.article_fetcher.ArticleFetcher.fetch_html",
        new_callable=AsyncMock,
    ) as mock_fetch:
        service = ExtractionService()
        result: ExtractedArticle = await service.extract_article(step1_item)

        mock_fetch.assert_not_called()

        assert result.category == "Developments"
        assert result.source_type == "rss"
        assert result.source_name == "ESA Bulletin"
        assert result.url == "https://space.example.com/satellites"
        assert result.content == full_content
        assert result.extraction_status == ExtractionStatus.CONTENT_ALREADY_AVAILABLE
        assert result.extraction_method == ExtractionMethod.EXISTING_SOURCE_CONTENT


@pytest.mark.asyncio
async def test_step1_to_step2_preserves_metadata_on_failure():
    """Verify that when extraction fails, Step 1 metadata is not discarded."""
    step1_item = NewsItem(
        title="Unreachable News Story",
        description="A short snippet that cannot be scraped.",
        url="https://down.example.com/offline-story",
        source_name="Offline Source",
        source_type="newsdata",
        category="Business",
        collected_at="2026-09-30T11:00:00Z",
    )

    with patch(
        "backend.step2_article_extraction.fetchers.article_fetcher.ArticleFetcher.fetch_html",
        new_callable=AsyncMock,
    ) as mock_fetch:
        mock_fetch.side_effect = Exception("DNS resolution failed")

        service = ExtractionService()
        result: ExtractedArticle = await service.extract_article(step1_item)

        assert result.category == "Business & Finance"
        assert result.source_type == "newsdata"
        assert result.source_name == "Offline Source"
        assert result.url == "https://down.example.com/offline-story"
        assert result.extraction_status == ExtractionStatus.EXTRACTION_FAILED
        assert result.content is None
        assert "DNS resolution failed" in result.error_message
