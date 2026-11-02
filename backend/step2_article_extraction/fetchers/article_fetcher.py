"""Asynchronous HTTP article webpage fetcher with robust error handling and timeout protection."""
import time
from typing import Optional
import httpx

from backend.common.logging.logger import logger
from backend.step2_article_extraction.config import ExtractionConfig, extraction_config
from backend.step2_article_extraction.exceptions.extraction_exceptions import (
    ArticleFetchConnectionError,
    ArticleFetchError,
    ArticleFetchHTTPError,
    ArticleFetchTimeoutError,
    EmptyWebpageError,
)
from backend.step2_article_extraction.fetchers.url_validator import URLValidator


class ArticleFetcher:
    """Fetches remote article HTML content safely with timeout and error handling."""

    def __init__(
        self,
        config: Optional[ExtractionConfig] = None,
        client: Optional[httpx.AsyncClient] = None,
    ):
        self.config = config or extraction_config
        self.validator = URLValidator(allow_private_ips=self.config.allow_private_ips)
        self._external_client = client

    async def fetch_html(self, url: str) -> str:
        """Fetch the raw HTML string of an article webpage.

        Args:
            url: The HTTP/HTTPS URL of the article.

        Returns:
            The raw HTML content of the page.

        Raises:
            InvalidURLError: If URL format is invalid.
            SSRFSecurityError: If URL targets forbidden internal addresses.
            ArticleFetchTimeoutError: If the request times out.
            ArticleFetchConnectionError: If network connection fails.
            ArticleFetchHTTPError: If HTTP 4xx or 5xx status is returned.
            EmptyWebpageError: If the response is empty.
        """
        validated_url = self.validator.validate_url(url)
        start_time = time.perf_counter()

        headers = {
            "User-Agent": self.config.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }

        logger.info(f"[FETCHER] Fetching article webpage | url='{validated_url}'")

        try:
            if self._external_client:
                response = await self._external_client.get(
                    validated_url,
                    headers=headers,
                    follow_redirects=True,
                    timeout=self.config.fetch_timeout_seconds,
                )
            else:
                async with httpx.AsyncClient(
                    timeout=self.config.fetch_timeout_seconds,
                    follow_redirects=True,
                    max_redirects=self.config.max_redirects,
                ) as client:
                    response = await client.get(validated_url, headers=headers)

            duration_ms = (time.perf_counter() - start_time) * 1000

            # Validate HTTP status
            if response.is_error:
                logger.error(
                    f"[FETCHER] Fetch failed with HTTP status | url='{validated_url}' | "
                    f"status_code={response.status_code} | duration={duration_ms:.2f}ms"
                )
                raise ArticleFetchHTTPError(
                    url=validated_url,
                    status_code=response.status_code,
                    reason=response.reason_phrase,
                )

            # Check content length
            content_bytes = response.content
            if len(content_bytes) > self.config.max_response_bytes:
                raise ArticleFetchError(
                    url=validated_url,
                    message=f"Page response size ({len(content_bytes)} bytes) exceeds limit ({self.config.max_response_bytes} bytes).",
                )

            # Validate Content-Type if present (must not be binary file)
            content_type = response.headers.get("content-type", "").lower()
            if content_type and not any(
                allowed in content_type for allowed in ["text/html", "application/xhtml", "text/plain", "application/xml"]
            ):
                raise ArticleFetchError(
                    url=validated_url,
                    message=f"Unsupported content type '{content_type}'. Expected HTML.",
                )

            # Check for empty body
            html_text = response.text
            if not html_text or not html_text.strip():
                logger.warning(f"[FETCHER] Empty webpage content received | url='{validated_url}'")
                raise EmptyWebpageError(validated_url)

            logger.info(
                f"[FETCHER] Successfully fetched webpage | url='{validated_url}' | "
                f"bytes={len(content_bytes)} | duration={duration_ms:.2f}ms"
            )
            return html_text

        except httpx.TimeoutException:
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.error(
                f"[FETCHER] Request timed out | url='{validated_url}' | "
                f"timeout={self.config.fetch_timeout_seconds}s | duration={duration_ms:.2f}ms"
            )
            raise ArticleFetchTimeoutError(
                url=validated_url,
                timeout_seconds=self.config.fetch_timeout_seconds,
            )

        except (httpx.ConnectError, httpx.NetworkError, httpx.ConnectTimeout) as exc:
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.error(
                f"[FETCHER] Connection error | url='{validated_url}' | error='{str(exc)}' | duration={duration_ms:.2f}ms"
            )
            raise ArticleFetchConnectionError(url=validated_url, detail=str(exc))

        except (ArticleFetchError, EmptyWebpageError):
            raise

        except Exception as exc:
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.error(
                f"[FETCHER] Unexpected error during fetch | url='{validated_url}' | error='{str(exc)}' | duration={duration_ms:.2f}ms"
            )
            raise ArticleFetchError(url=validated_url, message=str(exc))
