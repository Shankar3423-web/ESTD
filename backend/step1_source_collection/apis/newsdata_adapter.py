"""NewsData.io API Adapter for ESTD Step 1 Source Collection."""
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
    ProviderAuthenticationError,
    ProviderRateLimitError,
    ProviderResponseError,
)
from backend.common.logging.logger import log_request_success
from backend.common.utils.datetime_utils import get_utc_now_iso, normalize_datetime_to_iso
from backend.step1_source_collection.apis.base_adapter import BaseNewsAdapter
from backend.step1_source_collection.models.news_item import NewsItem


class NewsDataAdapter(BaseNewsAdapter):
    """Adapter for interacting with the NewsData.io API."""

    BASE_URL = "https://newsdata.io/api/1/news"

    # Category mappings: Direct NewsData.io categories
    # NewsData supports: business, entertainment, sports, technology directly
    DIRECT_CATEGORY_MAP = {
        ESTDCategory.ENTERTAINMENT.value: "entertainment",
        ESTDCategory.SPORTS.value: "sports",
        ESTDCategory.TECH.value: "technology",
        ESTDCategory.BUSINESS_FINANCE.value: "business",
    }

    # For Developments, use search query mapping
    SEARCH_QUERY_MAP = {
        ESTDCategory.DEVELOPMENTS.value: '"policy" OR "infrastructure" OR "government" OR "research"',
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
            provider_name=NewsProvider.NEWSDATA.value,
            timeout_seconds=timeout,
            max_retries=retries,
        )

    async def fetch_news(
        self,
        category: str,
        limit: int = 10,
        client: Optional[httpx.AsyncClient] = None,
    ) -> List[NewsItem]:
        """Fetch and normalize articles from NewsData.io for the given ESTD category."""
        canonical_category = resolve_canonical_category(category)
        if not canonical_category:
            raise InvalidCategoryError(category)

        # Ensure API key is configured before making request
        api_key = self._settings.get_newsdata_api_key()

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

        results = self._parse_results(data)
        normalized_items = self._normalize_results(results, canonical_category)

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
        """Construct URL and query parameters for NewsData.io."""
        # NewsData allows size up to 10 for free, and up to 50 for paid plans
        safe_limit = max(1, min(limit, 50))

        params: Dict[str, Any] = {
            "apikey": api_key,
            "language": "en",
            "size": safe_limit,
        }

        if category in self.DIRECT_CATEGORY_MAP:
            params["category"] = self.DIRECT_CATEGORY_MAP[category]
        elif category in self.SEARCH_QUERY_MAP:
            params["q"] = self.SEARCH_QUERY_MAP[category]
        else:
            raise InvalidCategoryError(category)

        return self.BASE_URL, params

    def _parse_results(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Validate and extract results list from raw NewsData.io JSON payload."""
        status = data.get("status")

        # NewsData error response handling
        if status == "error":
            error_data = data.get("results")
            error_msg = "Unknown NewsData.io error"
            code = ""
            if isinstance(error_data, dict):
                error_msg = error_data.get("message", error_msg)
                code = error_data.get("code", "")
            elif isinstance(error_data, str):
                error_msg = error_data

            if "Unauthorized" in code or "Forbidden" in code or "unauthorized" in error_msg.lower():
                raise ProviderAuthenticationError(
                    provider=self.provider_name,
                    message=f"NewsData authentication failed: {error_msg}",
                )
            if "RateLimit" in code or "rate limit" in error_msg.lower():
                raise ProviderRateLimitError(
                    provider=self.provider_name,
                    message=f"NewsData rate limit exceeded: {error_msg}",
                )

            raise ProviderResponseError(
                provider=self.provider_name,
                message=f"NewsData.io returned error status: {error_msg}",
            )

        if "results" not in data:
            raise ProviderResponseError(
                provider=self.provider_name,
                message="Unexpected NewsData response: missing 'results' field.",
            )

        results = data["results"]
        if not isinstance(results, list):
            raise ProviderResponseError(
                provider=self.provider_name,
                message="Invalid NewsData response: 'results' must be a list.",
            )

        return results

    def _normalize_results(
        self,
        results: List[Dict[str, Any]],
        category: str,
    ) -> List[NewsItem]:
        """Convert NewsData results into standardized NewsItem instances."""
        normalized: List[NewsItem] = []
        collected_now = get_utc_now_iso()

        for res in results:
            if not isinstance(res, dict):
                continue

            title = res.get("title")
            url = res.get("link")

            # Skip items missing mandatory fields
            if not title or not url or not str(title).strip() or not str(url).strip():
                continue

            # Extract source name
            source_name = res.get("source_name") or res.get("source_id")

            # Extract author from creator field
            author: Optional[str] = None
            creator = res.get("creator")
            if isinstance(creator, list) and creator:
                valid_creators = [str(c).strip() for c in creator if c and str(c).strip()]
                if valid_creators:
                    author = ", ".join(valid_creators)
            elif isinstance(creator, str) and creator.strip():
                author = creator.strip()

            # Parse publication timestamp
            published_at = normalize_datetime_to_iso(res.get("pubDate"))

            news_item = NewsItem(
                title=str(title).strip(),
                description=res.get("description"),
                url=str(url).strip(),
                source_name=str(source_name).strip() if source_name else None,
                source_type=self.provider_name,
                author=author,
                published_at=published_at,
                category=category,
                image_url=res.get("image_url"),
                collected_at=collected_now,
            )
            normalized.append(news_item)

        return normalized
