"""GNews API Adapter for ESTD Step 1 Source Collection."""
import time
from typing import Any, Dict, List, Optional
import httpx

from backend.common.config.settings import Settings, get_settings
from backend.common.constants.categories import (
    ESTDCategory,
    VALID_CATEGORIES,
    resolve_canonical_category,
)
from backend.common.constants.providers import NewsProvider
from backend.common.exceptions.custom_exceptions import (
    InvalidCategoryError,
    ProviderResponseError,
)
from backend.common.logging.logger import log_request_success
from backend.common.utils.datetime_utils import get_utc_now_iso, normalize_datetime_to_iso
from backend.step1_source_collection.apis.base_adapter import BaseNewsAdapter
from backend.step1_source_collection.models.news_item import NewsItem


class GNewsAdapter(BaseNewsAdapter):
    """Adapter for interacting with the GNews API (v4)."""

    BASE_URL = "https://gnews.io/api/v4"

    # Category mappings: Direct GNews category vs. Search query
    # GNews /top-headlines supports: business, technology, science, general, world, nation, entertainment, sports, health
    DIRECT_CATEGORY_MAP = {
        ESTDCategory.ENTERTAINMENT.value: "entertainment",
        ESTDCategory.SPORTS.value: "sports",
        ESTDCategory.TECH.value: "technology",
        ESTDCategory.BUSINESS_FINANCE.value: "business",
    }

    # For categories not directly supported as top-headline categories in GNews, use /search endpoint
    SEARCH_QUERY_MAP = {
        ESTDCategory.DEVELOPMENTS.value: '"developments" OR "public policy" OR "infrastructure" OR "research"',
    }

    def __init__(
        self,
        settings: Optional[Settings] = None,
        timeout_seconds: Optional[float] = None,
        max_retries: Optional[int] = None,
    ):
        self._settings = settings or get_settings()
        timeout = timeout_seconds or self._settings.http_timeout_seconds
        retries = max_retries if max_retries is not None else self._settings.http_max_retries
        super().__init__(
            provider_name=NewsProvider.GNEWS.value,
            timeout_seconds=timeout,
            max_retries=retries,
        )

    async def fetch_news(
        self,
        category: str,
        limit: int = 10,
        client: Optional[httpx.AsyncClient] = None,
    ) -> List[NewsItem]:
        """Fetch and normalize articles from GNews for the given ESTD category."""
        canonical_category = resolve_canonical_category(category)
        if not canonical_category:
            raise InvalidCategoryError(category)

        # Ensure API key is configured before making request
        api_key = self._settings.get_gnews_api_key()

        # Build endpoint and parameters
        url, params = self._build_request_params(canonical_category, limit, api_key)

        start_time = time.perf_counter()
        data = await self._execute_http_request(
            url=url,
            params=params,
            category=canonical_category,
            limit=limit,
            client=client,
        )

        articles = self._parse_articles(data)
        normalized_items = self._normalize_articles(articles, canonical_category)

        duration_ms = (time.perf_counter() - start_time) * 1000
        log_request_success(
            provider=self.provider_name,
            category=canonical_category,
            count=len(normalized_items),
            duration_ms=duration_ms,
        )

        return normalized_items

    def _build_request_params(
        self,
        category: str,
        limit: int,
        api_key: str,
    ) -> tuple[str, Dict[str, Any]]:
        """Construct the URL and query parameters for GNews."""
        # Clamp limit to positive range (max 10 for free tier, allow up to 50 if supported)
        safe_limit = max(1, min(limit, 50))

        params: Dict[str, Any] = {
            "apikey": api_key,
            "lang": "en",
            "max": safe_limit,
        }

        if category in self.DIRECT_CATEGORY_MAP:
            url = f"{self.BASE_URL}/top-headlines"
            params["category"] = self.DIRECT_CATEGORY_MAP[category]
        elif category in self.SEARCH_QUERY_MAP:
            url = f"{self.BASE_URL}/search"
            params["q"] = self.SEARCH_QUERY_MAP[category]
        else:
            raise InvalidCategoryError(category)

        return url, params

    def _parse_articles(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract article list from raw GNews JSON payload."""
        if "articles" not in data:
            # GNews errors may come as {"errors": [...]}
            if "errors" in data:
                error_msg = "; ".join(str(e) for e in data["errors"])
                raise ProviderResponseError(
                    provider=self.provider_name,
                    message=f"GNews API returned errors: {error_msg}",
                )
            raise ProviderResponseError(
                provider=self.provider_name,
                message="Unexpected GNews response: missing 'articles' field.",
            )

        articles = data["articles"]
        if not isinstance(articles, list):
            raise ProviderResponseError(
                provider=self.provider_name,
                message="Invalid GNews response: 'articles' must be a list.",
            )

        return articles

    def _normalize_articles(
        self,
        articles: List[Dict[str, Any]],
        category: str,
    ) -> List[NewsItem]:
        """Convert GNews articles into standardized NewsItem instances."""
        normalized: List[NewsItem] = []
        collected_now = get_utc_now_iso()

        for art in articles:
            if not isinstance(art, dict):
                continue

            title = art.get("title")
            url = art.get("url")

            # Skip items missing mandatory fields
            if not title or not url or not str(title).strip() or not str(url).strip():
                continue

            # Extract source name
            source_info = art.get("source")
            source_name = None
            if isinstance(source_info, dict):
                source_name = source_info.get("name")

            # Parse publication timestamp
            published_at = normalize_datetime_to_iso(art.get("publishedAt"))

            news_item = NewsItem(
                title=str(title).strip(),
                description=art.get("description"),
                url=str(url).strip(),
                source_name=source_name,
                source_type=self.provider_name,
                author=None,  # GNews API does not provide author
                published_at=published_at,
                category=category,
                image_url=art.get("image"),
                collected_at=collected_now,
            )
            normalized.append(news_item)

        return normalized
