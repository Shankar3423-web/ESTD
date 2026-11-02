"""Integration tests verifying Step 3 -> Step 4 and full Step 1 -> 2 -> 3 -> 4 pipeline."""
import pytest
from sqlalchemy.orm import Session

from backend.step1_source_collection.models.news_item import NewsItem
from backend.step2_article_extraction.models.extracted_article import ExtractedArticle
from backend.step2_article_extraction.services.extraction_service import ExtractionService
from backend.step3_content_cleaning.models.cleaned_article import CleanedArticle
from backend.step3_content_cleaning.services.content_cleaning_service import (
    ContentCleaningService,
)
from backend.step4_duplicate_detection.config import DuplicateDetectionConfig
from backend.step4_duplicate_detection.models.duplicate_record import (
    DuplicateReason,
    DuplicateStatus,
)
from backend.step4_duplicate_detection.services.duplicate_detection_service import (
    DuplicateDetectionService,
)


@pytest.mark.usefixtures("clean_db")
class TestStep3ToStep4Integration:
    """Integration suite between Step 3 Content Cleaning and Step 4 Duplicate Detection."""

    def test_step3_cleaned_article_to_step4_preserves_provenance(
        self,
        db_session: Session,
        sample_cleaned_article: CleanedArticle,
    ):
        service = DuplicateDetectionService(
            config=DuplicateDetectionConfig(
                enable_historical_detection=True,
                persist_unique_articles=True,
            )
        )

        result = service.check_article(sample_cleaned_article, session=db_session)

        # 1. Output structure verification
        assert result.status == "unique"
        assert result.decision.status == DuplicateStatus.UNIQUE
        assert result.decision.is_duplicate is False

        # 2. Complete provenance retention
        article = result.article
        assert article.title == sample_cleaned_article.title
        assert article.url == sample_cleaned_article.url
        assert article.canonical_url == sample_cleaned_article.canonical_url
        assert article.category == sample_cleaned_article.category
        assert article.source_type == sample_cleaned_article.source_type
        assert article.source_name == sample_cleaned_article.source_name
        assert article.author == sample_cleaned_article.author
        assert article.cleaned_content == sample_cleaned_article.cleaned_content
        assert article.cleaning_status == sample_cleaned_article.cleaning_status
        assert article.collected_at == sample_cleaned_article.collected_at

    @pytest.mark.asyncio
    async def test_full_pipeline_step1_to_step2_to_step3_to_step4(
        self,
        db_session: Session,
    ):
        """End-to-End Test: Step 1 -> Step 2 -> Step 3 -> Step 4."""
        # -----------------------------------------------------------------
        # STEP 1: Collected NewsItem
        # -----------------------------------------------------------------
        item = NewsItem(
            title="Next-Generation Solid-State Battery Enters Pilot Production",
            description="Solid-state battery cells manufactured for automotive endurance testing.",
            url="https://techdaily.example.com/energy/solid-state-pilot",
            source_name="TechDaily",
            source_type="rss",
            author="Marcus Vance",
            published_at="2026-10-01T10:00:00Z",
            category="Technology",
            collected_at="2026-10-01T10:15:00Z",
        )

        # -----------------------------------------------------------------
        # STEP 2: Extraction
        # -----------------------------------------------------------------
        raw_body = (
            "<p>Researchers today announced the successful completion of pilot manufacturing "
            "runs for an automotive-grade solid-state electrolyte battery cell.</p>\n\n"
            "<div class='ad-banner'>ADVERTISEMENT</div>\n\n"
            "<p>The cell demonstrates an energy density of 480 Wh/kg while retaining ninety-two "
            "percent capacity after one thousand rapid charge cycles at ambient temperatures.</p>\n\n"
            "Sign up for our newsletter to get clean energy updates delivered to your inbox.\n\n"
            "<p>Commercial scaling is slated to expand across European and North American pilot lines.</p>"
        )
        extracted = ExtractedArticle(
            title=item.title,
            description=item.description,
            url=item.url,
            source_name=item.source_name,
            source_type=item.source_type,
            author=item.author,
            published_at=item.published_at,
            category=item.category,
            collected_at=item.collected_at,
            extraction_status="EXTRACTED",
            extraction_method="article_web_extraction",
            content=raw_body,
        )

        # -----------------------------------------------------------------
        # STEP 3: Content Cleaning
        # -----------------------------------------------------------------
        cleaning_service = ContentCleaningService()
        cleaned: CleanedArticle = cleaning_service.clean_article(extracted)
        assert cleaned.cleaning_status.value == "SUCCESS"
        assert "<p>" not in (cleaned.cleaned_content or "")

        # -----------------------------------------------------------------
        # STEP 4: Deduplication (Run 1: First arrival -> UNIQUE)
        # -----------------------------------------------------------------
        dedup_service = DuplicateDetectionService(
            config=DuplicateDetectionConfig(
                enable_historical_detection=True,
                persist_unique_articles=True,
            )
        )
        first_run_result = dedup_service.check_article(cleaned, session=db_session)
        db_session.commit()

        assert first_run_result.status == "unique"
        assert first_run_result.decision.status == DuplicateStatus.UNIQUE
        assert first_run_result.decision.is_duplicate is False

        # -----------------------------------------------------------------
        # STEP 4: Deduplication (Run 2: Same article re-ingested -> DUPLICATE)
        # -----------------------------------------------------------------
        second_run_result = dedup_service.check_article(cleaned, session=db_session)
        assert second_run_result.status == "duplicate"
        assert second_run_result.decision.status == DuplicateStatus.DUPLICATE
        assert second_run_result.decision.is_duplicate is True
        assert second_run_result.decision.duplicate_reason == DuplicateReason.URL_MATCH
