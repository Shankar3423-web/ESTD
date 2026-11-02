"""Unit tests for NewsDataAdapter with mocked HTTP responses."""
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
from backend.step1_source_collection.apis.newsdata_adapter import NewsDataAdapter


@pytest.mark.asyncio
async def test_newsdata_successful_fetch_sports(mock_settings, sample_newsdata_response):
    """Verify successful NewsData fetch and normalization for Sports category."""
    async def handler(request: httpx.Request) -> httpx.Response:
        assert "newsdata.io/api/1/news" in str(request.url)
        assert "category=sports" in str(request.url)
        assert "apikey=test_newsdata_key_67890" in str(request.url)
        return httpx.Response(200, json=sample_newsdata_response)

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    adapter = NewsDataAdapter(settings=mock_settings, max_retries=0)

    items = await adapter.fetch_news(category="Sports", limit=5, client=client)

    assert len(items) == 2
    # Item 1 has multiple creators
    assert items[0].title == "Breakthrough in Fusion Energy"
    assert items[0].author == "Dr. Jane Doe, Dr. Alan Smith"
    assert items[0].source_name == "Nature Journal"
    assert items[0].source_type == "newsdata"
    assert items[0].category == "Sports"
    assert items[0].published_at == "2026-09-30T06:45:00Z"
    assert items[0].url == "https://example.com/fusion-energy"

    # Item 2 has creator=None and source_name fallback to source_id
    assert items[1].title == "Autonomous Rovers Map Deep Oceanic Trenches"
    assert items[1].author is None
    assert items[1].source_name == "deepsea_news"
    assert items[1].source_type == "newsdata"
    assert items[1].published_at == "2026-09-29T22:10:00Z"


@pytest.mark.asyncio
async def test_newsdata_developments_query_routing(mock_settings, sample_newsdata_response):
    """Verify that Developments category routes with q parameter."""
    captured_urls = []

    async def handler(request: httpx.Request) -> httpx.Response:
        captured_urls.append(str(request.url))
        return httpx.Response(200, json=sample_newsdata_response)

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    adapter = NewsDataAdapter(settings=mock_settings, max_retries=0)

    items = await adapter.fetch_news(category=ESTDCategory.DEVELOPMENTS.value, limit=5, client=client)

    assert len(captured_urls) == 1
    assert "q=" in captured_urls[0]
    assert "category=" not in captured_urls[0]
    assert all(item.category == "Developments" for item in items)


@pytest.mark.asyncio
async def test_newsdata_empty_results(mock_settings):
    """Verify handling when NewsData returns 0 results."""
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"status": "success", "totalResults": 0, "results": []})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    adapter = NewsDataAdapter(settings=mock_settings, max_retries=0)

    items = await adapter.fetch_news(category="Education", limit=10, client=client)
    assert items == []


@pytest.mark.asyncio
async def test_newsdata_error_status_auth_failure(mock_settings):
    """Verify ProviderAuthenticationError is raised when status=error with Unauthorized code."""
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "status": "error",
                "results": {
                    "message": "Invalid API key provided.",
                    "code": "Unauthorized",
                },
            },
        )

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    adapter = NewsDataAdapter(settings=mock_settings, max_retries=0)

    with pytest.raises(ProviderAuthenticationError) as exc_info:
        await adapter.fetch_news(category="Business", limit=10, client=client)
    assert "Invalid API key provided" in str(exc_info.value)


@pytest.mark.asyncio
async def test_newsdata_error_status_rate_limit(mock_settings):
    """Verify ProviderRateLimitError is raised when status=error with RateLimitExceeded code."""
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "status": "error",
                "results": {
                    "message": "You have exceeded your request rate limit.",
                    "code": "RateLimitExceeded",
                },
            },
        )

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    adapter = NewsDataAdapter(settings=mock_settings, max_retries=0)

    with pytest.raises(ProviderRateLimitError) as exc_info:
        await adapter.fetch_news(category="Technology", limit=10, client=client)
    assert "rate limit exceeded" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_newsdata_malformed_missing_results(mock_settings):
    """Verify ProviderResponseError is raised when 'results' key is absent."""
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"status": "success", "something_else": 123})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    adapter = NewsDataAdapter(settings=mock_settings, max_retries=0)

    with pytest.raises(ProviderResponseError) as exc_info:
        await adapter.fetch_news(category="Science", limit=10, client=client)
    assert "missing 'results' field" in str(exc_info.value)


@pytest.mark.asyncio
async def test_newsdata_auth_error_http_401(mock_settings):
    """Verify ProviderAuthenticationError is raised on HTTP 401."""
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"status": "error", "results": {"message": "Forbidden"}})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    adapter = NewsDataAdapter(settings=mock_settings, max_retries=0)

    with pytest.raises(ProviderAuthenticationError):
        await adapter.fetch_news(category="Technology", limit=10, client=client)


@pytest.mark.asyncio
async def test_newsdata_rate_limit_http_429(mock_settings):
    """Verify ProviderRateLimitError is raised on HTTP 429."""
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(429, headers={"Retry-After": "30"}, json={})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    adapter = NewsDataAdapter(settings=mock_settings, max_retries=0)

    with pytest.raises(ProviderRateLimitError) as exc_info:
        await adapter.fetch_news(category="Technology", limit=10, client=client)
    assert exc_info.value.retry_after == 30


@pytest.mark.asyncio
async def test_newsdata_server_error_500(mock_settings):
    """Verify ProviderServerError is raised on HTTP 500."""
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json={"error": "Server error"})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    adapter = NewsDataAdapter(settings=mock_settings, max_retries=0)

    with pytest.raises(ProviderServerError):
        await adapter.fetch_news(category="Technology", limit=10, client=client)


@pytest.mark.asyncio
async def test_newsdata_timeout(mock_settings):
    """Verify ProviderTimeoutError is raised on request timeout."""
    async def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("Timeout connecting to NewsData")

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    adapter = NewsDataAdapter(settings=mock_settings, max_retries=0)

    with pytest.raises(ProviderTimeoutError):
        await adapter.fetch_news(category="Technology", limit=10, client=client)


@pytest.mark.asyncio
async def test_newsdata_connection_failure(mock_settings):
    """Verify ProviderConnectionError is raised on network error."""
    async def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("Network is unreachable")

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    adapter = NewsDataAdapter(settings=mock_settings, max_retries=0)

    with pytest.raises(ProviderConnectionError):
        await adapter.fetch_news(category="Technology", limit=10, client=client)


@pytest.mark.asyncio
async def test_newsdata_missing_api_key(mock_empty_settings):
    """Verify ConfigurationError when NEWSDATA_API_KEY is missing."""
    adapter = NewsDataAdapter(settings=mock_empty_settings, max_retries=0)
    with pytest.raises(ConfigurationError):
        await adapter.fetch_news(category="Technology", limit=10)


@pytest.mark.asyncio
async def test_newsdata_invalid_category_rejected(mock_settings):
    """Verify InvalidCategoryError when unsupported category is requested."""
    adapter = NewsDataAdapter(settings=mock_settings)
    with pytest.raises(InvalidCategoryError):
        await adapter.fetch_news(category="TotallyInvalidTopicXYZ", limit=10)
