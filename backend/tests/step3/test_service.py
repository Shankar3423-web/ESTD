"""Unit tests for Step 3 ContentCleaningService."""
import pytest

from backend.step2_article_extraction.models import (
    ExtractedArticle,
    ExtractionMethod,
    ExtractionStatus,
)
from backend.step3_content_cleaning.models import CleanedArticle, CleaningStatus
from backend.step3_content_cleaning.services.content_cleaning_service import (
    ContentCleaningService,
)


def test_clean_valid_article(sample_extracted_article_clean):
    service = ContentCleaningService()
    result: CleanedArticle = service.clean_article(sample_extracted_article_clean)

    assert result.cleaning_status == CleaningStatus.SUCCESS
    assert result.cleaned_content is not None
    assert len(result.cleaned_content) > 50
    assert result.original_content == sample_extracted_article_clean.content
    assert result.title == sample_extracted_article_clean.title
    assert result.url == sample_extracted_article_clean.url
    assert result.category == "Developments"
    assert result.error_message is None


def test_clean_article_with_html(sample_extracted_article_with_html):
    service = ContentCleaningService()
    result: CleanedArticle = service.clean_article(sample_extracted_article_with_html)

    assert result.cleaning_status == CleaningStatus.SUCCESS
    assert "<p>" not in result.cleaned_content
    assert "<div>" not in result.cleaned_content
    assert "&amp;" not in result.cleaned_content
    assert "Google DeepMind announced its latest autonomous reasoning system" in result.cleaned_content
    assert "Advertisement" not in result.cleaned_content


def test_clean_article_with_boilerplate(sample_extracted_article_with_boilerplate):
    service = ContentCleaningService()
    result: CleanedArticle = service.clean_article(sample_extracted_article_with_boilerplate)

    assert result.cleaning_status == CleaningStatus.SUCCESS
    # Boilerplate lines should be stripped
    assert "We use cookies" not in result.cleaned_content
    assert "ADVERTISEMENT" not in result.cleaned_content
    assert "Sign up for our daily newsletter" not in result.cleaned_content
    assert "Share this article on Twitter" not in result.cleaned_content
    assert "All rights reserved" not in result.cleaned_content

    # Legitimate content preserved
    assert "European central bankers convened in Frankfurt" in result.cleaned_content
    assert "Analysts anticipate that borrowing rates will remain steady" in result.cleaned_content


def test_clean_article_null_or_empty_content():
    service = ContentCleaningService()
    article = ExtractedArticle(
        title="Empty Item",
        url="https://example.com/empty",
        source_type="rss",
        category="Technology",
        collected_at="2026-09-30T10:00:00Z",
        extraction_status=ExtractionStatus.EXTRACTION_FAILED,
        content=None,
    )
    result = service.clean_article(article)
    assert result.cleaning_status == CleaningStatus.CLEANING_FAILED
    assert result.cleaned_content is None
    assert "empty or contains no readable text" in result.error_message


def test_clean_article_content_only_boilerplate():
    service = ContentCleaningService()
    article = ExtractedArticle(
        title="Boilerplate Only Item",
        url="https://example.com/boilerplate",
        source_type="gnews",
        category="Business",
        collected_at="2026-09-30T10:00:00Z",
        extraction_status=ExtractionStatus.EXTRACTED,
        content="ADVERTISEMENT\n\nWe use cookies to improve your experience.\n\nSign up for our newsletter.",
    )
    result = service.clean_article(article)
    assert result.cleaning_status == CleaningStatus.CLEANING_FAILED
    assert result.cleaned_content is None
    assert "reduced to empty" in result.error_message or "below minimum threshold" in result.error_message


def test_clean_article_too_short_content():
    service = ContentCleaningService()
    article = ExtractedArticle(
        title="Short Item",
        url="https://example.com/short",
        source_type="gnews",
        category="Technology",
        collected_at="2026-09-30T10:00:00Z",
        extraction_status=ExtractionStatus.EXTRACTED,
        content="Hello world.",  # 12 chars, 2 words - below threshold
    )
    result = service.clean_article(article)
    assert result.cleaning_status == CleaningStatus.CLEANING_FAILED
    assert "below minimum threshold" in result.error_message


def test_clean_article_repeated_paragraphs_deduplicated():
    service = ContentCleaningService()
    repeated_content = (
        "Researchers at Oxford announced a milestone in molecular biology today.\n\n"
        "The findings suggest new avenues for therapeutic intervention.\n\n"
        "Researchers at Oxford announced a milestone in molecular biology today.\n\n"
        "Clinical trials will commence in the coming year."
    )
    article = ExtractedArticle(
        title="Oxford Molecular Biology Discovery",
        url="https://oxford.example.com/news",
        source_type="rss",
        category="Science",
        collected_at="2026-09-30T10:00:00Z",
        extraction_status=ExtractionStatus.EXTRACTED,
        content=repeated_content,
    )
    result = service.clean_article(article)
    assert result.cleaning_status == CleaningStatus.SUCCESS
    # Should only appear once
    assert result.cleaned_content.count("Researchers at Oxford announced a milestone in molecular biology today.") == 1
    assert "Clinical trials will commence" in result.cleaned_content


def test_clean_batch_with_mixed_articles(
    sample_extracted_article_clean, sample_extracted_article_with_boilerplate
):
    service = ContentCleaningService()
    empty_article = ExtractedArticle(
        title="Empty Item in Batch",
        url="https://example.com/batch-empty",
        source_type="rss",
        category="Technology",
        collected_at="2026-09-30T10:00:00Z",
        extraction_status=ExtractionStatus.EXTRACTION_FAILED,
        content=None,
    )
    batch = [
        sample_extracted_article_clean,
        sample_extracted_article_with_boilerplate,
        empty_article,
    ]

    results = service.clean_batch(batch)
    assert len(results) == 3
    assert results[0].cleaning_status == CleaningStatus.SUCCESS
    assert results[1].cleaning_status == CleaningStatus.SUCCESS
    assert results[2].cleaning_status == CleaningStatus.CLEANING_FAILED
