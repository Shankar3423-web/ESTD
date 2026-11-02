"""Historical deduplication test suite verifying database persistence and cross-session matching."""
import pytest
from sqlalchemy.orm import Session

from backend.step3_content_cleaning.models.cleaned_article import CleanedArticle
from backend.step4_duplicate_detection.config import DuplicateDetectionConfig
from backend.step4_duplicate_detection.models.duplicate_record import (
    DetectionScope,
    DuplicateReason,
    DuplicateStatus,
)
from backend.step4_duplicate_detection.services.duplicate_detection_service import (
    DuplicateDetectionService,
)


@pytest.mark.usefixtures("clean_db")
class TestHistoricalDeduplication:
    """Test suite verifying Section 18 & Section 31 historical deduplication requirements against PostgreSQL."""

    def test_mandatory_historical_scenario_run1_and_run2(
        self,
        db_session: Session,
        sample_cleaned_article: CleanedArticle,
    ):
        """Mandatory Section 31 Scenario:
        
        Run 1 (Day 1):
          Article A -> Step 4 -> UNIQUE -> stored in historical index
          
        Run 2 (Day 2):
          Submit Article A again using a NEW service instance (clean in-memory state)
          Expected -> DUPLICATE (HISTORICAL URL_MATCH)
        """
        config = DuplicateDetectionConfig(
            similarity_threshold=0.82,
            enable_historical_detection=True,
            persist_unique_articles=True,
            persist_duplicate_records=True,
        )

        # -------------------------------------------------------------
        # RUN 1: Article A arrives for the first time
        # -------------------------------------------------------------
        service_day_1 = DuplicateDetectionService(config=config)
        result_day_1 = service_day_1.check_article(sample_cleaned_article, session=db_session)
        db_session.commit()

        assert result_day_1.status == "unique"
        assert result_day_1.decision.status == DuplicateStatus.UNIQUE
        assert result_day_1.decision.is_duplicate is False

        # -------------------------------------------------------------
        # RUN 2: Article A arrives again tomorrow on a FRESH service instance
        # -------------------------------------------------------------
        service_day_2 = DuplicateDetectionService(config=config)
        # Ensure in-memory cache is empty
        assert len(service_day_2.index.batch_url_cache) == 0

        result_day_2 = service_day_2.check_article(sample_cleaned_article, session=db_session)

        assert result_day_2.status == "duplicate"
        assert result_day_2.decision.status == DuplicateStatus.DUPLICATE
        assert result_day_2.decision.is_duplicate is True
        assert result_day_2.decision.duplicate_reason == DuplicateReason.URL_MATCH
        assert result_day_2.decision.detection_scope == DetectionScope.HISTORICAL
        assert result_day_2.decision.matched_article_id is not None

    def test_historical_exact_content_match_different_url(
        self,
        db_session: Session,
        sample_cleaned_article: CleanedArticle,
        sample_exact_duplicate_article: CleanedArticle,
    ):
        """Article with different URL but identical body matches historically via SHA-256."""
        config = DuplicateDetectionConfig(
            enable_historical_detection=True,
            persist_unique_articles=True,
            persist_duplicate_records=False,
        )

        # Index original article
        service_1 = DuplicateDetectionService(config=config)
        res1 = service_1.check_article(sample_cleaned_article, session=db_session)
        db_session.commit()
        assert res1.status == "unique"

        # Submit article with different publisher URL on a new service instance
        service_2 = DuplicateDetectionService(config=config)
        res2 = service_2.check_article(sample_exact_duplicate_article, session=db_session)

        assert res2.status == "duplicate"
        assert res2.decision.status == DuplicateStatus.DUPLICATE
        assert res2.decision.is_duplicate is True
        assert res2.decision.duplicate_reason == DuplicateReason.EXACT_CONTENT
        assert res2.decision.detection_scope == DetectionScope.HISTORICAL

    def test_historical_similarity_match_different_wording_different_url(
        self,
        db_session: Session,
        sample_cleaned_article: CleanedArticle,
        sample_similar_article: CleanedArticle,
    ):
        """Mandatory Section 31 Scenario:
        
        Same story, different URL, paraphrased wording -> matches historically via SIMILARITY.
        """
        config = DuplicateDetectionConfig(
            similarity_threshold=0.70,
            enable_historical_detection=True,
            persist_unique_articles=True,
            persist_duplicate_records=False,
        )

        service_1 = DuplicateDetectionService(config=config)
        res1 = service_1.check_article(sample_cleaned_article, session=db_session)
        db_session.commit()
        assert res1.status == "unique"

        # Submit similar article on new service instance
        service_2 = DuplicateDetectionService(config=config)
        res2 = service_2.check_article(sample_similar_article, session=db_session)

        assert res2.status == "duplicate"
        assert res2.decision.status == DuplicateStatus.DUPLICATE
        assert res2.decision.is_duplicate is True
        assert res2.decision.duplicate_reason == DuplicateReason.SIMILARITY
        assert res2.decision.detection_scope == DetectionScope.HISTORICAL
        assert res2.decision.similarity_score is not None
        assert res2.decision.similarity_score >= 0.70

    def test_historical_different_article_remains_unique(
        self,
        db_session: Session,
        sample_cleaned_article: CleanedArticle,
        sample_different_article: CleanedArticle,
    ):
        """Completely different article is accepted as UNIQUE despite existing historical records."""
        config = DuplicateDetectionConfig(
            enable_historical_detection=True,
            persist_unique_articles=True,
        )

        service_1 = DuplicateDetectionService(config=config)
        service_1.check_article(sample_cleaned_article, session=db_session)
        db_session.commit()

        service_2 = DuplicateDetectionService(config=config)
        res = service_2.check_article(sample_different_article, session=db_session)

        assert res.status == "unique"
        assert res.decision.status == DuplicateStatus.UNIQUE
        assert res.decision.is_duplicate is False
