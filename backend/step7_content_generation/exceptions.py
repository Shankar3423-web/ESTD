"""Domain exceptions for Step 7 Gemini AI Content Generation layer."""
from typing import Optional

from backend.common.exceptions.custom_exceptions import ESTDException


class GenerationException(ESTDException):
    """Base exception for all Step 7 content generation errors."""

    def __init__(self, message: str, code: str = "GENERATION_ERROR"):
        super().__init__(message=message, code=code)


class GeminiConfigurationError(GenerationException):
    """Raised when Gemini API configuration is missing or invalid."""

    def __init__(self, message: str = "Gemini API configuration is missing or invalid."):
        super().__init__(message=message, code="GEMINI_CONFIGURATION_ERROR")


class GeminiAuthenticationError(GenerationException):
    """Raised when Gemini API key or credentials are rejected."""

    def __init__(self, message: str = "Gemini API authentication failed."):
        super().__init__(message=message, code="GEMINI_AUTHENTICATION_ERROR")


class GeminiConnectionError(GenerationException):
    """Raised when connection to Gemini API fails or cannot be established."""

    def __init__(self, message: str = "Failed to connect to Gemini API."):
        super().__init__(message=message, code="GEMINI_CONNECTION_ERROR")


class GeminiTimeoutError(GenerationException):
    """Raised when a Gemini API request exceeds the configured timeout."""

    def __init__(self, timeout_seconds: float):
        super().__init__(
            message=f"Gemini API request timed out after {timeout_seconds:.1f}s.",
            code="GEMINI_TIMEOUT_ERROR",
        )
        self.timeout_seconds = timeout_seconds


class GeminiRateLimitError(GenerationException):
    """Raised when Gemini API rate limit or quota is exceeded."""

    def __init__(self, message: str = "Gemini API rate limit exceeded.", retry_after: Optional[float] = None):
        super().__init__(message=message, code="GEMINI_RATE_LIMIT_ERROR")
        self.retry_after = retry_after


class GeminiModelError(GenerationException):
    """Raised when the specified Gemini model is unavailable or invalid."""

    def __init__(self, model_name: str, message: str = "Model is unavailable or invalid."):
        super().__init__(
            message=f"Gemini model '{model_name}' error: {message}",
            code="GEMINI_MODEL_ERROR",
        )
        self.model_name = model_name


class GenerationValidationError(GenerationException):
    """Raised when generated AI content fails validation checks."""

    def __init__(self, message: str = "Generated content failed validation."):
        super().__init__(message=message, code="GENERATION_VALIDATION_ERROR")


class ArticleIneligibleError(GenerationException):
    """Raised when an article cannot be processed for content generation."""

    def __init__(self, article_id: int, reason: str, code: str = "ARTICLE_INELIGIBLE_FOR_GENERATION"):
        super().__init__(
            message=f"Article ID {article_id} is ineligible for generation: {reason}",
            code=code,
        )
        self.article_id = article_id
        self.reason = reason


class InsufficientSourceContentError(ArticleIneligibleError):
    """Raised when source content is insufficient or a mere snippet incapable of supporting full publication."""

    def __init__(self, article_id: int, reason: str):
        super().__init__(
            article_id=article_id,
            reason=reason,
            code="INSUFFICIENT_SOURCE_CONTENT",
        )


class GenerationExecutionError(GenerationException):
    """Raised when content generation pipeline execution fails."""

    def __init__(self, message: str):
        super().__init__(message=message, code="GENERATION_EXECUTION_ERROR")
