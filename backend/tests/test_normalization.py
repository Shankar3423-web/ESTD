"""Tests verifying normalization consistency across GNews, NewsData.io, and RSS."""
import httpx
import pytest

from backend.step1_source_collection.apis.gnews_adapter import GNewsAdapter
from backend.step1_source_collection.apis.newsdata_adapter import NewsDataAdapter
from backend.step1_source_collection.models.news_item import NewsItem
from backend.step1_source_collection.rss.services.rss_service import RSSCollectionService
from backend.step1_source_collection.rss.sources.registry import RSSSourceRegistry


@pytest.mark.asyncio
async def test_normalization_consistency_all_sources(
    mock_settings,
    sample_gnews_response,
    sample_newsdata_response,
    sample_rss_source,
    sample_rss_xml,
):
    """Verify that articles from GNews, NewsData, and RSS conform to identical NewsItem structure."""
    # 1. Fetch normalized GNews items
    async def gnews_mock(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=sample_gnews_response)

    gnews_client = httpx.AsyncClient(transport=httpx.MockTransport(gnews_mock))
    gnews_adapter = GNewsAdapter(settings=mock_settings, max_retries=0)
    gnews_items = await gnews_adapter.fetch_news(category="Technology", limit=10, client=gnews_client)

    # 2. Fetch normalized NewsData items
    async def newsdata_mock(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=sample_newsdata_response)

    newsdata_client = httpx.AsyncClient(transport=httpx.MockTransport(newsdata_mock))
    newsdata_adapter = NewsDataAdapter(settings=mock_settings, max_retries=0)
    newsdata_items = await newsdata_adapter.fetch_news(category="Science", limit=10, client=newsdata_client)

    # 3. Fetch normalized RSS items
    async def rss_mock(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=sample_rss_xml.encode("utf-8"))

    rss_client = httpx.AsyncClient(transport=httpx.MockTransport(rss_mock))
    rss_registry = RSSSourceRegistry(initial_sources=[sample_rss_source])
    rss_service = RSSCollectionService(registry=rss_registry, timeout_seconds=5.0)
    rss_items = await rss_service.collect_from_source(sample_rss_source, limit=10, client=rss_client)

    # 4. Combine all collections into a single uniform feed
    combined_feed: list[NewsItem] = [*gnews_items, *newsdata_items, *rss_items]

    assert len(combined_feed) == 6
    assert len(gnews_items) == 2
    assert len(newsdata_items) == 2
    assert len(rss_items) == 2

    # 5. Verify all items share the exact same schema, types, and non-null required fields
    expected_fields = {
        "title",
        "description",
        "url",
        "source_name",
        "source_type",
        "author",
        "published_at",
        "category",
        "subcategory",
        "original_source_category",
        "language",
        "region",
        "image_url",
        "collected_at",
    }

    for item in combined_feed:
        assert isinstance(item, NewsItem)
        item_dict = item.model_dump()
        assert set(item_dict.keys()) == expected_fields

        # Mandatory fields
        assert isinstance(item.title, str) and len(item.title) > 0
        assert isinstance(item.url, str) and item.url.startswith("https://")
        assert item.source_type in ("gnews", "newsdata", "rss")
        assert item.category in ("Tech", "Developments")
        assert isinstance(item.collected_at, str) and item.collected_at.endswith("Z")

        # Optional fields validation
        if item.published_at is not None:
            assert isinstance(item.published_at, str) and item.published_at.endswith("Z")
        if item.source_name is not None:
            assert isinstance(item.source_name, str) and len(item.source_name) > 0
        if item.description is not None:
            assert isinstance(item.description, str)
        if item.author is not None:
            assert isinstance(item.author, str)
        if item.image_url is not None:
            assert isinstance(item.image_url, str) and item.image_url.startswith("http")

    # 6. Check provider-specific source_type identifiers
    assert all(i.source_type == "gnews" for i in gnews_items)
    assert all(i.source_type == "newsdata" for i in newsdata_items)
    assert all(i.source_type == "rss" for i in rss_items)

