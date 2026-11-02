"""Custom exceptions for Step 5 Knowledge Source."""
from typing import Optional

from backend.common.exceptions.custom_exceptions import ESTDException


class KnowledgeSourceException(ESTDException):
    """Base exception for all Step 5 Knowledge Source errors."""

    def __init__(self, message: str, code: str = "KNOWLEDGE_SOURCE_ERROR", status_code: int = 500):
        super().__init__(message=message, code=code)
        self.status_code = status_code


class ArticleNotFoundError(KnowledgeSourceException):
    """Raised when an article cannot be found in the knowledge source."""

    def __init__(self, article_id: int):
        super().__init__(
            message=f"Article with ID {article_id} not found in knowledge source.",
            code="ARTICLE_NOT_FOUND",
            status_code=404,
        )
        self.article_id = article_id


class ArticleDuplicateError(KnowledgeSourceException):
    """Raised when attempting to persist an article that already exists in the knowledge source."""

    def __init__(self, reason: str, identifier: str):
        super().__init__(
            message=f"Cannot persist duplicate article. Duplicate detected by {reason}: '{identifier}'",
            code="DUPLICATE_ARTICLE",
            status_code=409,
        )
        self.reason = reason
        self.identifier = identifier


class InvalidArticleDataError(KnowledgeSourceException):
    """Raised when article data fails validation before persistence."""

    def __init__(self, message: str):
        super().__init__(
            message=message,
            code="INVALID_ARTICLE_DATA",
            status_code=400,
        )


class DatabaseConnectionError(KnowledgeSourceException):
    """Raised when a database connectivity or health check operation fails."""

    def __init__(self, message: str):
        super().__init__(
            message=message,
            code="DATABASE_ERROR",
            status_code=500,
        )


class CategoryNotFoundError(KnowledgeSourceException):
    """Raised when a referenced category does not exist in the database."""

    def __init__(self, category_name: str):
        super().__init__(
            message=f"Category '{category_name}' not found in canonical reference table.",
            code="CATEGORY_NOT_FOUND",
            status_code=404,
        )
