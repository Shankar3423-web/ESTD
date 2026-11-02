"""Integration and endpoint tests for Step 2 Article Extraction API."""
from unittest.mock import AsyncMock, patch
import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.step2_article_extraction.exceptions import (
    ArticleFetchConnectionError,
    ArticleFetchHTTPError,
)
from backend.step2_article_extraction.models import (
    ExtractionMethod,
    ExtractionStatus,
)


@pytest.fixture
def test_client() -> TestClient:
    """Create FastAPI TestClient."""
    return TestClient(app)


# ============================================================================
# Single Extraction Endpoint Tests
# ============================================================================

def test_extract_endpoint_success(test_client, valid_article_html):
    """POST /extract with valid article snippet successfully fetches and extracts body."""
    payload = {
        "title": "DeepMind Unveils Next-Gen AI System",
        "description": "Short snippet describing the announcement.",
        "url": "https://technews.example.com/articles/deepmind-breakthrough",
        "source_name": "TechNews",
        "source_type": "gnews",
        "category": "Artificial Intelligence",
        "collected_at": "2026-09-30T10:00:00Z",
    }

    with patch(
        "backend.step2_article_extraction.fetchers.article_fetcher.ArticleFetcher.fetch_html",
        new_callable=AsyncMock,
    ) as mock_fetch:
        mock_fetch.return_value = valid_article_html

        response = test_client.post("/api/v1/article-extraction/extract", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        article = data["data"]
        assert article["extraction_status"] == ExtractionStatus.EXTRACTED
        assert article["extraction_method"] == ExtractionMethod.ARTICLE_WEB_EXTRACTION
        assert "Google DeepMind" in article["content"]
        assert article["author"] == "Dr. Alan Turing"
        assert article["category"] == "Tech"


def test_extract_endpoint_existing_content_no_scrape(test_client, sample_news_item_full_content):
    """POST /extract with already sufficient content succeeds without external fetch."""
    payload = sample_news_item_full_content.model_dump()

    with patch(
        "backend.step2_article_extraction.fetchers.article_fetcher.ArticleFetcher.fetch_html",
        new_callable=AsyncMock,
    ) as mock_fetch:
        response = test_client.post("/api/v1/article-extraction/extract", json=payload)

        # Assert no fetch took place
        mock_fetch.assert_not_called()

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        article = data["data"]
        assert article["extraction_status"] == ExtractionStatus.CONTENT_ALREADY_AVAILABLE
        assert article["extraction_method"] == ExtractionMethod.EXISTING_SOURCE_CONTENT
        assert article["content"] == sample_news_item_full_content.description


def test_extract_endpoint_invalid_url_returns_400(test_client):
    """POST /extract with invalid URL scheme returns controlled 400 Bad Request."""
    payload = {
        "title": "Invalid URL Item",
        "description": "Some description",
        "url": "ftp://malformed-url-format",
        "source_type": "gnews",
        "category": "Technology",
    }
    response = test_client.post("/api/v1/article-extraction/extract", json=payload)
    assert response.status_code == 400
    err = response.json()
    assert "error" in err
    assert err["error"]["code"] == "INVALID_ARTICLE_URL"


def test_extract_endpoint_ssrf_url_returns_400(test_client):
    """POST /extract with private IP address returns controlled 400 Bad Request."""
    payload = {
        "title": "Private IP Item",
        "description": "Some description",
        "url": "http://127.0.0.1:8000/internal-secrets",
        "source_type": "gnews",
        "category": "Technology",
    }
    response = test_client.post("/api/v1/article-extraction/extract", json=payload)
    assert response.status_code == 400
    err = response.json()
    assert "error" in err
    assert err["error"]["code"] == "SSRF_SECURITY_REJECTION"


def test_extract_endpoint_unreachable_url_returns_controlled_failure(test_client):
    """POST /extract with network failure returns 200 with EXTRACTION_FAILED."""
    payload = {
        "title": "Unreachable Article",
        "description": "Short snippet",
        "url": "https://unreachable-external-site.example.com/story",
        "source_type": "newsdata",
        "category": "Business",
    }

    with patch(
        "backend.step2_article_extraction.fetchers.article_fetcher.ArticleFetcher.fetch_html",
        new_callable=AsyncMock,
    ) as mock_fetch:
        mock_fetch.side_effect = ArticleFetchConnectionError(
            payload["url"], "Failed to establish connection"
        )

        response = test_client.post("/api/v1/article-extraction/extract", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "failed"
        article = data["data"]
        assert article["extraction_status"] == ExtractionStatus.EXTRACTION_FAILED
        assert article["content"] is None
        assert "Failed to establish connection" in article["error_message"]


def test_extract_endpoint_missing_body_returns_controlled_failure(
    test_client, missing_body_html
):
    """POST /extract with page lacking extractable content returns 200 with EXTRACTION_FAILED."""
    payload = {
        "title": "Paywalled Article",
        "description": "Short snippet",
        "url": "https://paywall.example.com/exclusive",
        "source_type": "rss",
        "category": "Business",
    }

    with patch(
        "backend.step2_article_extraction.fetchers.article_fetcher.ArticleFetcher.fetch_html",
        new_callable=AsyncMock,
    ) as mock_fetch:
        mock_fetch.return_value = missing_body_html

        response = test_client.post("/api/v1/article-extraction/extract", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "failed"
        article = data["data"]
        assert article["extraction_status"] == ExtractionStatus.EXTRACTION_FAILED
        assert "Extraction failed" in article["error_message"]


def test_extract_endpoint_wrapped_payload_supported(test_client, sample_news_item_full_content):
    """POST /extract also accepts wrapped {'news_item': {...}} payload."""
    payload = {"news_item": sample_news_item_full_content.model_dump()}
    response = test_client.post("/api/v1/article-extraction/extract", json=payload)
    assert response.status_code == 200
    assert response.json()["status"] == "success"


# ============================================================================
# Batch Extraction Endpoint Tests
# ============================================================================

def test_extract_batch_endpoint(test_client, valid_article_html, sample_news_item_full_content):
    """POST /extract-batch processes list of NewsItems with failure isolation."""
    item1 = {
        "title": "Needs Scrape",
        "description": "Short snippet",
        "url": "https://item1.example.com/story",
        "source_type": "gnews",
        "category": "Technology",
    }
    item2 = sample_news_item_full_content.model_dump()

    with patch(
        "backend.step2_article_extraction.fetchers.article_fetcher.ArticleFetcher.fetch_html",
        new_callable=AsyncMock,
    ) as mock_fetch:
        mock_fetch.return_value = valid_article_html

        response = test_client.post(
            "/api/v1/article-extraction/extract-batch",
            json=[item1, item2],
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["count"] == 2
        items = data["items"]
        assert items[0]["extraction_status"] == ExtractionStatus.EXTRACTED
        assert items[1]["extraction_status"] == ExtractionStatus.CONTENT_ALREADY_AVAILABLE
