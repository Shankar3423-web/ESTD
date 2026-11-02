"""Unit tests for Step 3 models and schemas."""
import pytest
from pydantic import ValidationError

from backend.step2_article_extraction.models import ExtractedArticle, ExtractionStatus
from backend.step3_content_cleaning.models import CleanedArticle, CleaningStatus
from backend.step3_content_cleaning.schemas import (
    BatchCleaningRequest,
    BatchCleaningResponse,
    CleaningRequest,
    SingleCleaningResponse,
)


def test_cleaned_article_from_extracted_article_success(sample_extracted_article_clean):
    cleaned_text = "Cleaned version of article content."
    cleaned_article = CleanedArticle.from_extracted_article(
        sample_extracted_article_clean, cleaned_text
    )

    # Preserved Step 1 fields
    assert cleaned_article.title == sample_extracted_article_clean.title
    assert cleaned_article.url == sample_extracted_article_clean.url
    assert cleaned_article.category == sample_extracted_article_clean.category
    assert cleaned_article.source_name == sample_extracted_article_clean.source_name
    assert cleaned_article.source_type == sample_extracted_article_clean.source_type
    assert cleaned_article.author == sample_extracted_article_clean.author
    assert cleaned_article.published_at == sample_extracted_article_clean.published_at
    assert cleaned_article.collected_at == sample_extracted_article_clean.collected_at

    # Preserved Step 2 fields
    assert cleaned_article.canonical_url == sample_extracted_article_clean.canonical_url
    assert cleaned_article.extracted_at == sample_extracted_article_clean.extracted_at

    # Step 3 specific fields
    assert cleaned_article.cleaning_status == CleaningStatus.SUCCESS
    assert cleaned_article.cleaned_content == cleaned_text
    assert cleaned_article.content == cleaned_text
    assert cleaned_article.original_content == sample_extracted_article_clean.content
    assert cleaned_article.original_content_length == len(sample_extracted_article_clean.content)
    assert cleaned_article.cleaned_content_length == len(cleaned_text)
    assert cleaned_article.cleaned_at is not None
    assert cleaned_article.error_message is None


def test_cleaned_article_from_failure(sample_extracted_article_clean):
    cleaned_article = CleanedArticle.from_failure(
        sample_extracted_article_clean,
        error_message="Content was completely reduced to empty.",
    )

    assert cleaned_article.cleaning_status == CleaningStatus.CLEANING_FAILED
    assert cleaned_article.cleaned_content is None
    assert cleaned_article.content is None
    assert cleaned_article.cleaned_content_length == 0
    assert cleaned_article.error_message == "Content was completely reduced to empty."
    assert cleaned_article.title == sample_extracted_article_clean.title
    assert cleaned_article.url == sample_extracted_article_clean.url


def test_cleaned_article_validates_category():
    # Valid canonical categories
    from backend.common.constants.categories import VALID_CATEGORIES
    for cat in VALID_CATEGORIES:
        article = CleanedArticle(
            title="Sample Title",
            url="https://example.com/test",
            source_type="rss",
            category=cat,
            collected_at="2026-09-30T10:00:00Z",
            cleaning_status=CleaningStatus.SUCCESS,
        )
        assert article.category == cat

    # Invalid category
    with pytest.raises(ValidationError):
        CleanedArticle(
            title="Sample Title",
            url="https://example.com/test",
            source_type="rss",
            category="Sports & Entertainment",
            collected_at="2026-09-30T10:00:00Z",
            cleaning_status=CleaningStatus.SUCCESS,
        )


def test_cleaning_request_and_response_schemas(sample_extracted_article_clean):
    req = CleaningRequest(article=sample_extracted_article_clean)
    assert req.article.title == sample_extracted_article_clean.title

    cleaned = CleanedArticle.from_extracted_article(
        sample_extracted_article_clean, "Clean body text"
    )
    resp = SingleCleaningResponse(status="success", data=cleaned)
    assert resp.status == "success"
    assert resp.data.cleaned_content == "Clean body text"

    batch_req = BatchCleaningRequest(articles=[sample_extracted_article_clean])
    assert len(batch_req.articles) == 1

    batch_resp = BatchCleaningResponse(status="success", count=1, items=[cleaned])
    assert batch_resp.count == 1
    assert len(batch_resp.items) == 1
