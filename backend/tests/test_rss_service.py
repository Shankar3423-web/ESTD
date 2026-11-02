"""Unit tests for RSSCollectionService covering fault tolerance and deduplication."""
import httpx
import pytest

from backend.common.exceptions.custom_exceptions import (
    InvalidCategoryError,
    RSSFetchError,
    RSSTimeoutError,
)
from backend.step1_source_collection.rss.services.rss_service import RSSCollectionService
from backend.step1_source_collection.rss.sources.models import RSSSource
from backend.step1_source_collection.rss.sources.registry import RSSSourceRegistry


@pytest.mark.asyncio
async def test_collect_from_source_success(sample_rss_source, sample_rss_xml):
    """Verify collecting from a single RSSSource via mocked HTTPX."""
    async def handler(request: httpx.Request) -> httpx.Response:
        assert str(request.url) == sample_rss_source.feed_url
        return httpx.Response(200, content=sample_rss_xml.encode("utf-8"))

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    service = RSSCollectionService(timeout_seconds=5.0)

    items = await service.collect_from_source(sample_rss_source, limit=5, client=client)

    assert len(items) == 2
    assert items[0].title == "Autonomous Drones Deliver Medical Supplies"
    assert items[0].source_type == "rss"
    assert items[0].category == "Tech"


@pytest.mark.asyncio
async def test_collect_from_source_deduplication(sample_rss_source, sample_rss_duplicate_xml):
    """Verify that duplicate canonical URLs within a feed are collapsed to 1."""
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=sample_rss_duplicate_xml.encode("utf-8"))

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    service = RSSCollectionService(timeout_seconds=5.0)

    items = await service.collect_from_source(sample_rss_source, client=client)

    # sample_rss_duplicate_xml has 3 items: 2 have url 'https://example.com/article-alpha', 1 has 'article-beta'
    assert len(items) == 2
    urls = [i.url for i in items]
    assert urls == ["https://example.com/article-alpha", "https://example.com/article-beta"]


@pytest.mark.asyncio
async def test_collect_by_category_fault_tolerance(sample_rss_xml):
    """Verify that if one feed fails (404/500/timeout), other feeds in the category still succeed."""
    source_a = RSSSource(
        source_id="feed_a",
        source_name="Feed A Working",
        publisher="Publisher A",
        feed_url="https://feed-a.com/rss",
        category="Technology",
        enabled=True,
    )
    source_b_broken = RSSSource(
        source_id="feed_b",
        source_name="Feed B Broken 500",
        publisher="Publisher B",
        feed_url="https://feed-b.com/rss",
        category="Technology",
        enabled=True,
    )
    source_c_timeout = RSSSource(
        source_id="feed_c",
        source_name="Feed C Timeout",
        publisher="Publisher C",
        feed_url="https://feed-c.com/rss",
        category="Technology",
        enabled=True,
    )
    source_d = RSSSource(
        source_id="feed_d",
        source_name="Feed D Working",
        publisher="Publisher D",
        feed_url="https://feed-d.com/rss",
        category="Technology",
        enabled=True,
    )

    feed_d_xml = """<?xml version="1.0"?>
    <rss version="2.0">
      <channel>
        <title>Feed D</title>
        <item>
          <title>Article From Feed D</title>
          <link>https://feed-d.com/article-1</link>
          <pubDate>Wed, 30 Sep 2026 10:00:00 GMT</pubDate>
        </item>
      </channel>
    </rss>
    """

    async def handler(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        if "feed-a.com" in url:
            return httpx.Response(200, content=sample_rss_xml.encode("utf-8"))
        elif "feed-b.com" in url:
            return httpx.Response(500, content=b"Server error")
        elif "feed-c.com" in url:
            raise httpx.ReadTimeout("Simulated timeout on Feed C")
        elif "feed-d.com" in url:
            return httpx.Response(200, content=feed_d_xml.encode("utf-8"))
        return httpx.Response(404)

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    registry = RSSSourceRegistry(initial_sources=[source_a, source_b_broken, source_c_timeout, source_d])
    service = RSSCollectionService(registry=registry, timeout_seconds=2.0)

    # Run collection for Technology category
    response = await service.collect_by_category("Technology", limit=10, client=client)

    # Feeds B and C failed, but Feeds A (2 items) and D (1 item) should both be included
    assert response.provider == "rss"
    assert response.category == "Tech"
    assert response.count == 3
    assert len(response.items) == 3

    titles = [i.title for i in response.items]
    assert "Autonomous Drones Deliver Medical Supplies" in titles
    assert "Neuromorphic Chip Emulates Synaptic Plasticity" in titles
    assert "Article From Feed D" in titles


@pytest.mark.asyncio
async def test_collect_from_source_timeout_raises(sample_rss_source):
    """Verify that RSSTimeoutError is raised when directly calling collect_from_source on a timing-out feed."""
    async def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("Timed out")

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    service = RSSCollectionService(timeout_seconds=2.0)

    with pytest.raises(RSSTimeoutError) as exc_info:
        await service.collect_from_source(sample_rss_source, client=client)
    assert exc_info.value.code == "RSS_TIMEOUT"


@pytest.mark.asyncio
async def test_collect_from_source_http_error_raises(sample_rss_source):
    """Verify that RSSFetchError is raised when directly calling collect_from_source on 404."""
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, content=b"Not found")

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    service = RSSCollectionService(timeout_seconds=2.0)

    with pytest.raises(RSSFetchError) as exc_info:
        await service.collect_from_source(sample_rss_source, client=client)
    assert exc_info.value.code == "RSS_FETCH_FAILED"


@pytest.mark.asyncio
async def test_collect_by_category_invalid_category():
    """Verify InvalidCategoryError when non-ESTD category is passed."""
    service = RSSCollectionService()
    with pytest.raises(InvalidCategoryError):
        await service.collect_by_category("Automotive")


@pytest.mark.asyncio
async def test_collect_by_category_respects_limit(sample_rss_source, sample_rss_xml):
    """Verify limit parameter properly clamps the number of returned articles."""
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=sample_rss_xml.encode("utf-8"))

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    registry = RSSSourceRegistry(initial_sources=[sample_rss_source])
    service = RSSCollectionService(registry=registry)

    response = await service.collect_by_category("Technology", limit=1, client=client)
    assert response.count == 1
    assert len(response.items) == 1
