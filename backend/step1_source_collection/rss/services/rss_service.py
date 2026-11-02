"""RSS Collection Service for ESTD Step 1 Source Collection."""
import asyncio
import time
from typing import Dict, List, Optional, Set
import httpx

from backend.common.config.settings import Settings, get_settings
from backend.common.constants.categories import VALID_CATEGORIES
from backend.common.constants.providers import NewsProvider
from backend.common.exceptions.custom_exceptions import (
    InvalidCategoryError,
    RSSEmptyFeedError,
    RSSFetchError,
    RSSTimeoutError,
)
from backend.common.logging.logger import (
    log_rss_fetch_error,
    log_rss_fetch_start,
    log_rss_fetch_success,
    logger,
)
from backend.step1_source_collection.models.news_item import NewsItem
from backend.step1_source_collection.models.response_models import CollectionResponse
from backend.step1_source_collection.rss.services.rss_parser import RSSParser
from backend.step1_source_collection.rss.sources.models import RSSSource
from backend.step1_source_collection.rss.sources.registry import (
    RSSSourceRegistry,
    get_source_registry,
)


class RSSCollectionService:
    """Coordinates fetching, parsing, and normalizing RSS feeds across categories."""

    def __init__(
        self,
        registry: Optional[RSSSourceRegistry] = None,
        settings: Optional[Settings] = None,
        timeout_seconds: Optional[float] = None,
    ):
        self.registry = registry or get_source_registry()
        self.settings = settings or get_settings()
        self.timeout_seconds = timeout_seconds or self.settings.http_timeout_seconds
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 ESTD-NewsAggregator/1.0"

    def _normalize_category(self, category: str) -> str:
        """Validate and return official casing of category."""
        from backend.common.constants.categories import resolve_canonical_category
        resolved = resolve_canonical_category(category)
        if resolved:
            return resolved
        raise InvalidCategoryError(category)

    async def fetch_feed_content(
        self,
        source: RSSSource,
        client: Optional[httpx.AsyncClient] = None,
    ) -> bytes:
        """Fetch raw feed bytes via HTTPX with error translation and timeouts."""
        headers = {
            "User-Agent": self.user_agent,
            "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml, */*",
        }

        should_close = False
        if client is None:
            client = httpx.AsyncClient(timeout=self.timeout_seconds, follow_redirects=True)
            should_close = True

        try:
            response = await client.get(source.feed_url, headers=headers)
            if response.status_code >= 400:
                raise RSSFetchError(
                    source_id=source.source_id,
                    message=f"HTTP request failed with status {response.status_code}",
                )
            return response.content
        except (httpx.TimeoutException, TimeoutError) as timeout_err:
            raise RSSTimeoutError(
                source_id=source.source_id,
                timeout_seconds=self.timeout_seconds,
            ) from timeout_err
        except httpx.NetworkError as net_err:
            raise RSSFetchError(
                source_id=source.source_id,
                message=f"Network error connecting to feed: {net_err}",
            ) from net_err
        finally:
            if should_close:
                await client.aclose()

    async def collect_from_source(
        self,
        source: RSSSource,
        limit: Optional[int] = None,
        client: Optional[httpx.AsyncClient] = None,
    ) -> List[NewsItem]:
        """Fetch and normalize articles from a single RSSSource.

        Deduplicates within the source feed and respects limit.
        """
        start_time = time.perf_counter()
        log_rss_fetch_start(source.source_name, source.category, source.feed_url)

        try:
            content = await self.fetch_feed_content(source, client=client)
            items = RSSParser.parse_feed_content(content, source)

            # Obvious duplicate prevention by canonical URL within the feed
            unique_items: List[NewsItem] = []
            seen_urls: Set[str] = set()
            duplicates_count = 0

            for item in items:
                if item.url in seen_urls:
                    duplicates_count += 1
                    continue
                seen_urls.add(item.url)
                unique_items.append(item)

            if limit and limit > 0:
                unique_items = unique_items[:limit]

            duration_ms = (time.perf_counter() - start_time) * 1000
            log_rss_fetch_success(
                source_name=source.source_name,
                category=source.category,
                entries_count=len(items),
                normalized_count=len(unique_items),
                duplicates_removed=duplicates_count,
                duration_ms=duration_ms,
            )

            return unique_items

        except Exception as err:
            log_rss_fetch_error(source.source_name, source.category, str(err))
            raise

    async def collect_by_category(
        self,
        category: str,
        limit: int = 10,
        client: Optional[httpx.AsyncClient] = None,
    ) -> CollectionResponse:
        """Collect news from all enabled RSS sources in a category.

        Fault-tolerant: If one source fails, other sources continue processing.
        Deduplicates across sources by canonical URL.
        """
        normalized_cat = self._normalize_category(category)
        sources = self.registry.get_sources_by_category(normalized_cat, enabled_only=True)

        all_items: List[NewsItem] = []
        seen_urls: Set[str] = set()

        # Reusable client if not provided
        should_close = False
        if client is None:
            client = httpx.AsyncClient(timeout=self.timeout_seconds, follow_redirects=True)
            should_close = True

        try:
            for source in sources:
                try:
                    items = await self.collect_from_source(source, limit=limit, client=client)
                    for item in items:
                        if item.url not in seen_urls:
                            seen_urls.add(item.url)
                            all_items.append(item)
                except Exception as source_err:
                    # Log failure and continue with other sources in the category
                    logger.warning(
                        f"[RSS] Skipping failed feed source '{source.source_id}' "
                        f"in category '{normalized_cat}': {source_err}"
                    )
                    continue

            # Respect final requested limit
            if limit and limit > 0:
                all_items = all_items[:limit]

            return CollectionResponse(
                provider=NewsProvider.RSS.value,
                category=normalized_cat,
                count=len(all_items),
                items=all_items,
            )
        finally:
            if should_close:
                await client.aclose()

    async def collect_all(
        self,
        limit_per_category: int = 10,
        client: Optional[httpx.AsyncClient] = None,
    ) -> List[CollectionResponse]:
        """Collect news from all 5 ESTD categories."""
        results: List[CollectionResponse] = []
        for cat in VALID_CATEGORIES:
            res = await self.collect_by_category(cat, limit=limit_per_category, client=client)
            results.append(res)
        return results
