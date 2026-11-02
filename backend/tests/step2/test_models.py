"""Unit tests for Step 2 ExtractedArticle model and factory methods."""
import pytest
from pydantic import ValidationError

from backend.step1_source_collection.models.news_item import NewsItem
from backend.step2_article_extraction.models import (
    ExtractedArticle,
    ExtractionMethod,
    ExtractionStatus,
)


def test_extracted_article_from_existing_content(sample_news_item_full_content):
    """Factory creates ExtractedArticle with status CONTENT_ALREADY_AVAILABLE and preserves metadata."""
    article = ExtractedArticle.from_existing_content(
        sample_news_item_full_content,
        content=sample_news_item_full_content.description,
    )

    assert article.extraction_status == ExtractionStatus.CONTENT_ALREADY_AVAILABLE
    assert article.extraction_method == ExtractionMethod.EXISTING_SOURCE_CONTENT
    assert article.error_message is None
    assert article.content == sample_news_item_full_content.description
    assert article.title == sample_news_item_full_content.title
    assert article.category == sample_news_item_full_content.category
    assert article.source_name == sample_news_item_full_content.source_name
    assert article.source_type == sample_news_item_full_content.source_type
    assert article.url == sample_news_item_full_content.url
    assert article.canonical_url == sample_news_item_full_content.url
    assert article.collected_at == sample_news_item_full_content.collected_at
    assert article.extracted_at is not None


def test_extracted_article_from_extracted(sample_news_item_snippet):
    """Factory creates ExtractedArticle with status EXTRACTED and extracted attributes."""
    extracted_content = "This is the newly extracted article body from the webpage."
    article = ExtractedArticle.from_extracted(
        news_item=sample_news_item_snippet,
        content=extracted_content,
        title="Updated Extracted Title",
        canonical_url="https://technews.example.com/canonical",
        author="Lead Researcher",
    )

    assert article.extraction_status == ExtractionStatus.EXTRACTED
    assert article.extraction_method == ExtractionMethod.ARTICLE_WEB_EXTRACTION
    assert article.error_message is None
    assert article.content == extracted_content
    assert article.title == "Updated Extracted Title"
    assert article.canonical_url == "https://technews.example.com/canonical"
    assert article.author == "Lead Researcher"
    assert article.category == sample_news_item_snippet.category
    assert article.source_type == sample_news_item_snippet.source_type


def test_extracted_article_from_failure(sample_news_item_snippet):
    """Factory creates ExtractedArticle with status EXTRACTION_FAILED without losing Step 1 fields."""
    article = ExtractedArticle.from_failure(
        news_item=sample_news_item_snippet,
        error_message="HTTP 404 Not Found",
    )

    assert article.extraction_status == ExtractionStatus.EXTRACTION_FAILED
    assert article.extraction_method is None
    assert article.content is None
    assert article.error_message == "HTTP 404 Not Found"
    assert article.title == sample_news_item_snippet.title
    assert article.category == sample_news_item_snippet.category
    assert article.url == sample_news_item_snippet.url


def test_extracted_article_invalid_category_rejected():
    """Invalid category cannot be set on ExtractedArticle."""
    with pytest.raises(ValidationError):
        ExtractedArticle(
            title="Some Title",
            url="https://example.com",
            source_type="gnews",
            category="InvalidCategory123",
            collected_at="2026-09-30T10:00:00Z",
            extraction_status=ExtractionStatus.EXTRACTED,
        )


def test_extracted_article_json_serialization(sample_news_item_full_content):
    """ExtractedArticle serializes to dict and JSON correctly."""
    article = ExtractedArticle.from_existing_content(
        sample_news_item_full_content,
        content=sample_news_item_full_content.description,
    )
    data = article.model_dump()
    assert data["extraction_status"] == "CONTENT_ALREADY_AVAILABLE"
    assert data["extraction_method"] == "existing_source_content"
    assert data["category"] == "Tech"
