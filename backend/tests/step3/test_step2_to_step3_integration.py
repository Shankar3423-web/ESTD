"""Integration tests validating the pipeline contract between Step 2 ExtractedArticle and Step 3 CleanedArticle."""
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


def test_step2_to_step3_full_provenance_preservation():
    """Verify that every field from Step 2 ExtractedArticle survives into Step 3 CleanedArticle."""
    extracted = ExtractedArticle(
        title="Breakthrough in Quantum Telemetry",
        description="A major physics achievement at cryogenic temperatures.",
        url="https://quantum.example.com/telemetry/2026",
        source_name="Quantum Reports",
        source_type="rss",
        author="Dr. Richard Feynman II",
        published_at="2026-09-30T07:00:00Z",
        category="Science",
        image_url="https://quantum.example.com/img/crystal.png",
        collected_at="2026-09-30T07:15:00Z",
        canonical_url="https://quantum.example.com/telemetry/2026/canonical",
        extraction_status=ExtractionStatus.EXTRACTED,
        extraction_method=ExtractionMethod.ARTICLE_WEB_EXTRACTION,
        extracted_at="2026-09-30T07:15:08Z",
        content=(
            "<p>Physicists at the High Energy Consortium have demonstrated quantum telemetry "
            "over a forty-kilometer subterranean optical fiber network.</p>\n\n"
            "ADVERTISEMENT\n\n"
            "<p>The technique maintains coherence across entangled photon pairs despite thermal fluctuations.</p>"
        ),
    )

    service = ContentCleaningService()
    cleaned: CleanedArticle = service.clean_article(extracted)

    # 1. Verification of Step 1 metadata preservation
    assert cleaned.title == extracted.title
    assert cleaned.description == extracted.description
    assert cleaned.url == extracted.url
    assert cleaned.source_name == extracted.source_name
    assert cleaned.source_type == extracted.source_type
    assert cleaned.author == extracted.author
    assert cleaned.published_at == extracted.published_at
    assert cleaned.category == extracted.category
    assert cleaned.image_url == extracted.image_url
    assert cleaned.collected_at == extracted.collected_at

    # 2. Verification of Step 2 metadata preservation
    assert cleaned.canonical_url == extracted.canonical_url
    assert cleaned.extracted_at == extracted.extracted_at
    assert cleaned.extraction_status == "EXTRACTED"
    assert cleaned.extraction_method == "article_web_extraction"

    # 3. Verification of Step 3 cleaning results
    assert cleaned.cleaning_status == CleaningStatus.SUCCESS
    assert cleaned.cleaned_at is not None
    assert cleaned.original_content == extracted.content
    assert cleaned.original_content_length == len(extracted.content)
    assert cleaned.cleaned_content_length == len(cleaned.cleaned_content)
    assert cleaned.content == cleaned.cleaned_content

    # Content cleaned properly
    assert "<p>" not in cleaned.cleaned_content
    assert "ADVERTISEMENT" not in cleaned.cleaned_content
    assert "Physicists at the High Energy Consortium" in cleaned.cleaned_content
    assert "entangled photon pairs" in cleaned.cleaned_content


def test_step2_to_step3_with_extraction_failure():
    """Verify that when Step 2 produced an extraction failure, Step 3 handles it gracefully."""
    failed_extracted = ExtractedArticle(
        title="Unreachable Article",
        url="https://failed.example.com/down",
        source_type="newsdata",
        category="Technology",
        collected_at="2026-09-30T08:00:00Z",
        extraction_status=ExtractionStatus.EXTRACTION_FAILED,
        error_message="HTTP 502 Bad Gateway",
        content=None,
    )

    service = ContentCleaningService()
    cleaned = service.clean_article(failed_extracted)

    assert cleaned.cleaning_status == CleaningStatus.CLEANING_FAILED
    assert cleaned.cleaned_content is None
    assert cleaned.title == "Unreachable Article"
    assert cleaned.category == "Tech"
    assert "empty or contains no readable text" in cleaned.error_message
