"""API endpoint test suite verifying HTTP contracts, status codes, error handling, and serialization."""
import pytest
from fastapi.testclient import TestClient


def test_api_health_endpoint(client: TestClient):
    """TEST 1: Health endpoint returns 200 OK with database connection status."""
    res = client.get("/api/v1/knowledge/health")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "healthy"
    assert body["database"] == "connected"
    assert body["database_name"] == "estd_knowledge"


def test_api_categories_list(client: TestClient):
    """TEST 10: Canonical categories endpoint returns exactly 5 categories."""
    res = client.get("/api/v1/knowledge/categories")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "success"
    assert body["total"] == 5
    names = {item["name"] for item in body["items"]}
    assert names == {
        "Entertainment",
        "Sports",
        "Tech",
        "Developments",
        "Business & Finance",
    }


def test_api_create_and_retrieve_article(client: TestClient, clean_knowledge_db, sample_ai_article_payload):
    """TEST 2 & 3: Create valid article (201) and retrieve by ID (200)."""
    # Create article
    create_res = client.post("/api/v1/knowledge/articles", json=sample_ai_article_payload)
    assert create_res.status_code == 201
    created_data = create_res.json()["data"]
    art_id = created_data["id"]
    assert art_id is not None
    assert created_data["title"] == sample_ai_article_payload["title"]
    assert created_data["category"] == "Tech"

    # Retrieve by ID
    get_res = client.get(f"/api/v1/knowledge/articles/{art_id}")
    assert get_res.status_code == 200
    fetched_data = get_res.json()["data"]
    assert fetched_data["id"] == art_id
    assert fetched_data["title"] == sample_ai_article_payload["title"]


def test_api_list_articles(client: TestClient, clean_knowledge_db, sample_ai_article_payload):
    """TEST 4: List articles endpoint returns 200 with list payload and pagination."""
    client.post("/api/v1/knowledge/articles", json=sample_ai_article_payload)

    res = client.get("/api/v1/knowledge/articles")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "success"
    assert "items" in body["data"]
    assert "pagination" in body["data"]
    assert body["data"]["pagination"]["total_items"] >= 1


def test_api_filter_by_category_developments(client: TestClient, clean_knowledge_db):
    """TEST 5: Filtering by category=Developments returns Developments articles."""
    # Seed one Tech and one Developments article
    client.post("/api/v1/knowledge/articles", json={
        "title": "Test AI Story",
        "content": "AI story content...",
        "url": "https://example.com/test-ai-story",
        "category": "Tech",
    })
    client.post("/api/v1/knowledge/articles", json={
        "title": "Test Developments Story",
        "content": "Science story content...",
        "url": "https://example.com/test-science-story",
        "category": "Developments",
    })

    res = client.get("/api/v1/knowledge/articles?category=Developments&page_size=50")
    assert res.status_code == 200
    items = res.json()["data"]["items"]
    assert len(items) >= 1
    assert any(it["title"] == "Test Developments Story" for it in items)
    assert all(it["category"] == "Developments" for it in items)


def test_api_filter_by_category_technology(client: TestClient, clean_knowledge_db):
    """TEST 6: Filtering by category=Tech returns Tech articles."""
    client.post("/api/v1/knowledge/articles", json={
        "title": "Test Tech Story",
        "content": "Tech story content...",
        "url": "https://example.com/test-tech-story",
        "category": "Tech",
    })

    res = client.get("/api/v1/knowledge/articles?category=Tech&page_size=50")
    assert res.status_code == 200
    items = res.json()["data"]["items"]
    assert len(items) >= 1
    assert any(it["title"] == "Test Tech Story" for it in items)
    assert all(it["category"] == "Tech" for it in items)


def test_api_invalid_category_returns_400(client: TestClient):
    """TEST 7: Unsupported category like 'NonExistentCategory' returns 400 Bad Request."""
    res = client.get("/api/v1/knowledge/articles?category=NonExistentCategory")
    assert res.status_code == 400
    err = res.json()["error"]
    assert err["code"] == "INVALID_CATEGORY"
    assert "NonExistentCategory" in err["message"]


def test_api_duplicate_article_returns_409(client: TestClient, clean_knowledge_db, sample_ai_article_payload):
    """TEST 8: Submitting duplicate article returns 409 Conflict."""
    res1 = client.post("/api/v1/knowledge/articles", json=sample_ai_article_payload)
    assert res1.status_code == 201

    # Second submission with same URL and content
    res2 = client.post("/api/v1/knowledge/articles", json=sample_ai_article_payload)
    assert res2.status_code == 409
    err = res2.json()["error"]
    assert err["code"] == "DUPLICATE_ARTICLE"


def test_api_pagination(client: TestClient, clean_knowledge_db):
    """TEST 9: Pagination query parameters return correct page size and metadata."""
    for i in range(5):
        client.post("/api/v1/knowledge/articles", json={
            "title": f"Test Pagination Story {i}",
            "content": f"Content for story {i}...",
            "url": f"https://example.com/test-pagination-{i}",
            "category": "Business & Finance",
        })

    res = client.get("/api/v1/knowledge/articles?page=1&page_size=2")
    assert res.status_code == 200
    meta = res.json()["data"]["pagination"]
    assert meta["page"] == 1
    assert meta["page_size"] == 2
    assert meta["total_items"] >= 5
    assert meta["total_pages"] >= 3
    assert meta["has_next"] is True
    assert meta["has_prev"] is False


def test_api_article_not_found(client: TestClient):
    """TEST 12: Requesting non-existent article returns 404."""
    res = client.get("/api/v1/knowledge/articles/99999999")
    assert res.status_code == 404
    err = res.json()["error"]
    assert err["code"] == "ARTICLE_NOT_FOUND"


def test_api_delete_article(client: TestClient, clean_knowledge_db, sample_ai_article_payload):
    """TEST 11: DELETE /api/v1/knowledge/articles/{id} deletes record."""
    create_res = client.post("/api/v1/knowledge/articles", json=sample_ai_article_payload)
    art_id = create_res.json()["data"]["id"]

    del_res = client.delete(f"/api/v1/knowledge/articles/{art_id}")
    assert del_res.status_code == 200
    assert del_res.json()["status"] == "success"

    # Confirm subsequent GET returns 404
    get_res = client.get(f"/api/v1/knowledge/articles/{art_id}")
    assert get_res.status_code == 404
