"""Batch deduplication test suite verifying in-batch detection without DB dependencies."""
import pytest

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


class TestBatchDeduplication:
    """Test suite verifying Section 17 & Section 32 current-batch deduplication requirements."""

    def test_canonical_batch_scenario_a_equals_b_c_equals_d(
        self,
        sample_cleaned_article: CleanedArticle,
        sample_different_article: CleanedArticle,
    ):
        """Mandatory Section 32 Scenario:
        
        Input: [Article A, Article B, Article C, Article D]
        Where:
          A == B (exact content match)
          C == D (exact content match)
          
        Expected output:
          A -> UNIQUE
          B -> DUPLICATE
          C -> UNIQUE
          D -> DUPLICATE
        """
        article_a = sample_cleaned_article.model_copy(
            update={"url": "https://source-a.com/story-1", "canonical_url": "https://source-a.com/story-1"}
        )
        article_b = sample_cleaned_article.model_copy(
            update={"url": "https://source-b.com/story-1-syndicated", "canonical_url": "https://source-b.com/story-1-syndicated"}
        )
        article_c = sample_different_article.model_copy(
            update={"url": "https://source-c.com/story-2", "canonical_url": "https://source-c.com/story-2"}
        )
        article_d = sample_different_article.model_copy(
            update={"url": "https://source-d.com/story-2-copy", "canonical_url": "https://source-d.com/story-2-copy"}
        )

        batch = [article_a, article_b, article_c, article_d]

        # Service configured with no database persistence to strictly isolate batch detection
        service = DuplicateDetectionService(
            config=DuplicateDetectionConfig(
                similarity_threshold=0.82,
                enable_historical_detection=False,
                persist_unique_articles=False,
                persist_duplicate_records=False,
            )
        )

        results = service.check_batch(batch)

        assert len(results) == 4

        # A must be UNIQUE
        assert results[0].decision.status == DuplicateStatus.UNIQUE
        assert results[0].decision.is_duplicate is False

        # B must be DUPLICATE (matched A in batch)
        assert results[1].decision.status == DuplicateStatus.DUPLICATE
        assert results[1].decision.is_duplicate is True
        assert results[1].decision.duplicate_reason == DuplicateReason.EXACT_CONTENT
        assert results[1].decision.detection_scope == DetectionScope.BATCH

        # C must be UNIQUE
        assert results[2].decision.status == DuplicateStatus.UNIQUE
        assert results[2].decision.is_duplicate is False

        # D must be DUPLICATE (matched C in batch)
        assert results[3].decision.status == DuplicateStatus.DUPLICATE
        assert results[3].decision.is_duplicate is True
        assert results[3].decision.duplicate_reason == DuplicateReason.EXACT_CONTENT
        assert results[3].decision.detection_scope == DetectionScope.BATCH

    def test_batch_url_duplicate_detection(
        self,
        sample_cleaned_article: CleanedArticle,
    ):
        """Two articles in the same batch with identical normalized URLs."""
        article_1 = sample_cleaned_article.model_copy(
            update={"url": "https://example.com/breaking-ai"}
        )
        article_2 = sample_cleaned_article.model_copy(
            update={"url": "https://www.example.com/breaking-ai?utm_source=rss&utm_medium=feed"}
        )

        service = DuplicateDetectionService(
            config=DuplicateDetectionConfig(
                enable_historical_detection=False,
                persist_unique_articles=False,
                persist_duplicate_records=False,
            )
        )

        results = service.check_batch([article_1, article_2])

        assert results[0].decision.status == DuplicateStatus.UNIQUE
        assert results[1].decision.status == DuplicateStatus.DUPLICATE
        assert results[1].decision.duplicate_reason == DuplicateReason.URL_MATCH
        assert results[1].decision.detection_scope == DetectionScope.BATCH

    def test_batch_similarity_duplicate_detection(
        self,
        sample_cleaned_article: CleanedArticle,
        sample_similar_article: CleanedArticle,
    ):
        """Two articles in the same batch covering the same story with paraphrased wording."""
        service = DuplicateDetectionService(
            config=DuplicateDetectionConfig(
                similarity_threshold=0.70,
                enable_historical_detection=False,
                persist_unique_articles=False,
                persist_duplicate_records=False,
            )
        )

        results = service.check_batch([sample_cleaned_article, sample_similar_article])

        assert results[0].decision.status == DuplicateStatus.UNIQUE
        assert results[1].decision.status == DuplicateStatus.DUPLICATE
        assert results[1].decision.duplicate_reason == DuplicateReason.SIMILARITY
        assert results[1].decision.detection_scope == DetectionScope.BATCH
        assert results[1].decision.similarity_score is not None
        assert results[1].decision.similarity_score >= 0.70

    def test_batch_with_all_unique_articles(
        self,
        sample_cleaned_article: CleanedArticle,
        sample_different_article: CleanedArticle,
        sample_related_different_article: CleanedArticle,
    ):
        service = DuplicateDetectionService(
            config=DuplicateDetectionConfig(
                enable_historical_detection=False,
                persist_unique_articles=False,
                persist_duplicate_records=False,
            )
        )

        results = service.check_batch([
            sample_cleaned_article,
            sample_different_article,
            sample_related_different_article,
        ])

        assert all(r.decision.status == DuplicateStatus.UNIQUE for r in results)
        assert all(r.decision.is_duplicate is False for r in results)

    def test_empty_batch_returns_empty_list(self):
        service = DuplicateDetectionService()
        assert service.check_batch([]) == []
