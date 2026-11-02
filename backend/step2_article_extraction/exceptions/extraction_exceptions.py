"""Step 2 domain exceptions for article fetching and extraction."""
from typing import Optional
from backend.common.exceptions.custom_exceptions import ESTDException


class ExtractionException(ESTDException):
    """Base exception for all Step 2 Article Extraction errors."""

    def __init__(self, message: str, code: str = "EXTRACTION_ERROR"):
        super().__init__(message=message, code=code)


class InvalidURLError(ExtractionException):
    """Raised when an article URL is malformed, missing scheme, or invalid."""

    def __init__(self, url: str, reason: str = "Invalid URL format."):
        super().__init__(
            message=f"Invalid article URL '{url}': {reason}",
            code="INVALID_ARTICLE_URL",
        )
        self.url = url


class SSRFSecurityError(ExtractionException):
    """Raised when an article URL resolves to a forbidden private, loopback, or local address."""

    def __init__(self, url: str, target: str):
        super().__init__(
            message=f"Security rejection: URL '{url}' targets private/internal address '{target}'.",
            code="SSRF_SECURITY_REJECTION",
        )
        self.url = url
        self.target = target


class ArticleFetchError(ExtractionException):
    """Base exception for HTTP errors when fetching an article page."""

    def __init__(
        self,
        url: str,
        message: str = "Failed to fetch article webpage.",
        code: str = "ARTICLE_FETCH_FAILED",
        status_code: Optional[int] = None,
    ):
        super().__init__(message=f"[{url}] {message}", code=code)
        self.url = url
        self.status_code = status_code


class ArticleFetchTimeoutError(ArticleFetchError):
    """Raised when fetching article webpage times out."""

    def __init__(self, url: str, timeout_seconds: float):
        super().__init__(
            url=url,
            message=f"Webpage request timed out after {timeout_seconds}s.",
            code="ARTICLE_FETCH_TIMEOUT",
            status_code=504,
        )
        self.timeout_seconds = timeout_seconds


class ArticleFetchConnectionError(ArticleFetchError):
    """Raised when connection to the article server fails (DNS, refusal, reset)."""

    def __init__(self, url: str, detail: str = "Network connection failed."):
        super().__init__(
            url=url,
            message=f"Connection failure: {detail}",
            code="ARTICLE_FETCH_CONNECTION_ERROR",
            status_code=502,
        )


class ArticleFetchHTTPError(ArticleFetchError):
    """Raised when the remote server returns a client or server error (4xx/5xx)."""

    def __init__(self, url: str, status_code: int, reason: str = "HTTP error"):
        super().__init__(
            url=url,
            message=f"HTTP {status_code} {reason}",
            code="ARTICLE_FETCH_HTTP_ERROR",
            status_code=status_code,
        )


class EmptyWebpageError(ExtractionException):
    """Raised when the fetched page response is empty or contains no parseable text."""

    def __init__(self, url: str):
        super().__init__(
            message=f"[{url}] Webpage returned an empty or unsupported response body.",
            code="EMPTY_WEBPAGE",
        )
        self.url = url


class ContentExtractionError(ExtractionException):
    """Raised when article extraction fails to find a meaningful article title or body."""

    def __init__(self, url: str, reason: str = "No readable article content found."):
        super().__init__(
            message=f"[{url}] Extraction failed: {reason}",
            code="CONTENT_EXTRACTION_FAILED",
        )
        self.url = url
