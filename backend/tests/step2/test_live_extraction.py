"""Controlled live integration tests against real public web pages."""
import pytest
import httpx

from backend.step1_source_collection.models.news_item import NewsItem
from backend.step2_article_extraction.models import ExtractionStatus
from backend.step2_article_extraction.services.extraction_service import (
    ExtractionService,
)

# Test URLs from reliable public domains with diverse layouts
LIVE_TEST_URLS = [
    {
        "url": "https://en.wikipedia.org/wiki/Artificial_intelligence",
        "category": "Tech",
        "title": "Artificial intelligence - Wikipedia",
    },
    {
        "url": "https://arstechnica.com/gadgets/",
        "category": "Tech",
        "title": "Ars Technica Gadgets",
    },
]


@pytest.mark.asyncio
async def test_live_webpage_fetching_and_extraction():
    """Live integration test verifying real HTTP fetch and extraction pipeline."""
    service = ExtractionService()

    for target in LIVE_TEST_URLS:
        item = NewsItem(
            title=target["title"],
            description="Snippet needing full page fetch",
            url=target["url"],
            source_type="live_test",
            category=target["category"],
        )

        try:
            result = await service.extract_article(item)
            # The test confirms that the live fetcher + extractor executes end-to-end without crashing
            assert result.category == target["category"]
            assert result.url == target["url"]
            if result.extraction_status == ExtractionStatus.EXTRACTED:
                assert result.content is not None
                assert len(result.content) > 50
            else:
                # If a site blocked or rate-limited, it must be recorded cleanly as EXTRACTION_FAILED
                assert result.extraction_status == ExtractionStatus.EXTRACTION_FAILED
                assert result.error_message is not None
        except httpx.ConnectError:
            pytest.skip("External internet access unavailable during test run.")
