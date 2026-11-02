"""Service layer for Step 1 Source Collection."""
from typing import Optional
import httpx

from backend.common.constants.categories import (
    VALID_CATEGORIES,
    resolve_canonical_category,
)
from backend.common.constants.providers import NewsProvider
from backend.common.exceptions.custom_exceptions import (
    ESTDException,
    InvalidCategoryError,
)
from backend.step1_source_collection.apis.gnews_adapter import GNewsAdapter
from backend.step1_source_collection.apis.newsdata_adapter import NewsDataAdapter
from backend.step1_source_collection.models.response_models import CollectionResponse
from backend.step1_source_collection.rss.services.rss_service import RSSCollectionService


class SourceCollectionService:
    """Orchestrates news fetching and normalization across providers."""

    def __init__(
        self,
        gnews_adapter: Optional[GNewsAdapter] = None,
        newsdata_adapter: Optional[NewsDataAdapter] = None,
        rss_service: Optional[RSSCollectionService] = None,
    ):
        self.gnews_adapter = gnews_adapter or GNewsAdapter()
        self.newsdata_adapter = newsdata_adapter or NewsDataAdapter()
        self.rss_service = rss_service or RSSCollectionService()

    def _validate_category(self, category: str) -> str:
        """Ensure the category matches or resolves to one of the five official ESTD categories."""
        canonical = resolve_canonical_category(category)
        if not canonical or canonical not in VALID_CATEGORIES:
            raise InvalidCategoryError(category)
        return canonical

    async def collect_from_gnews(
        self,
        category: str,
        limit: int = 10,
        client: Optional[httpx.AsyncClient] = None,
    ) -> CollectionResponse:
        """Fetch and normalize articles from GNews.

        Args:
            category: One of the 5 ESTD categories.
            limit: Maximum number of articles to return.
            client: Optional httpx AsyncClient for dependency injection/testing.

        Returns:
            Standardized CollectionResponse.
        """
        canonical = self._validate_category(category)
        items = await self.gnews_adapter.fetch_news(category=canonical, limit=limit, client=client)
        return CollectionResponse(
            provider=NewsProvider.GNEWS.value,
            category=canonical,
            count=len(items),
            items=items,
        )

    async def collect_from_newsdata(
        self,
        category: str,
        limit: int = 10,
        client: Optional[httpx.AsyncClient] = None,
    ) -> CollectionResponse:
        """Fetch and normalize articles from NewsData.io.

        Args:
            category: One of the 5 ESTD categories.
            limit: Maximum number of articles to return.
            client: Optional httpx AsyncClient for dependency injection/testing.

        Returns:
            Standardized CollectionResponse.
        """
        canonical = self._validate_category(category)
        items = await self.newsdata_adapter.fetch_news(category=canonical, limit=limit, client=client)
        return CollectionResponse(
            provider=NewsProvider.NEWSDATA.value,
            category=canonical,
            count=len(items),
            items=items,
        )

    async def collect_from_rss(
        self,
        category: str,
        limit: int = 10,
        client: Optional[httpx.AsyncClient] = None,
    ) -> CollectionResponse:
        """Fetch and normalize articles from curated RSS feeds for a given category.

        Args:
            category: One of the 5 ESTD categories.
            limit: Maximum number of articles to return.
            client: Optional httpx AsyncClient for dependency injection/testing.

        Returns:
            Standardized CollectionResponse.
        """
        canonical = self._validate_category(category)
        return await self.rss_service.collect_by_category(category=canonical, limit=limit, client=client)

    async def collect_news(
        self,
        provider: str,
        category: str,
        limit: int = 10,
        client: Optional[httpx.AsyncClient] = None,
    ) -> CollectionResponse:
        """Generic collection dispatcher by provider name."""
        provider_lower = provider.lower().strip()
        if provider_lower == NewsProvider.GNEWS.value:
            return await self.collect_from_gnews(category=category, limit=limit, client=client)
        elif provider_lower == NewsProvider.NEWSDATA.value:
            return await self.collect_from_newsdata(category=category, limit=limit, client=client)
        elif provider_lower == NewsProvider.RSS.value:
            return await self.collect_from_rss(category=category, limit=limit, client=client)
        else:
            raise ESTDException(
                message=f"Unsupported news provider '{provider}'. Supported providers: {[p.value for p in NewsProvider]}",
                code="UNSUPPORTED_PROVIDER",
            )

