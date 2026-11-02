"""API endpoint tests for Step 3 Content Cleaning & Normalization."""
import pytest
from fastapi.testclient import TestClient

from backend.step3_content_cleaning.models import CleaningStatus


def test_endpoint_clean_valid_article(test_client, sample_extracted_article_clean):
    payload = sample_extracted_article_clean.model_dump()
    response = test_client.post("/api/v1/content-cleaning/clean", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    article = data["data"]
    assert article["cleaning_status"] == CleaningStatus.SUCCESS
    assert article["category"] == "Developments"
    assert "MIT" in article["title"]
    assert len(article["cleaned_content"]) > 50
    assert article["original_content"] == sample_extracted_article_clean.content


def test_endpoint_clean_wrapped_payload(test_client, sample_extracted_article_clean):
    payload = {"article": sample_extracted_article_clean.model_dump()}
    response = test_client.post("/api/v1/content-cleaning/clean", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["data"]["cleaning_status"] == CleaningStatus.SUCCESS


def test_endpoint_clean_html_article(test_client, sample_extracted_article_with_html):
    payload = sample_extracted_article_with_html.model_dump()
    response = test_client.post("/api/v1/content-cleaning/clean", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    cleaned = data["data"]["cleaned_content"]
    assert "<p>" not in cleaned
    assert "Advertisement" not in cleaned
    assert "Google DeepMind" in cleaned


def test_endpoint_clean_boilerplate_article(test_client, sample_extracted_article_with_boilerplate):
    payload = sample_extracted_article_with_boilerplate.model_dump()
    response = test_client.post("/api/v1/content-cleaning/clean", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    cleaned = data["data"]["cleaned_content"]
    assert "We use cookies" not in cleaned
    assert "ADVERTISEMENT" not in cleaned
    assert "Sign up for our daily newsletter" not in cleaned
    assert "European central bankers" in cleaned


def test_endpoint_clean_empty_content_returns_controlled_failure(test_client):
    payload = {
        "title": "Article With Empty Content",
        "url": "https://example.com/no-content",
        "source_type": "rss",
        "category": "Technology",
        "collected_at": "2026-09-30T10:00:00Z",
        "extraction_status": "EXTRACTED",
        "content": None,
    }
    response = test_client.post("/api/v1/content-cleaning/clean", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "failed"
    article = data["data"]
    assert article["cleaning_status"] == CleaningStatus.CLEANING_FAILED
    assert article["cleaned_content"] is None
    assert "empty or contains no readable text" in article["error_message"]


def test_endpoint_clean_invalid_category_returns_422(test_client):
    payload = {
        "title": "Invalid Category Article",
        "url": "https://example.com/test",
        "source_type": "rss",
        "category": "UnsupportedCategory",
        "collected_at": "2026-09-30T10:00:00Z",
        "content": "Valid body content here for testing.",
    }
    response = test_client.post("/api/v1/content-cleaning/clean", json=payload)
    assert response.status_code == 422


def test_endpoint_clean_missing_required_fields_returns_422(test_client):
    payload = {
        "content": "Only content without title or url",
    }
    response = test_client.post("/api/v1/content-cleaning/clean", json=payload)
    assert response.status_code == 422


def test_endpoint_clean_batch_success(
    test_client, sample_extracted_article_clean, sample_extracted_article_with_html
):
    payload = [
        sample_extracted_article_clean.model_dump(),
        sample_extracted_article_with_html.model_dump(),
    ]
    response = test_client.post("/api/v1/content-cleaning/clean-batch", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["count"] == 2
    assert len(data["items"]) == 2
    assert data["items"][0]["cleaning_status"] == CleaningStatus.SUCCESS
    assert data["items"][1]["cleaning_status"] == CleaningStatus.SUCCESS
