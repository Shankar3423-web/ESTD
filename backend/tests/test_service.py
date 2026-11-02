"""Unit tests for SourceCollectionService."""
import httpx
import pytest

from backend.common.exceptions.custom_exceptions import ESTDException, InvalidCategoryError
from backend.step1_source_collection.apis.gnews_adapter import GNewsAdapter
from backend.step1_source_collection.apis.newsdata_adapter import NewsDataAdapter
from backend.step1_source_collection.services.source_collection_service import (
    SourceCollectionService,
)


@pytest.mark.asyncio
async def test_service_collect_gnews(mock_settings, sample_gnews_response):
    """Verify service coordination for GNews collection."""
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=sample_gnews_response)

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    gnews_adapter = GNewsAdapter(settings=mock_settings, max_retries=0)
    service = SourceCollectionService(gnews_adapter=gnews_adapter)

    response = await service.collect_from_gnews(category="Technology", limit=5, client=client)

    assert response.provider == "gnews"
    assert response.category == "Tech"
    assert response.count == 2
    assert len(response.items) == 2


@pytest.mark.asyncio
async def test_service_collect_newsdata(mock_settings, sample_newsdata_response):
    """Verify service coordination for NewsData collection."""
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=sample_newsdata_response)

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    newsdata_adapter = NewsDataAdapter(settings=mock_settings, max_retries=0)
    service = SourceCollectionService(newsdata_adapter=newsdata_adapter)

    response = await service.collect_from_newsdata(category="Science", limit=5, client=client)

    assert response.provider == "newsdata"
    assert response.category == "Developments"
    assert response.count == 2
    assert len(response.items) == 2


@pytest.mark.asyncio
async def test_service_invalid_category_rejected():
    """Verify service rejects unsupported categories before hitting adapters."""
    service = SourceCollectionService()
    with pytest.raises(InvalidCategoryError):
        await service.collect_from_gnews(category="NonExistentCategory")
    with pytest.raises(InvalidCategoryError):
        await service.collect_from_newsdata(category="Celebrity")


@pytest.mark.asyncio
async def test_service_dispatcher(mock_settings, sample_gnews_response):
    """Verify generic collect_news dispatcher works by provider name."""
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=sample_gnews_response)

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    gnews_adapter = GNewsAdapter(settings=mock_settings, max_retries=0)
    service = SourceCollectionService(gnews_adapter=gnews_adapter)

    res = await service.collect_news(provider="gnews", category="Business", limit=2, client=client)
    assert res.provider == "gnews"

    with pytest.raises(ESTDException) as exc_info:
        await service.collect_news(provider="unknown_provider", category="Business")
    assert exc_info.value.code == "UNSUPPORTED_PROVIDER"
