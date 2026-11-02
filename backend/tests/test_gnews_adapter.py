"""Unit tests for GNewsAdapter with mocked HTTP responses."""
import json
import httpx
import pytest

from backend.common.constants.categories import ESTDCategory
from backend.common.exceptions.custom_exceptions import (
    ConfigurationError,
    InvalidCategoryError,
    ProviderAuthenticationError,
    ProviderConnectionError,
    ProviderRateLimitError,
    ProviderResponseError,
    ProviderServerError,
    ProviderTimeoutError,
)
from backend.step1_source_collection.apis.gnews_adapter import GNewsAdapter


@pytest.mark.asyncio
async def test_gnews_successful_fetch_technology(mock_settings, sample_gnews_response):
    """Verify successful GNews fetch and normalization for Technology category."""
    async def handler(request: httpx.Request) -> httpx.Response:
        assert "gnews.io/api/v4/top-headlines" in str(request.url)
        assert "category=technology" in str(request.url)
        assert "apikey=test_gnews_key_12345" in str(request.url)
        return httpx.Response(200, json=sample_gnews_response)

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    adapter = GNewsAdapter(settings=mock_settings, max_retries=0)

    items = await adapter.fetch_news(category="Technology", limit=5, client=client)

    assert len(items) == 2
    assert items[0].title == "Quantum Leap in Supercomputing"
    assert items[0].source_name == "Tech Times"
    assert items[0].source_type == "gnews"
    assert items[0].category == "Tech"
    assert items[0].author is None
    assert items[0].published_at == "2026-09-30T08:30:00Z"
    assert items[0].image_url == "https://example.com/images/quantum.jpg"
    assert items[0].url == "https://example.com/quantum-leap"


@pytest.mark.asyncio
async def test_gnews_search_endpoint_for_developments(mock_settings, sample_gnews_response):
    """Verify that Developments category routes to /search with q parameter."""
    captured_urls = []

    async def handler(request: httpx.Request) -> httpx.Response:
        captured_urls.append(str(request.url))
        return httpx.Response(200, json=sample_gnews_response)

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    adapter = GNewsAdapter(settings=mock_settings, max_retries=0)

    items = await adapter.fetch_news(category=ESTDCategory.DEVELOPMENTS.value, limit=5, client=client)

    assert len(captured_urls) == 1
    assert "gnews.io/api/v4/search" in captured_urls[0]
    assert "q=" in captured_urls[0]
    assert all(item.category == "Developments" for item in items)


@pytest.mark.asyncio
async def test_gnews_empty_articles_response(mock_settings):
    """Verify handling when provider returns 0 articles."""
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"totalArticles": 0, "articles": []})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    adapter = GNewsAdapter(settings=mock_settings, max_retries=0)

    items = await adapter.fetch_news(category="Business", limit=10, client=client)
    assert items == []


@pytest.mark.asyncio
async def test_gnews_malformed_missing_articles_field(mock_settings):
    """Verify ProviderResponseError is raised when 'articles' key is missing."""
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"some_other_key": 123})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    adapter = GNewsAdapter(settings=mock_settings, max_retries=0)

    with pytest.raises(ProviderResponseError) as exc_info:
        await adapter.fetch_news(category="Science", limit=10, client=client)
    assert "missing 'articles' field" in str(exc_info.value)


@pytest.mark.asyncio
async def test_gnews_malformed_invalid_json(mock_settings):
    """Verify ProviderResponseError is raised when response is not valid JSON."""
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="<html>502 Bad Gateway Nginx</html>")

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    adapter = GNewsAdapter(settings=mock_settings, max_retries=0)

    with pytest.raises(ProviderResponseError) as exc_info:
        await adapter.fetch_news(category="Technology", limit=10, client=client)
    assert "invalid JSON" in str(exc_info.value)


@pytest.mark.asyncio
async def test_gnews_auth_error_401(mock_settings):
    """Verify ProviderAuthenticationError is raised on 401 Unauthorized."""
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"errors": ["Invalid API key"]})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    adapter = GNewsAdapter(settings=mock_settings, max_retries=0)

    with pytest.raises(ProviderAuthenticationError) as exc_info:
        await adapter.fetch_news(category="Technology", limit=10, client=client)
    assert exc_info.value.status_code == 401
    assert "Authentication failed" in str(exc_info.value)


@pytest.mark.asyncio
async def test_gnews_rate_limit_429(mock_settings):
    """Verify ProviderRateLimitError is raised on 429 with Retry-After respected."""
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            429,
            headers={"Retry-After": "60"},
            json={"errors": ["Rate limit exceeded"]},
        )

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    adapter = GNewsAdapter(settings=mock_settings, max_retries=0)

    with pytest.raises(ProviderRateLimitError) as exc_info:
        await adapter.fetch_news(category="Technology", limit=10, client=client)
    assert exc_info.value.status_code == 429
    assert exc_info.value.retry_after == 60


@pytest.mark.asyncio
async def test_gnews_server_error_500(mock_settings):
    """Verify ProviderServerError is raised on 500 response."""
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json={"errors": ["Internal GNews error"]})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    adapter = GNewsAdapter(settings=mock_settings, max_retries=0)

    with pytest.raises(ProviderServerError) as exc_info:
        await adapter.fetch_news(category="Technology", limit=10, client=client)
    assert exc_info.value.status_code == 500


@pytest.mark.asyncio
async def test_gnews_timeout(mock_settings):
    """Verify ProviderTimeoutError is raised when request times out."""
    async def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("Read timed out")

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    adapter = GNewsAdapter(settings=mock_settings, max_retries=0)

    with pytest.raises(ProviderTimeoutError) as exc_info:
        await adapter.fetch_news(category="Technology", limit=10, client=client)
    assert exc_info.value.status_code == 504


@pytest.mark.asyncio
async def test_gnews_connection_failure(mock_settings):
    """Verify ProviderConnectionError is raised on network error."""
    async def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("Failed to establish connection")

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    adapter = GNewsAdapter(settings=mock_settings, max_retries=0)

    with pytest.raises(ProviderConnectionError) as exc_info:
        await adapter.fetch_news(category="Technology", limit=10, client=client)
    assert exc_info.value.status_code == 502


@pytest.mark.asyncio
async def test_gnews_missing_api_key(mock_empty_settings):
    """Verify ConfigurationError when GNEWS_API_KEY is not configured."""
    adapter = GNewsAdapter(settings=mock_empty_settings, max_retries=0)
    with pytest.raises(ConfigurationError):
        await adapter.fetch_news(category="Technology", limit=10)


@pytest.mark.asyncio
async def test_gnews_invalid_category_rejected(mock_settings):
    """Verify InvalidCategoryError when an unsupported category is passed."""
    adapter = GNewsAdapter(settings=mock_settings)
    with pytest.raises(InvalidCategoryError):
        await adapter.fetch_news(category="TotallyInvalidTopicXYZ", limit=10)
