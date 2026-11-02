"""Integration tests for FastAPI endpoints using TestClient."""
import httpx
import pytest
from fastapi.testclient import TestClient

from backend.common.exceptions.custom_exceptions import (
    ConfigurationError,
    ProviderAuthenticationError,
    ProviderRateLimitError,
    ProviderTimeoutError,
)
from backend.main import app
from backend.step1_source_collection.apis.routes import get_service
from backend.step1_source_collection.models.news_item import NewsItem
from backend.step1_source_collection.models.response_models import CollectionResponse
from backend.step1_source_collection.services.source_collection_service import (
    SourceCollectionService,
)


@pytest.fixture
def client():
    """Return FastAPI TestClient."""
    return TestClient(app)


def test_health_check_endpoint(client):
    """Verify GET /health returns status: ok."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_gnews_endpoint_success(client):
    """Verify GET /api/v1/source-collection/gnews returns 200 and formatted response."""
    class MockService:
        async def collect_from_gnews(self, category: str, limit: int = 10):
            item = NewsItem(
                title="Mock GNews Headline",
                url="https://example.com/gnews-article",
                source_name="Tech Verge",
                source_type="gnews",
                category=category,
            )
            return CollectionResponse(
                provider="gnews",
                category=category,
                count=1,
                items=[item],
            )

    app.dependency_overrides[get_service] = lambda: MockService()
    try:
        response = client.get("/api/v1/source-collection/gnews?category=Technology&limit=5")
        assert response.status_code == 200
        data = response.json()
        assert data["provider"] == "gnews"
        assert data["category"] == "Tech"
        assert data["count"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["title"] == "Mock GNews Headline"
    finally:
        app.dependency_overrides.clear()


def test_newsdata_endpoint_success(client):
    """Verify GET /api/v1/source-collection/newsdata returns 200 and formatted response."""
    class MockService:
        async def collect_from_newsdata(self, category: str, limit: int = 10):
            item = NewsItem(
                title="Mock NewsData Headline",
                url="https://example.com/newsdata-article",
                source_name="Science Direct",
                source_type="newsdata",
                category=category,
                author="John Doe",
            )
            return CollectionResponse(
                provider="newsdata",
                category=category,
                count=1,
                items=[item],
            )

    app.dependency_overrides[get_service] = lambda: MockService()
    try:
        response = client.get("/api/v1/source-collection/newsdata?category=Science")
        assert response.status_code == 200
        data = response.json()
        assert data["provider"] == "newsdata"
        assert data["category"] == "Developments"
        assert data["count"] == 1
        assert data["items"][0]["author"] == "John Doe"
    finally:
        app.dependency_overrides.clear()


def test_invalid_category_returns_400(client):
    """Verify that an invalid category query parameter returns HTTP 400."""
    response = client.get("/api/v1/source-collection/gnews?category=UnsupportedCategory")
    assert response.status_code == 400
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "INVALID_CATEGORY"
    assert "not supported" in data["error"]["message"]


def test_missing_category_returns_422(client):
    """Verify that omitting the required category parameter returns HTTP 422."""
    response = client.get("/api/v1/source-collection/gnews")
    assert response.status_code == 422
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "VALIDATION_ERROR"


def test_provider_rate_limit_maps_to_429(client):
    """Verify that ProviderRateLimitError is handled and returns HTTP 429."""
    class MockService:
        async def collect_from_gnews(self, category: str, limit: int = 10):
            raise ProviderRateLimitError(provider="gnews", retry_after=120)

    app.dependency_overrides[get_service] = lambda: MockService()
    try:
        response = client.get("/api/v1/source-collection/gnews?category=Technology")
        assert response.status_code == 429
        assert response.headers.get("retry-after") == "120"
        data = response.json()
        assert data["error"]["code"] == "RATE_LIMIT_EXCEEDED"
    finally:
        app.dependency_overrides.clear()


def test_provider_auth_error_maps_to_502(client):
    """Verify that ProviderAuthenticationError returns HTTP 502 with safe message."""
    class MockService:
        async def collect_from_newsdata(self, category: str, limit: int = 10):
            raise ProviderAuthenticationError(provider="newsdata")

    app.dependency_overrides[get_service] = lambda: MockService()
    try:
        response = client.get("/api/v1/source-collection/newsdata?category=Technology")
        assert response.status_code == 502
        data = response.json()
        assert data["error"]["code"] == "PROVIDER_AUTH_ERROR"
    finally:
        app.dependency_overrides.clear()


def test_provider_timeout_maps_to_504(client):
    """Verify that ProviderTimeoutError returns HTTP 504."""
    class MockService:
        async def collect_from_gnews(self, category: str, limit: int = 10):
            raise ProviderTimeoutError(provider="gnews")

    app.dependency_overrides[get_service] = lambda: MockService()
    try:
        response = client.get("/api/v1/source-collection/gnews?category=Business")
        assert response.status_code == 504
        data = response.json()
        assert data["error"]["code"] == "PROVIDER_TIMEOUT"
    finally:
        app.dependency_overrides.clear()


def test_configuration_error_maps_to_500(client):
    """Verify that ConfigurationError returns HTTP 500 without leaking secrets."""
    class MockService:
        async def collect_from_gnews(self, category: str, limit: int = 10):
            raise ConfigurationError("GNews API key is not configured.")

    app.dependency_overrides[get_service] = lambda: MockService()
    try:
        response = client.get("/api/v1/source-collection/gnews?category=Science")
        assert response.status_code == 500
        data = response.json()
        assert data["error"]["code"] == "CONFIGURATION_ERROR"
    finally:
        app.dependency_overrides.clear()


def test_rss_endpoint_success_with_category(client):
    """Verify GET /api/v1/source-collection/rss with category returns 200 and normalized items."""
    class MockService:
        async def collect_from_rss(self, category: str, limit: int = 10):
            item = NewsItem(
                title="Mock RSS Headline",
                url="https://example.com/rss-article",
                source_name="Tech Dispatch",
                source_type="rss",
                category=category,
                author="Jane Reporter",
            )
            return CollectionResponse(
                provider="rss",
                category=category,
                count=1,
                items=[item],
            )

    app.dependency_overrides[get_service] = lambda: MockService()
    try:
        response = client.get("/api/v1/source-collection/rss?category=Technology&limit=5")
        assert response.status_code == 200
        data = response.json()
        assert data["provider"] == "rss"
        assert data["category"] == "Tech"
        assert data["count"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["title"] == "Mock RSS Headline"
        assert data["items"][0]["source_type"] == "rss"
    finally:
        app.dependency_overrides.clear()


def test_rss_endpoint_invalid_category_returns_400(client):
    """Verify GET /api/v1/source-collection/rss with invalid category returns HTTP 400."""
    response = client.get("/api/v1/source-collection/rss?category=InvalidCat")
    assert response.status_code == 400
    data = response.json()
    assert data["error"]["code"] == "INVALID_CATEGORY"

