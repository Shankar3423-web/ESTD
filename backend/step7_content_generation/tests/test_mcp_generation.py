"""Unit tests for MCPGenerationService and PostgreSQL MCP integration layer."""
from unittest.mock import MagicMock
import pytest

from backend.common.constants.categories import ESTDCategory
from backend.step7_content_generation.exceptions import ArticleIneligibleError
from backend.step7_content_generation.schemas.generated_news import GeneratedNews
from backend.step7_content_generation.schemas.generation_request import (
    ArticleGenerationRequest,
)
from backend.step7_content_generation.services.mcp_generation_service import (
    MCPGenerationService,
)


@pytest.fixture
def mock_mcp_article_row():
    return {
        "id": 101,
        "title": "Quantum Supremacy Experiment Reaches New Milestone",
        "description": "Researchers achieve verifiable computational advantage.",
        "content": (
            "Physicists at the national laboratory demonstrated quantum supremacy across a 72-qubit "
            "superconducting system. The calculations required 200 seconds, an operation estimated to "
            "require 10,000 years on classical supercomputing clusters."
        ),
        "url": "https://science.org/quantum-72",
        "source_name": "Science Journal",
        "source_type": "rss",
        "author": "Dr. Sarah Chen",
        "published_at": "2026-10-05T08:00:00Z",
        "category": "Developments",
    }


def test_fetch_article_via_mcp_success(mock_mcp_article_row):
    """Verify that fetch_article_via_mcp executes SQL through MCPService and returns row."""
    mock_mcp = MagicMock()
    mock_mcp.query_knowledge_source.return_value = [mock_mcp_article_row]

    service = MCPGenerationService(mcp_service=mock_mcp)
    article = service.fetch_article_via_mcp(101)

    assert article["id"] == 101
    assert article["title"] == "Quantum Supremacy Experiment Reaches New Milestone"
    assert article["category"] == "Developments"
    assert mock_mcp.query_knowledge_source.call_count == 1
    # Ensure SQL generated is a SELECT query targeting news_articles
    call_sql = mock_mcp.query_knowledge_source.call_args[0][0]
    assert "SELECT" in call_sql
    assert "news_articles" in call_sql
    assert "WHERE id = 101" in call_sql


def test_fetch_article_not_found_raises_ineligible():
    """Verify that a non-existent article ID raises ArticleIneligibleError."""
    mock_mcp = MagicMock()
    mock_mcp.query_knowledge_source.return_value = []  # No rows

    service = MCPGenerationService(mcp_service=mock_mcp)
    with pytest.raises(ArticleIneligibleError) as exc_info:
        service.fetch_article_via_mcp(99999)
    assert "not found" in str(exc_info.value).lower()


def test_validate_article_eligibility_failures():
    """Verify eligibility rules reject malformed database rows."""
    service = MCPGenerationService(mcp_service=MagicMock())

    # Empty title
    with pytest.raises(ArticleIneligibleError):
        service.validate_article_eligibility(
            {"id": 1, "title": "", "content": "A" * 100, "category": "Developments", "url": "https://example.com"}
        )

    # Content too short (< 50 chars)
    with pytest.raises(ArticleIneligibleError):
        service.validate_article_eligibility(
            {"id": 2, "title": "Headline", "content": "Too short", "category": "Developments", "url": "https://example.com"}
        )

    # Invalid category
    with pytest.raises(ArticleIneligibleError):
        service.validate_article_eligibility(
            {"id": 3, "title": "Headline", "content": "A" * 100, "category": "CryptoNews", "url": "https://example.com"}
        )


def test_duplicate_generation_cache_prevents_reprocessing(mock_mcp_article_row):
    """Verify that consecutive requests for the same article ID reuse the cached generation."""
    mock_mcp = MagicMock()
    mock_mcp.query_knowledge_source.return_value = [mock_mcp_article_row]

    mock_gen = MagicMock()
    mock_gen.settings.gemini_model = "gemini-2.5-flash"
    mock_news = GeneratedNews(
        title="Synthesized Quantum Advantage",
        category=ESTDCategory.DEVELOPMENTS,
        summary="Quantum milestone achieved with superconducting qubit system.",
        content="Physicists demonstrated verifiable computational speedups using superconducting processors. The results confirm multi-year theoretical predictions with reproducible precision.",
        source_name="Science Journal",
        source_url="https://science.org/quantum-72",
    )
    mock_gen.generate_news.return_value = mock_news

    service = MCPGenerationService(mcp_service=mock_mcp, generation_service=mock_gen)
    req = ArticleGenerationRequest(article_id=101)

    # First call: triggers MCP fetch and generation
    resp1 = service.generate_from_mcp_article(req)
    assert resp1.success is True
    assert mock_gen.generate_news.call_count == 1
    assert mock_mcp.query_knowledge_source.call_count == 1

    # Second call for same article: returned from cache, no new generation call!
    resp2 = service.generate_from_mcp_article(req)
    assert resp2.success is True
    assert resp2.data.title == resp1.data.title
    assert mock_gen.generate_news.call_count == 1  # Still 1, was not called again!

    # Force regenerate: bypasses cache and regenerates
    resp3 = service.generate_from_mcp_article(req, force_regenerate=True)
    assert resp3.success is True
    assert mock_gen.generate_news.call_count == 2
