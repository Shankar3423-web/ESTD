"""Step 4 domain exceptions for duplicate detection and deduplication."""
from typing import Optional

from backend.common.exceptions.custom_exceptions import ESTDException


class DuplicateDetectionException(ESTDException):
    """Base exception for all Step 4 Duplicate Detection errors."""

    def __init__(self, message: str, code: str = "DUPLICATE_DETECTION_ERROR"):
        super().__init__(message=message, code=code)


class InvalidArticleForDeduplicationError(DuplicateDetectionException):
    """Raised when an article cannot be evaluated due to missing mandatory identifiers or content."""

    def __init__(self, url: Optional[str] = None, reason: str = "Article is missing required fields for deduplication."):
        prefix = f"[{url}] " if url else ""
        super().__init__(
            message=f"{prefix}Invalid article for deduplication: {reason}",
            code="INVALID_ARTICLE_FOR_DEDUPLICATION",
        )
        self.url = url


class SimilarityCalculationError(DuplicateDetectionException):
    """Raised when similarity vectorization or computation fails unexpectedly."""

    def __init__(self, reason: str = "Failed to calculate TF-IDF or cosine similarity."):
        super().__init__(
            message=f"Similarity calculation failed: {reason}",
            code="SIMILARITY_CALCULATION_ERROR",
        )


class DuplicateIndexDatabaseError(DuplicateDetectionException):
    """Raised when historical database lookup or record persistence fails."""

    def __init__(self, reason: str = "Database operation in duplicate index failed."):
        super().__init__(
            message=f"Duplicate index database error: {reason}",
            code="DUPLICATE_INDEX_DB_ERROR",
        )


class DuplicateConfigurationError(DuplicateDetectionException):
    """Raised when duplicate detection configuration parameters are invalid."""

    def __init__(self, reason: str = "Invalid duplicate detection configuration."):
        super().__init__(
            message=f"Duplicate detection configuration error: {reason}",
            code="DUPLICATE_CONFIG_ERROR",
        )
