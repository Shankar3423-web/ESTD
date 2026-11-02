"""Unit and service tests for Step 2 ExtractionService."""
from unittest.mock import AsyncMock, MagicMock
import pytest

from backend.step1_source_collection.models.news_item import NewsItem
from backend.step2_article_extraction.exceptions import (
    ArticleFetchHTTPError,
    ArticleFetchTimeoutError,
)
from backend.step2_article_extraction.extractors.article_extractor import ArticleExtractor
from backend.step2_article_extraction.fetchers.article_fetcher import ArticleFetcher
from backend.step2_article_extraction.models import (
    ExtractionMethod,
    ExtractionStatus,
)
from backend.step2_article_extraction.services.extraction_service import (
    ExtractionService,
)


@pytest.mark.asyncio
async def test_service_no_scrape_required_path(sample_news_item_full_content):
    """When NewsItem already has sufficient content, fetcher must NOT be called."""
    mock_fetcher = MagicMock(spec=ArticleFetcher)
    mock_fetcher.fetch_html = AsyncMock()

    service = ExtractionService(fetcher=mock_fetcher)
    result = await service.extract_article(sample_news_item_full_content)

    # CRITICAL: Verify fetcher was NEVER called
    mock_fetcher.fetch_html.assert_not_called()

    assert result.extraction_status == ExtractionStatus.CONTENT_ALREADY_AVAILABLE
    assert result.extraction_method == ExtractionMethod.EXISTING_SOURCE_CONTENT
    assert result.content == sample_news_item_full_content.description
    assert result.title == sample_news_item_full_content.title
    assert result.category == sample_news_item_full_content.category


@pytest.mark.asyncio
async def test_service_scrape_required_path(sample_news_item_snippet, valid_article_html):
    """When NewsItem has insufficient snippet, fetcher is called and content extracted."""
    mock_fetcher = MagicMock(spec=ArticleFetcher)
    mock_fetcher.fetch_html = AsyncMock(return_value=valid_article_html)

    service = ExtractionService(fetcher=mock_fetcher)
    result = await service.extract_article(sample_news_item_snippet)

    # Verify fetcher was called with the exact article URL
    mock_fetcher.fetch_html.assert_called_once_with(sample_news_item_snippet.url)

    assert result.extraction_status == ExtractionStatus.EXTRACTED
    assert result.extraction_method == ExtractionMethod.ARTICLE_WEB_EXTRACTION
    assert result.content is not None
    assert "Google DeepMind" in result.content
    assert result.author == "Dr. Alan Turing"
    assert result.category == sample_news_item_snippet.category


@pytest.mark.asyncio
async def test_service_fetch_failure_returns_structured_failure(sample_news_item_snippet):
    """HTTP fetch failures return a structured ExtractedArticle with EXTRACTION_FAILED."""
    mock_fetcher = MagicMock(spec=ArticleFetcher)
    mock_fetcher.fetch_html = AsyncMock(
        side_effect=ArticleFetchHTTPError(sample_news_item_snippet.url, 404, "Not Found")
    )

    service = ExtractionService(fetcher=mock_fetcher)
    result = await service.extract_article(sample_news_item_snippet)

    assert result.extraction_status == ExtractionStatus.EXTRACTION_FAILED
    assert result.extraction_method is None
    assert result.content is None
    assert "HTTP 404" in result.error_message
    assert result.title == sample_news_item_snippet.title
    assert result.url == sample_news_item_snippet.url


@pytest.mark.asyncio
async def test_service_timeout_returns_structured_failure(sample_news_item_snippet):
    """Timeout during fetch returns structured failure without crashing."""
    mock_fetcher = MagicMock(spec=ArticleFetcher)
    mock_fetcher.fetch_html = AsyncMock(
        side_effect=ArticleFetchTimeoutError(sample_news_item_snippet.url, 10.0)
    )

    service = ExtractionService(fetcher=mock_fetcher)
    result = await service.extract_article(sample_news_item_snippet)

    assert result.extraction_status == ExtractionStatus.EXTRACTION_FAILED
    assert result.extraction_method is None
    assert "timed out after 10.0s" in result.error_message


@pytest.mark.asyncio
async def test_service_extraction_failure_returns_structured_failure(
    sample_news_item_snippet, missing_body_html
):
    """When webpage has no readable article content, returns structured failure."""
    mock_fetcher = MagicMock(spec=ArticleFetcher)
    mock_fetcher.fetch_html = AsyncMock(return_value=missing_body_html)

    service = ExtractionService(fetcher=mock_fetcher)
    result = await service.extract_article(sample_news_item_snippet)

    assert result.extraction_status == ExtractionStatus.EXTRACTION_FAILED
    assert result.extraction_method is None
    assert "Extraction failed" in result.error_message


@pytest.mark.asyncio
async def test_service_batch_failure_isolation(
    sample_news_item_snippet,
    sample_news_item_full_content,
    valid_article_html,
):
    """Failure in one article in a batch does not crash or abort remaining articles."""
    # Item 1: Needs scrape -> succeeds
    item1 = sample_news_item_snippet.model_copy(update={"url": "https://item1.com/story"})

    # Item 2: Needs scrape -> fails with 500 server error
    item2 = NewsItem(
        title="Failing Article",
        description="Short snippet that fails",
        url="https://item2-fails.com/story",
        source_type="newsdata",
        category="Business",
    )

    # Item 3: Has full content -> no scrape needed
    item3 = sample_news_item_full_content

    async def mock_fetch_dispatcher(url: str) -> str:
        if "item1" in url:
            return valid_article_html
        elif "item2" in url:
            raise ArticleFetchHTTPError(url, 500, "Internal Server Error")
        return ""

    mock_fetcher = MagicMock(spec=ArticleFetcher)
    mock_fetcher.fetch_html = AsyncMock(side_effect=mock_fetch_dispatcher)

    service = ExtractionService(fetcher=mock_fetcher)
    results = await service.extract_batch([item1, item2, item3])

    assert len(results) == 3

    # Item 1 succeeded
    assert results[0].extraction_status == ExtractionStatus.EXTRACTED
    assert results[0].content is not None

    # Item 2 failed safely
    assert results[1].extraction_status == ExtractionStatus.EXTRACTION_FAILED
    assert "HTTP 500" in results[1].error_message

    # Item 3 used existing content without fetch
    assert results[2].extraction_status == ExtractionStatus.CONTENT_ALREADY_AVAILABLE
    assert results[2].content == item3.description
