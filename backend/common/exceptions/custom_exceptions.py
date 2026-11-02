"""Custom domain exceptions for ESTD backend."""
from typing import Optional


class ESTDException(Exception):
    """Base exception for all ESTD errors."""

    def __init__(self, message: str, code: str = "INTERNAL_ERROR"):
        super().__init__(message)
        self.message = message
        self.code = code


class ConfigurationError(ESTDException):
    """Raised when environment or application configuration is invalid or missing."""

    def __init__(self, message: str):
        super().__init__(message=message, code="CONFIGURATION_ERROR")


class InvalidCategoryError(ESTDException):
    """Raised when an unsupported category is requested."""

    def __init__(self, category: str):
        super().__init__(
            message=f"Category '{category}' is not supported.",
            code="INVALID_CATEGORY",
        )


class InvalidSubcategoryError(ESTDException):
    """Raised when an unsupported subcategory or mismatched parent category is provided."""

    def __init__(self, subcategory: str, category: Optional[str] = None):
        detail = f"Subcategory '{subcategory}' is not valid"
        if category:
            detail += f" for parent category '{category}'"
        detail += "."
        super().__init__(
            message=detail,
            code="INVALID_SUBCATEGORY",
        )


class ExternalAPIError(ESTDException):
    """Base exception for external news provider errors."""

    def __init__(
        self,
        provider: str,
        message: str = "External API call failed.",
        code: str = "EXTERNAL_API_ERROR",
        status_code: Optional[int] = None,
    ):
        super().__init__(message=message, code=code)
        self.provider = provider
        self.status_code = status_code


class ProviderAuthenticationError(ExternalAPIError):
    """Raised when an external API rejects the API key (401/403)."""

    def __init__(self, provider: str, message: str = "Authentication failed with news provider."):
        super().__init__(
            provider=provider,
            message=message,
            code="PROVIDER_AUTH_ERROR",
            status_code=401,
        )


class ProviderRateLimitError(ExternalAPIError):
    """Raised when an external API rate limit is exceeded (429)."""

    def __init__(
        self,
        provider: str,
        retry_after: Optional[int] = None,
        message: str = "Rate limit exceeded for news provider. Please try again later.",
    ):
        super().__init__(
            provider=provider,
            message=message,
            code="RATE_LIMIT_EXCEEDED",
            status_code=429,
        )
        self.retry_after = retry_after


class ProviderTimeoutError(ExternalAPIError):
    """Raised when an external API request times out."""

    def __init__(self, provider: str, message: str = "Connection to news provider timed out."):
        super().__init__(
            provider=provider,
            message=message,
            code="PROVIDER_TIMEOUT",
            status_code=504,
        )


class ProviderConnectionError(ExternalAPIError):
    """Raised when network connection to an external API fails."""

    def __init__(self, provider: str, message: str = "Network error connecting to news provider."):
        super().__init__(
            provider=provider,
            message=message,
            code="PROVIDER_CONNECTION_ERROR",
            status_code=502,
        )


class ProviderServerError(ExternalAPIError):
    """Raised when an external API responds with a 5xx error."""

    def __init__(
        self,
        provider: str,
        status_code: int = 500,
        message: str = "News provider server returned an error.",
    ):
        super().__init__(
            provider=provider,
            message=message,
            code="PROVIDER_SERVER_ERROR",
            status_code=status_code,
        )


class ProviderResponseError(ExternalAPIError):
    """Raised when external API returns unexpected, malformed, or unparseable response."""

    def __init__(self, provider: str, message: str = "Malformed or unexpected response from news provider."):
        super().__init__(
            provider=provider,
            message=message,
            code="PROVIDER_RESPONSE_ERROR",
            status_code=502,
        )


# ============================================================================
# RSS Domain Exceptions
# ============================================================================

class RSSException(ESTDException):
    """Base exception for all RSS feed collection errors."""

    def __init__(self, message: str, code: str = "RSS_ERROR"):
        super().__init__(message=message, code=code)


class RSSSourceNotFoundError(RSSException):
    """Raised when an RSS source is not found in the registry."""

    def __init__(self, source_id: str):
        super().__init__(
            message=f"RSS source '{source_id}' was not found in registry.",
            code="RSS_SOURCE_NOT_FOUND",
        )


class RSSFetchError(RSSException):
    """Raised when an RSS feed cannot be fetched from its URL."""

    def __init__(self, source_id: str, message: str = "Failed to fetch RSS feed."):
        super().__init__(
            message=f"[{source_id}] {message}",
            code="RSS_FETCH_FAILED",
        )


class RSSTimeoutError(RSSException):
    """Raised when an RSS feed request times out."""

    def __init__(self, source_id: str, timeout_seconds: float):
        super().__init__(
            message=f"[{source_id}] RSS feed request timed out after {timeout_seconds}s.",
            code="RSS_TIMEOUT",
        )


class RSSInvalidFeedError(RSSException):
    """Raised when content is not a valid RSS/Atom feed."""

    def __init__(self, source_id: str, message: str = "Invalid RSS or Atom feed structure."):
        super().__init__(
            message=f"[{source_id}] {message}",
            code="RSS_INVALID_FEED",
        )


class RSSParseError(RSSException):
    """Raised when parsing feed content fails."""

    def __init__(self, source_id: str, message: str = "Failed to parse RSS feed entries."):
        super().__init__(
            message=f"[{source_id}] {message}",
            code="RSS_PARSE_ERROR",
        )


class RSSEmptyFeedError(RSSException):
    """Raised when an RSS feed contains zero entries."""

    def __init__(self, source_id: str):
        super().__init__(
            message=f"[{source_id}] RSS feed contains no articles/entries.",
            code="RSS_EMPTY_FEED",
        )

