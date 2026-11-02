"""Tests verifying duplicate protection at repository, service, and database levels."""
import pytest
from sqlalchemy.orm import Session

from backend.database.connection.session import get_db_session
from backend.step5_knowledge_source.exceptions import ArticleDuplicateError
from backend.step5_knowledge_source.schemas.article_schemas import ArticleCreateRequest
from backend.step5_knowledge_source.services.knowledge_service import KnowledgeSourceService


def test_duplicate_url_rejected_by_service(clean_knowledge_db, sample_ai_article_payload):
    """Verify that submitting an article with an already stored normalized URL raises ArticleDuplicateError."""
    service = KnowledgeSourceService()

    # First persistence succeeds
    req1 = ArticleCreateRequest.model_validate(sample_ai_article_payload)
    art1 = service.create_article(req1)
    assert art1.id is not None

    # Second persistence with same URL must fail
    req2 = ArticleCreateRequest.model_validate(sample_ai_article_payload)
    with pytest.raises(ArticleDuplicateError) as exc_info:
        service.create_article(req2)

    assert "duplicate" in exc_info.value.code.lower()
    assert exc_info.value.status_code == 409


def test_duplicate_content_hash_rejected_different_url(clean_knowledge_db, sample_ai_article_payload):
    """Verify that submitting an article with identical body content but different URL raises ArticleDuplicateError."""
    service = KnowledgeSourceService()

    # First persistence succeeds
    req1 = ArticleCreateRequest.model_validate(sample_ai_article_payload)
    service.create_article(req1)

    # Second persistence with different URL but same exact content body
    payload2 = dict(sample_ai_article_payload)
    payload2["url"] = "https://example.com/different-url-same-story"
    payload2["title"] = "Different Title Same Content"
    req2 = ArticleCreateRequest.model_validate(payload2)

    with pytest.raises(ArticleDuplicateError) as exc_info:
        service.create_article(req2)

    assert exc_info.value.status_code == 409


def test_step4_duplicate_result_rejected(clean_knowledge_db, sample_step4_duplicate_result):
    """Verify that a Step 4 DuplicateCheckResult marked as DUPLICATE is rejected from persistence."""
    service = KnowledgeSourceService()

    with pytest.raises(ArticleDuplicateError) as exc_info:
        service.persist_from_step4(sample_step4_duplicate_result)

    assert "duplicate" in exc_info.value.code.lower()
    assert exc_info.value.status_code == 409


def test_step4_unique_result_accepted(clean_knowledge_db, sample_step4_unique_result):
    """Verify that a Step 4 DuplicateCheckResult marked as UNIQUE is persisted successfully."""
    service = KnowledgeSourceService()

    art = service.persist_from_step4(sample_step4_unique_result)
    assert art.id is not None
    assert art.title == sample_step4_unique_result.article.title
    assert art.category == "Developments"
    assert art.normalized_url == sample_step4_unique_result.decision.normalized_url
    assert art.content_hash == sample_step4_unique_result.decision.content_hash
