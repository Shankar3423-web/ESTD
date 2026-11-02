"""Base adapter for external news providers."""
import asyncio
from abc import ABC, abstractmethod
import time
from typing import Any, Dict, List, Optional
import httpx

from backend.common.exceptions.custom_exceptions import (
    ProviderAuthenticationError,
    ProviderConnectionError,
    ProviderRateLimitError,
    ProviderResponseError,
    ProviderServerError,
    ProviderTimeoutError,
)
from backend.common.logging.logger import (
    log_request_error,
    log_request_start,
    log_request_success,
    logger,
)
from backend.step1_source_collection.models.news_item import NewsItem


class BaseNewsAdapter(ABC):
    """Abstract base class for all news provider adapters."""

    def __init__(
        self,
        provider_name: str,
        timeout_seconds: float = 15.0,
        max_retries: int = 2,
    ):
        self.provider_name = provider_name
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self._user_agent = f"ESTD-NewsAggregator/1.0 (+https://github.com/ESTD)"

    @abstractmethod
    async def fetch_news(self, category: str, limit: int = 10) -> List[NewsItem]:
        """Fetch and normalize news articles for a given category.

        Args:
            category: Standardized ESTD category.
            limit: Maximum number of articles to return.

        Returns:
            List of normalized NewsItem instances.
        """
        pass

    async def _execute_http_request(
        self,
        url: str,
        params: Dict[str, Any],
        category: str,
        limit: int,
        client: Optional[httpx.AsyncClient] = None,
    ) -> Dict[str, Any]:
        """Execute an asynchronous HTTP request with error handling and retry for transient server errors.

        Ensures API keys are never exposed in exception messages or logs.
        """
        log_request_start(self.provider_name, category, limit)
        start_time = time.perf_counter()

        headers = {
            "User-Agent": self._user_agent,
            "Accept": "application/json",
        }

        # If a client is passed in (e.g. from tests or dependency injection), reuse it;
        # otherwise create a dedicated client for this request.
        should_close_client = False
        if client is None:
            client = httpx.AsyncClient(timeout=self.timeout_seconds)
            should_close_client = True

        attempt = 0
        try:
            while True:
                attempt += 1
                try:
                    response = await client.get(url, params=params, headers=headers)

                    # Handle 401 / 403 Authentication Errors
                    if response.status_code in (401, 403):
                        log_request_error(
                            self.provider_name,
                            category,
                            "Authentication failed with provider (invalid or inactive API key)",
                            response.status_code,
                        )
                        raise ProviderAuthenticationError(
                            provider=self.provider_name,
                            message=f"Authentication failed for {self.provider_name}. Check API key configuration.",
                        )

                    # Handle 429 Rate Limit
                    if response.status_code == 429:
                        retry_after_header = response.headers.get("Retry-After")
                        retry_after_val: Optional[int] = None
                        if retry_after_header and retry_after_header.isdigit():
                            retry_after_val = int(retry_after_header)

                        log_request_error(
                            self.provider_name,
                            category,
                            f"Rate limit exceeded (Retry-After: {retry_after_val}s)",
                            response.status_code,
                        )
                        raise ProviderRateLimitError(
                            provider=self.provider_name,
                            retry_after=retry_after_val,
                            message=f"Rate limit exceeded for {self.provider_name}. Please try again later.",
                        )

                    # Handle 5xx Server Errors (with retry for transient 502/503/504)
                    if response.status_code >= 500:
                        if response.status_code in (502, 503, 504) and attempt <= self.max_retries:
                            backoff = 0.5 * (2 ** (attempt - 1))
                            logger.warning(
                                f"[{self.provider_name.upper()}] Transient {response.status_code} error, "
                                f"retrying in {backoff:.1f}s (attempt {attempt}/{self.max_retries})..."
                            )
                            await asyncio.sleep(backoff)
                            continue

                        log_request_error(
                            self.provider_name,
                            category,
                            f"Server returned status {response.status_code}",
                            response.status_code,
                        )
                        raise ProviderServerError(
                            provider=self.provider_name,
                            status_code=response.status_code,
                            message=f"{self.provider_name} service returned an error (status {response.status_code}).",
                        )

                    # Handle other 4xx errors
                    if response.status_code >= 400:
                        log_request_error(
                            self.provider_name,
                            category,
                            f"Client error with status {response.status_code}",
                            response.status_code,
                        )
                        raise ProviderResponseError(
                            provider=self.provider_name,
                            message=f"Unexpected client error from {self.provider_name} (status {response.status_code}).",
                        )

                    # Parse JSON response
                    try:
                        data = response.json()
                    except Exception as json_err:
                        log_request_error(
                            self.provider_name,
                            category,
                            "Failed to parse JSON response",
                            response.status_code,
                        )
                        raise ProviderResponseError(
                            provider=self.provider_name,
                            message=f"Received invalid JSON from {self.provider_name}.",
                        ) from json_err

                    if not isinstance(data, dict):
                        log_request_error(
                            self.provider_name,
                            category,
                            "Response JSON is not an object",
                            response.status_code,
                        )
                        raise ProviderResponseError(
                            provider=self.provider_name,
                            message=f"Unexpected JSON structure from {self.provider_name}.",
                        )

                    duration_ms = (time.perf_counter() - start_time) * 1000
                    # Return parsed JSON
                    return data

                except (httpx.TimeoutException, TimeoutError) as timeout_err:
                    if attempt <= self.max_retries:
                        backoff = 0.5 * (2 ** (attempt - 1))
                        logger.warning(
                            f"[{self.provider_name.upper()}] Request timed out, retrying in {backoff:.1f}s "
                            f"(attempt {attempt}/{self.max_retries})..."
                        )
                        await asyncio.sleep(backoff)
                        continue

                    log_request_error(self.provider_name, category, "Request timed out")
                    raise ProviderTimeoutError(
                        provider=self.provider_name,
                        message=f"Request to {self.provider_name} timed out after {self.timeout_seconds}s.",
                    ) from timeout_err

                except httpx.NetworkError as net_err:
                    if attempt <= self.max_retries:
                        backoff = 0.5 * (2 ** (attempt - 1))
                        logger.warning(
                            f"[{self.provider_name.upper()}] Network error, retrying in {backoff:.1f}s "
                            f"(attempt {attempt}/{self.max_retries})..."
                        )
                        await asyncio.sleep(backoff)
                        continue

                    log_request_error(self.provider_name, category, "Network connection error")
                    raise ProviderConnectionError(
                        provider=self.provider_name,
                        message=f"Failed to connect to {self.provider_name} network.",
                    ) from net_err

        finally:
            if should_close_client:
                await client.aclose()
