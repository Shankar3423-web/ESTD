"""Tests verifying article creation, validation, timestamp handling, and retrieval by ID."""
from datetime import datetime, timezone
import pytest
from pydantic import ValidationError

from backend.common.constants.categories import VALID_CATEGORIES
from backend.step5_knowledge_source.exceptions import (
    ArticleNotFoundError,
    InvalidArticleDataError,
)
from backend.step5_knowledge_source.schemas.article_schemas import ArticleCreateRequest
from backend.step5_knowledge_source.services.knowledge_service import KnowledgeSourceService


def test_create_article_all_five_categories(clean_knowledge_db):
    """Verify that articles can be created and retrieved across all 5 canonical categories."""
    service = KnowledgeSourceService()

    for idx, cat in enumerate(VALID_CATEGORIES):
        req = ArticleCreateRequest(
            title=f"Test Headline for {cat}",
            description=f"Description for {cat} article.",
            content=f"Detailed body content for article covering topic in {cat}.",
            url=f"https://example.com/test-article-category-{idx}",
            source_name=f"{cat} Weekly",
            source_type="rss",
            author="Test Author",
            published_at="2026-10-01T12:00:00Z",
            category=cat,
        )
        art = service.create_article(req)
        assert art.id is not None
        assert art.category == cat
        assert art.category_id is not None

        # Verify retrieval
        fetched = service.get_article_by_id(art.id)
        assert fetched.id == art.id
        assert fetched.title == req.title
        assert fetched.category == cat


def test_missing_required_fields_rejected():
    """Verify Pydantic validation rejects empty title, content, or URL."""
    # Empty title
    with pytest.raises(ValidationError):
        ArticleCreateRequest(
            title="",
            content="Valid content...",
            url="https://example.com/valid",
            category="Technology",
        )

    # Empty content
    with pytest.raises(ValidationError):
        ArticleCreateRequest(
            title="Valid title",
            content="",
            url="https://example.com/valid",
            category="Technology",
        )

    # Empty URL
    with pytest.raises(ValidationError):
        ArticleCreateRequest(
            title="Valid title",
            content="Valid content...",
            url="",
            category="Technology",
        )


def test_timestamps_are_timezone_aware(clean_knowledge_db, sample_ai_article_payload):
    """Verify that stored timestamps are timezone-aware UTC objects."""
    service = KnowledgeSourceService()
    req = ArticleCreateRequest.model_validate(sample_ai_article_payload)
    art = service.create_article(req)

    assert art.created_at is not None
    assert art.created_at.tzinfo is not None
    assert art.collected_at is not None
    assert art.collected_at.tzinfo is not None
    if art.published_at is not None:
        assert art.published_at.tzinfo is not None


def test_get_article_by_id_not_found():
    """Verify that fetching a non-existent article ID raises ArticleNotFoundError."""
    service = KnowledgeSourceService()
    with pytest.raises(ArticleNotFoundError) as exc_info:
        service.get_article_by_id(99999999)
    assert exc_info.value.status_code == 404


def test_delete_article_success(clean_knowledge_db, sample_ai_article_payload):
    """Verify deleting an existing article succeeds and subsequent fetch raises 404."""
    service = KnowledgeSourceService()
    req = ArticleCreateRequest.model_validate(sample_ai_article_payload)
    art = service.create_article(req)

    deleted = service.delete_article(art.id)
    assert deleted is True

    with pytest.raises(ArticleNotFoundError):
        service.get_article_by_id(art.id)
