"""Exception hierarchy for Step 8 Google Drive and Google Docs output pipeline."""
from typing import Optional


class Step8Exception(Exception):
    """Base exception for all Step 8 errors."""

    def __init__(self, message: str, code: str = "STEP8_ERROR", details: Optional[dict] = None):
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}


class Step8ValidationError(Step8Exception):
    """Raised when an article payload fails Step 8 eligibility or schema validation."""

    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(message, code="STEP8_VALIDATION_ERROR", details=details)


class InvalidStep8CategoryError(Step8ValidationError):
    """Raised when an article category does not match the 5 finalized ESTD categories."""

    def __init__(self, category: str):
        super().__init__(
            f"Invalid category '{category}'. Must be one of the 5 finalized ESTD categories: "
            "Artificial Intelligence, Technology, Business, Education, Science.",
            details={"invalid_category": category},
        )


class ArticleIneligibleForOutputError(Step8ValidationError):
    """Raised when an article lacks required content or approval to proceed to Google Docs."""

    def __init__(self, reason: str, article_id: Optional[int] = None):
        super().__init__(
            f"Article {article_id or ''} is ineligible for Google Docs output: {reason}",
            details={"article_id": article_id, "reason": reason},
        )


class DuplicateDocumentError(Step8Exception):
    """Raised when an attempt is made to duplicate an already existing Google Document."""

    def __init__(self, article_id: int, google_document_id: str):
        super().__init__(
            f"Article {article_id} already has a created Google Document (ID: {google_document_id}).",
            code="DUPLICATE_DOCUMENT_ERROR",
            details={"article_id": article_id, "google_document_id": google_document_id},
        )


class GoogleDriveAPIError(Step8Exception):
    """Raised when a Google Drive API request fails or returns an error."""

    def __init__(self, operation: str, error_message: str, status_code: Optional[int] = None):
        super().__init__(
            f"Google Drive operation '{operation}' failed: {error_message}",
            code="GDRIVE_API_ERROR",
            details={"operation": operation, "status_code": status_code, "error": error_message},
        )


class FolderInitializationError(Step8Exception):
    """Raised when folder hierarchy creation or resolution fails."""

    def __init__(self, message: str, folder_name: Optional[str] = None):
        super().__init__(
            f"Failed to initialize folder '{folder_name or 'hierarchy'}': {message}",
            code="FOLDER_INIT_ERROR",
            details={"folder_name": folder_name},
        )


class DocumentCreationError(Step8Exception):
    """Raised when Google Document creation fails."""

    def __init__(self, message: str, article_id: Optional[int] = None):
        super().__init__(
            f"Failed creating Google Document for article {article_id or ''}: {message}",
            code="DOCUMENT_CREATION_ERROR",
            details={"article_id": article_id},
        )


class DocumentRecordNotFoundError(Step8Exception):
    """Raised when looking for a document reference record that does not exist."""

    def __init__(self, article_id: int):
        super().__init__(
            f"No Google Document record found for article ID {article_id}.",
            code="DOCUMENT_RECORD_NOT_FOUND",
            details={"article_id": article_id},
        )
