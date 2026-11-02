"""Tests for Step 7 MCP retrieval integrity, source sufficiency gating, and content quality validation."""
import pytest
from unittest.mock import MagicMock

from backend.step7_content_generation.exceptions import (
    GenerationValidationError,
    InsufficientSourceContentError,
)
from backend.step7_content_generation.schemas.generated_news import GeneratedNews
from backend.step7_content_generation.services.mcp_generation_service import MCPGenerationService
from backend.step7_content_generation.validators.generation_validator import GenerationValidator


def test_mcp_generation_service_sql_selects_full_content():
    """Verify that MCP SQL query selects full content and does not truncate or select only summary."""
    mock_mcp = MagicMock()
    service = MCPGenerationService(mcp_service=mock_mcp, generation_service=MagicMock())

    sample_content = "This is a full rich article body with extensive background. " * 30
    mock_mcp.query_knowledge_source.return_value = [
        {
            "id": 42,
            "title": "Major Tech Breakthrough",
            "description": "Short description teaser.",
            "content": sample_content,
            "url": "https://example.com/tech-breakthrough",
            "source_name": "Tech News",
            "source_type": "rss",
            "author": "Tech Author",
            "published_at": "2026-10-06T10:00:00Z",
            "category": "Technology",
        }
    ]

    row = service.fetch_article_via_mcp(42)

    # Verify query was called with full content column
    called_sql = mock_mcp.query_knowledge_source.call_args[0][0]
    assert "content" in called_sql
    assert "description" in called_sql
    assert "LIMIT 1" in called_sql
    assert "SUBSTRING" not in called_sql
    assert "LEFT(" not in called_sql

    # Verify full content returned without alteration
    assert row["content"] == sample_content
    assert len(row["content"]) == len(sample_content)
    assert row["content"] != row["description"]


def test_source_sufficiency_gate_rejects_snippets():
    """Verify that short snippets or teasers (< 200 chars / < 30 words) are rejected."""
    service = MCPGenerationService(mcp_service=MagicMock(), generation_service=MagicMock())

    short_row = {
        "id": 101,
        "title": "Short Snippet Article",
        "content": "DeepMind announced a new AI system today in London.",  # ~50 chars, 8 words
        "url": "https://example.com/ai",
        "category": "Artificial Intelligence",
    }

    with pytest.raises(InsufficientSourceContentError) as exc_info:
        service.validate_article_eligibility(short_row)

    assert exc_info.value.code == "INSUFFICIENT_SOURCE_CONTENT"
    assert "insufficient for publication generation" in str(exc_info.value)


def test_source_sufficiency_gate_accepts_rich_content():
    """Verify that genuine full-length articles pass the sufficiency gate."""
    service = MCPGenerationService(mcp_service=MagicMock(), generation_service=MagicMock())

    rich_row = {
        "id": 102,
        "title": "Rich Publication Article",
        "content": (
            "Researchers have demonstrated a significant new method for training neural networks. "
            "The approach reduces compute requirements while retaining full benchmark accuracy. "
            "According to the published study, the architecture separates reasoning modules from memory retrieval, "
            "enabling highly specialized sub-networks to coordinate effectively on complex logical benchmarks. "
            "Independent analysts praised the work as a pivotal step forward for practical enterprise deployment."
        ),
        "url": "https://example.com/ai-rich",
        "category": "Artificial Intelligence",
    }

    # Should not raise
    service.validate_article_eligibility(rich_row)


def test_generation_validator_rejects_repeated_paragraphs():
    """Verify that validator catches repetitive padding / repeated paragraphs."""
    validator = GenerationValidator()

    repeated_para = "This is a repeated paragraph that artificially inflates word count. " * 3
    body_with_repeats = f"{repeated_para}\n\n{repeated_para}\n\n{repeated_para}"

    candidate = GeneratedNews(
        title="Valid Headline That Is Factual",
        category="Tech",
        summary="This is a concise executive summary with useful context.",
        content=body_with_repeats,
        source_name="Tech Source",
        source_url="https://example.com/tech",
    )

    with pytest.raises(GenerationValidationError) as exc_info:
        validator.validate_generated_news(candidate)

    assert "contains repeated duplicate paragraphs" in str(exc_info.value)


def test_generation_validator_rejects_summary_as_article():
    """Verify that validator rejects an article that merely duplicates the executive summary."""
    validator = GenerationValidator()

    same_text = (
        "This exact text is used for both summary and article body to test rejection by the validator. "
        "It is deliberately made longer than one hundred characters to ensure Pydantic model validation passes."
    )

    candidate = GeneratedNews(
        title="Valid Headline",
        category="Tech",
        summary=same_text,
        content=same_text,
        source_name="Tech Source",
        source_url="https://example.com/tech",
    )

    with pytest.raises(GenerationValidationError) as exc_info:
        validator.validate_generated_news(candidate)

    assert "identical to executive summary" in str(exc_info.value)

