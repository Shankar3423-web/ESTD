"""API endpoint tests for Step 4 Duplicate Detection routes."""
import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.step3_content_cleaning.models.cleaned_article import CleanedArticle


@pytest.fixture
def client():
    """FastAPI TestClient fixture."""
    return TestClient(app)


@pytest.mark.usefixtures("clean_db")
class TestDuplicateDetectionAPI:
    """Test suite for Step 4 FastAPI routes."""

    def test_check_single_unique_article(
        self,
        client: TestClient,
        sample_cleaned_article: CleanedArticle,
    ):
        payload = {"article": sample_cleaned_article.model_dump()}
        response = client.post("/api/v1/duplicate-detection/check", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["status"] == "unique"
        assert data["data"]["decision"]["status"] == "UNIQUE"
        assert data["data"]["decision"]["is_duplicate"] is False
        assert data["data"]["decision"]["duplicate_reason"] is None

    def test_check_duplicate_article_url_match(
        self,
        client: TestClient,
        sample_cleaned_article: CleanedArticle,
    ):
        # 1. First request creates index record
        client.post("/api/v1/duplicate-detection/check", json={"article": sample_cleaned_article.model_dump()})

        # 2. Second request with tracking query parameter
        url_with_tracking = sample_cleaned_article.url + "?utm_source=twitter&utm_medium=social"
        dup_article = sample_cleaned_article.model_copy(update={"url": url_with_tracking})

        response = client.post("/api/v1/duplicate-detection/check", json={"article": dup_article.model_dump()})
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["status"] == "duplicate"
        assert data["data"]["decision"]["status"] == "DUPLICATE"
        assert data["data"]["decision"]["is_duplicate"] is True
        assert data["data"]["decision"]["duplicate_reason"] == "URL_MATCH"

    def test_check_duplicate_exact_content(
        self,
        client: TestClient,
        sample_cleaned_article: CleanedArticle,
        sample_exact_duplicate_article: CleanedArticle,
    ):
        client.post("/api/v1/duplicate-detection/check", json={"article": sample_cleaned_article.model_dump()})

        response = client.post(
            "/api/v1/duplicate-detection/check",
            json={"article": sample_exact_duplicate_article.model_dump()},
        )
        assert response.status_code == 200

        data = response.json()
        assert data["data"]["status"] == "duplicate"
        assert data["data"]["decision"]["duplicate_reason"] == "EXACT_CONTENT"

    def test_check_duplicate_similarity(
        self,
        client: TestClient,
        sample_cleaned_article: CleanedArticle,
        sample_similar_article: CleanedArticle,
    ):
        client.post("/api/v1/duplicate-detection/check", json={"article": sample_cleaned_article.model_dump()})

        response = client.post(
            "/api/v1/duplicate-detection/check",
            json={"article": sample_similar_article.model_dump()},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["status"] == "duplicate"
        assert data["data"]["decision"]["duplicate_reason"] == "SIMILARITY"
        assert data["data"]["decision"]["similarity_score"] is not None

    def test_check_batch_endpoint_success(
        self,
        client: TestClient,
        sample_cleaned_article: CleanedArticle,
        sample_different_article: CleanedArticle,
    ):
        article_a = sample_cleaned_article.model_copy(update={"url": "https://a.com/1"})
        article_b = sample_cleaned_article.model_copy(update={"url": "https://b.com/1"})
        article_c = sample_different_article.model_copy(update={"url": "https://c.com/2"})
        article_d = sample_different_article.model_copy(update={"url": "https://d.com/2"})

        batch_payload = {
            "articles": [
                article_a.model_dump(),
                article_b.model_dump(),
                article_c.model_dump(),
                article_d.model_dump(),
            ]
        }

        response = client.post("/api/v1/duplicate-detection/check-batch", json=batch_payload)
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "success"
        assert data["total_count"] == 4
        assert data["unique_count"] == 2
        assert data["duplicate_count"] == 2
        assert len(data["items"]) == 4

        # A is unique, B is duplicate
        assert data["items"][0]["decision"]["status"] == "UNIQUE"
        assert data["items"][1]["decision"]["status"] == "DUPLICATE"

        # C is unique, D is duplicate
        assert data["items"][2]["decision"]["status"] == "UNIQUE"
        assert data["items"][3]["decision"]["status"] == "DUPLICATE"

    def test_stats_endpoint(self, client: TestClient, sample_cleaned_article: CleanedArticle):
        # Index one unique article
        client.post("/api/v1/duplicate-detection/check", json={"article": sample_cleaned_article.model_dump()})

        response = client.get("/api/v1/duplicate-detection/stats")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["unique_articles"] >= 1
        assert data["total_indexed"] >= 1

    def test_invalid_request_missing_required_fields_returns_422(self, client: TestClient):
        response = client.post("/api/v1/duplicate-detection/check", json={"article": {"title": "Incomplete Article"}})
        assert response.status_code == 422
        data = response.json()
        assert data["error"]["code"] == "VALIDATION_ERROR"
