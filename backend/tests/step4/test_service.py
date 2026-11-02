"""Unit tests for Step 4 DuplicateDetectionService."""
import pytest
from unittest.mock import MagicMock, patch

from backend.step3_content_cleaning.models.cleaned_article import CleanedArticle
from backend.step4_duplicate_detection.config import DuplicateDetectionConfig
from backend.step4_duplicate_detection.exceptions import (
    InvalidArticleForDeduplicationError,
)
from backend.step4_duplicate_detection.models.duplicate_record import (
    DetectionScope,
    DuplicateReason,
    DuplicateStatus,
)
from backend.step4_duplicate_detection.services.duplicate_detection_service import (
    DuplicateDetectionService,
)


class TestDuplicateDetectionService:
    """Test suite verifying end-to-end service orchestration, priorities, and error handling."""

    def test_unique_article_evaluation(
        self,
        duplicate_service: DuplicateDetectionService,
        sample_cleaned_article: CleanedArticle,
    ):
        result = duplicate_service.check_article(sample_cleaned_article)
        assert result.status == "unique"
        assert result.decision.status == DuplicateStatus.UNIQUE
        assert result.decision.is_duplicate is False
        assert result.decision.duplicate_reason is None
        assert result.decision.matched_article_id is None
        assert result.article.title == sample_cleaned_article.title

    def test_duplicate_by_url_match_priority(
        self,
        duplicate_service: DuplicateDetectionService,
        sample_cleaned_article: CleanedArticle,
    ):
        # Register original in batch
        duplicate_service.check_article(sample_cleaned_article)

        # Same article with tracking parameter attached to URL
        url_with_tracking = sample_cleaned_article.url + "?utm_source=twitter&fbclid=123"
        article_with_tracking = sample_cleaned_article.model_copy(
            update={"url": url_with_tracking, "canonical_url": url_with_tracking}
        )

        result = duplicate_service.check_article(article_with_tracking)
        assert result.status == "duplicate"
        assert result.decision.status == DuplicateStatus.DUPLICATE
        assert result.decision.is_duplicate is True
        assert result.decision.duplicate_reason == DuplicateReason.URL_MATCH
        assert result.decision.detection_scope == DetectionScope.BATCH

    def test_duplicate_by_exact_content_hash(
        self,
        duplicate_service: DuplicateDetectionService,
        sample_cleaned_article: CleanedArticle,
        sample_exact_duplicate_article: CleanedArticle,
    ):
        # First article evaluated
        res1 = duplicate_service.check_article(sample_cleaned_article)
        assert res1.status == "unique"

        # Second article has completely different URL but identical normalized content
        res2 = duplicate_service.check_article(sample_exact_duplicate_article)
        assert res2.status == "duplicate"
        assert res2.decision.status == DuplicateStatus.DUPLICATE
        assert res2.decision.is_duplicate is True
        assert res2.decision.duplicate_reason == DuplicateReason.EXACT_CONTENT
        assert res2.decision.detection_scope == DetectionScope.BATCH

    def test_duplicate_by_similarity_above_threshold(
        self,
        sample_cleaned_article: CleanedArticle,
        sample_similar_article: CleanedArticle,
    ):
        # Configure service with threshold 0.70 to ensure similar article matches
        config = DuplicateDetectionConfig(
            similarity_threshold=0.70,
            persist_unique_articles=False,
            persist_duplicate_records=False,
        )
        service = DuplicateDetectionService(config=config)

        res1 = service.check_article(sample_cleaned_article)
        assert res1.status == "unique"

        res2 = service.check_article(sample_similar_article)
        assert res2.status == "duplicate"
        assert res2.decision.status == DuplicateStatus.DUPLICATE
        assert res2.decision.is_duplicate is True
        assert res2.decision.duplicate_reason == DuplicateReason.SIMILARITY
        assert res2.decision.detection_scope == DetectionScope.BATCH
        assert res2.decision.similarity_score is not None
        assert res2.decision.similarity_score >= 0.70

    def test_related_but_different_articles_are_unique(
        self,
        duplicate_service: DuplicateDetectionService,
        sample_cleaned_article: CleanedArticle,
        sample_related_different_article: CleanedArticle,
    ):
        """Related != Duplicate: different events in technology must remain UNIQUE."""
        res1 = duplicate_service.check_article(sample_cleaned_article)
        assert res1.status == "unique"

        res2 = duplicate_service.check_article(sample_related_different_article)
        assert res2.status == "unique"
        assert res2.decision.status == DuplicateStatus.UNIQUE
        assert res2.decision.is_duplicate is False

    def test_completely_different_article_is_unique(
        self,
        duplicate_service: DuplicateDetectionService,
        sample_cleaned_article: CleanedArticle,
        sample_different_article: CleanedArticle,
    ):
        res1 = duplicate_service.check_article(sample_cleaned_article)
        assert res1.status == "unique"

        res2 = duplicate_service.check_article(sample_different_article)
        assert res2.status == "unique"
        assert res2.decision.status == DuplicateStatus.UNIQUE

    def test_priority_url_check_short_circuits_expensive_similarity(
        self,
        sample_cleaned_article: CleanedArticle,
    ):
        """When URL matches, exact content and similarity calculations must NOT run."""
        mock_similarity = MagicMock()
        service = DuplicateDetectionService(
            similarity_detector=mock_similarity,
            config=DuplicateDetectionConfig(persist_unique_articles=False, persist_duplicate_records=False),
        )

        # First evaluation
        service.check_article(sample_cleaned_article)

        # Same URL evaluation
        duplicate_article = sample_cleaned_article.model_copy()
        result = service.check_article(duplicate_article)

        assert result.status == "duplicate"
        assert result.decision.duplicate_reason == DuplicateReason.URL_MATCH
        # find_highest_similarity must NOT have been called for the duplicate check
        mock_similarity.find_highest_similarity.assert_not_called()

    def test_priority_exact_content_short_circuits_similarity(
        self,
        sample_cleaned_article: CleanedArticle,
        sample_exact_duplicate_article: CleanedArticle,
    ):
        """When exact content hash matches, similarity calculations must NOT run."""
        mock_similarity = MagicMock()
        service = DuplicateDetectionService(
            similarity_detector=mock_similarity,
            config=DuplicateDetectionConfig(persist_unique_articles=False, persist_duplicate_records=False),
        )

        service.check_article(sample_cleaned_article)
        result = service.check_article(sample_exact_duplicate_article)

        assert result.status == "duplicate"
        assert result.decision.duplicate_reason == DuplicateReason.EXACT_CONTENT
        mock_similarity.find_highest_similarity.assert_not_called()

    def test_missing_or_none_article_raises_exception(
        self,
        duplicate_service: DuplicateDetectionService,
    ):
        with pytest.raises(InvalidArticleForDeduplicationError):
            duplicate_service.check_article(None)  # type: ignore

    def test_empty_content_graceful_handling(
        self,
        duplicate_service: DuplicateDetectionService,
        sample_cleaned_article: CleanedArticle,
    ):
        empty_article = sample_cleaned_article.model_copy(
            update={
                "url": "https://example.com/empty-story",
                "canonical_url": "https://example.com/empty-story",
                "cleaned_content": "",
                "content": "",
                "description": "",
            }
        )
        result = duplicate_service.check_article(empty_article)
        assert result.status == "unique"
        assert result.decision.content_hash == ""
