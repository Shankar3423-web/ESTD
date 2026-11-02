"""Step 3 domain exceptions for content cleaning and normalization."""
from typing import Optional
from backend.common.exceptions.custom_exceptions import ESTDException


class CleaningException(ESTDException):
    """Base exception for all Step 3 Content Cleaning errors."""

    def __init__(self, message: str, code: str = "CLEANING_ERROR"):
        super().__init__(message=message, code=code)


class InvalidArticleContentError(CleaningException):
    """Raised when an article content is missing, null, or has an invalid type."""

    def __init__(self, url: str, reason: str = "Article content is invalid or missing."):
        super().__init__(
            message=f"[{url}] Invalid article content: {reason}",
            code="INVALID_ARTICLE_CONTENT",
        )
        self.url = url


class ContentCleaningFailedError(CleaningException):
    """Raised when content cleaning fails or reduces article content below acceptable thresholds."""

    def __init__(self, url: str, reason: str = "Failed to produce meaningful cleaned content."):
        super().__init__(
            message=f"[{url}] Cleaning failed: {reason}",
            code="CLEANING_FAILED",
        )
        self.url = url


class CleaningValidationError(CleaningException):
    """Raised when post-cleaning validation of the article fails."""

    def __init__(self, url: str, reason: str = "Post-cleaning validation failed."):
        super().__init__(
            message=f"[{url}] Validation error: {reason}",
            code="CLEANING_VALIDATION_ERROR",
        )
        self.url = url
