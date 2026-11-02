"""Integration test suite verifying Step 4 -> Step 5 pipeline flow and PostgreSQL persistence."""
import pytest
from fastapi.testclient import TestClient

from backend.common.constants.categories import VALID_CATEGORIES
from backend.step3_content_cleaning.models.cleaned_article import CleanedArticle
from backend.step3_content_cleaning.models.cleaning_enums import CleaningStatus
from backend.step4_duplicate_detection.detectors.exact_content_detector import ExactContentDetector
from backend.step4_duplicate_detection.models.duplicate_record import (
    DetectionScope,
    DuplicateDecision,
    DuplicateReason,
    DuplicateStatus,
)
from backend.step4_duplicate_detection.normalizers.url_normalizer import normalize_url
from backend.step4_duplicate_detection.schemas.duplicate_response import DuplicateCheckResult
from backend.step5_knowledge_source.exceptions import ArticleDuplicateError
from backend.step5_knowledge_source.services.knowledge_service import KnowledgeSourceService


class TestStep4ToStep5Integration:
    """Verifies that Step 4 output is properly consumed and persisted into PostgreSQL."""

    def test_step4_unique_article_to_step5_persistence(
        self,
        clean_knowledge_db,
        sample_step4_unique_result: DuplicateCheckResult,
    ):
        """End-to-end flow: Step 4 UNIQUE decision -> Step 5 Service -> PostgreSQL -> Retrieval."""
        service = KnowledgeSourceService()

        # Step 5 persistence
        persisted = service.persist_from_step4(sample_step4_unique_result)

        assert persisted.id is not None
        assert persisted.title == sample_step4_unique_result.article.title
        assert persisted.content == sample_step4_unique_result.article.content
        assert persisted.url == sample_step4_unique_result.article.url
        assert persisted.normalized_url == sample_step4_unique_result.decision.normalized_url
        assert persisted.content_hash == sample_step4_unique_result.decision.content_hash
        assert persisted.category == sample_step4_unique_result.article.category
        assert persisted.category_id is not None

        # Verify query from database
        fetched = service.get_article_by_id(persisted.id)
        assert fetched.id == persisted.id
        assert fetched.title == sample_step4_unique_result.article.title
        assert fetched.normalized_url == sample_step4_unique_result.decision.normalized_url

    def test_step4_duplicate_article_to_step5_rejected(
        self,
        clean_knowledge_db,
        sample_step4_duplicate_result: DuplicateCheckResult,
    ):
        """End-to-end flow: Step 4 DUPLICATE decision is blocked from entering Knowledge Source."""
        service = KnowledgeSourceService()

        with pytest.raises(ArticleDuplicateError) as exc_info:
            service.persist_from_step4(sample_step4_duplicate_result)

        assert exc_info.value.status_code == 409
        assert "duplicate" in exc_info.value.code.lower()

    def test_all_five_categories_step4_to_step5(
        self,
        clean_knowledge_db,
    ):
        """Verify pipeline contract works across all 5 canonical categories."""
        service = KnowledgeSourceService()

        for idx, cat in enumerate(VALID_CATEGORIES):
            content = f"Cleaned body text for {cat} domain topic explaining new findings and methodology in detail."
            url = f"https://example.com/test-step4-step5-pipeline-{idx}"
            cleaned_article = CleanedArticle(
                title=f"Test Article for {cat}",
                description=f"Summary for {cat}",
                content=content,
                cleaned_content=content,
                url=url,
                canonical_url=url,
                source_name=f"{cat} Digest",
                source_type="rss",
                author="Research Team",
                published_at="2026-10-01T15:00:00Z",
                category=cat,
                collected_at="2026-10-01T15:05:00Z",
                cleaning_status=CleaningStatus.SUCCESS,
                cleaned_content_length=len(content),
                original_content_length=len(content),
            )
            norm_url = normalize_url(url)
            c_hash = ExactContentDetector.compute_content_hash(content)
            decision = DuplicateDecision.unique(
                normalized_url=norm_url,
                content_hash=c_hash,
            )
            check_result = DuplicateCheckResult(
                status="unique",
                decision=decision,
                article=cleaned_article,
            )

            persisted = service.persist_from_step4(check_result)
            assert persisted.id is not None
            assert persisted.category == cat

    def test_api_step4_payload_persistence(
        self,
        client: TestClient,
        clean_knowledge_db,
        sample_step4_unique_result: DuplicateCheckResult,
    ):
        """Verify API POST /api/v1/knowledge/articles accepts raw Step 4 DuplicateCheckResult JSON."""
        payload = sample_step4_unique_result.model_dump(mode="json")
        res = client.post("/api/v1/knowledge/articles", json=payload)
        assert res.status_code == 201
        data = res.json()["data"]
        assert data["id"] is not None
        assert data["title"] == sample_step4_unique_result.article.title
        assert data["normalized_url"] == sample_step4_unique_result.decision.normalized_url

    def test_api_step4_duplicate_payload_returns_409(
        self,
        client: TestClient,
        clean_knowledge_db,
        sample_step4_duplicate_result: DuplicateCheckResult,
    ):
        """Verify API POST /api/v1/knowledge/articles rejects raw Step 4 duplicate result with 409."""
        payload = sample_step4_duplicate_result.model_dump(mode="json")
        res = client.post("/api/v1/knowledge/articles", json=payload)
        assert res.status_code == 409
        err = res.json()["error"]
        assert err["code"] == "DUPLICATE_ARTICLE"
