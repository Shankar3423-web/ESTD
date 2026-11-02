"""Domain models and enums for Step 4 duplicate detection decisions and traceability."""
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field

from backend.common.utils.datetime_utils import get_utc_now_iso


class DuplicateStatus(str, Enum):
    """Primary classification status for Step 4 deduplication."""

    UNIQUE = "UNIQUE"
    DUPLICATE = "DUPLICATE"


class DuplicateReason(str, Enum):
    """Reason code explaining how duplicate classification occurred."""

    URL_MATCH = "URL_MATCH"
    EXACT_CONTENT = "EXACT_CONTENT"
    SIMILARITY = "SIMILARITY"


class DetectionScope(str, Enum):
    """Origin of the matching duplicate."""

    BATCH = "BATCH"
    HISTORICAL = "HISTORICAL"


class DuplicateDecision(BaseModel):
    """Audit and decision outcome for a single article evaluation in Step 4."""

    status: DuplicateStatus = Field(
        ...,
        description="Outcome classification: UNIQUE or DUPLICATE.",
    )
    is_duplicate: bool = Field(
        ...,
        description="Convenience boolean flag: True if DUPLICATE, False if UNIQUE.",
    )
    duplicate_reason: Optional[DuplicateReason] = Field(
        default=None,
        description="Reason code: URL_MATCH, EXACT_CONTENT, or SIMILARITY; None if UNIQUE.",
    )
    detection_scope: Optional[DetectionScope] = Field(
        default=None,
        description="Scope where match was detected: BATCH or HISTORICAL; None if UNIQUE.",
    )
    matched_article_id: Optional[str] = Field(
        default=None,
        description="ID of the matching article if duplicate; None if UNIQUE.",
    )
    matched_article_title: Optional[str] = Field(
        default=None,
        description="Title of the matching article if duplicate; None if UNIQUE.",
    )
    matched_article_url: Optional[str] = Field(
        default=None,
        description="URL of the matching article if duplicate; None if UNIQUE.",
    )
    similarity_score: Optional[float] = Field(
        default=None,
        description="Computed cosine similarity score (0.0 to 1.0) if checked; None if exact match or UNIQUE.",
    )
    confidence: float = Field(
        default=1.0,
        description="Confidence score of the decision (1.0 for deterministic URL/hash matches, similarity score for vector matches).",
    )
    normalized_url: str = Field(
        ...,
        description="Canonical normalized URL used for matching.",
    )
    content_hash: str = Field(
        ...,
        description="SHA-256 fingerprint hex digest of the normalized content.",
    )
    evaluated_at: str = Field(
        default_factory=get_utc_now_iso,
        description="ISO 8601 UTC timestamp of when deduplication evaluation was executed.",
    )

    model_config = {
        "extra": "ignore",
        "json_schema_extra": {
            "example": {
                "status": "DUPLICATE",
                "is_duplicate": True,
                "duplicate_reason": "SIMILARITY",
                "detection_scope": "HISTORICAL",
                "matched_article_id": "42",
                "matched_article_title": "OpenAI announces reasoning model",
                "matched_article_url": "https://techcrunch.com/2026/09/30/openai-model",
                "similarity_score": 0.9125,
                "confidence": 0.9125,
                "normalized_url": "https://example.com/openai-model",
                "content_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                "evaluated_at": "2026-10-01T15:00:00Z",
            }
        },
    }

    @classmethod
    def unique(
        cls,
        normalized_url: str,
        content_hash: str,
        similarity_score: Optional[float] = None,
    ) -> "DuplicateDecision":
        """Factory for a confirmed UNIQUE article."""
        return cls(
            status=DuplicateStatus.UNIQUE,
            is_duplicate=False,
            duplicate_reason=None,
            detection_scope=None,
            matched_article_id=None,
            matched_article_title=None,
            matched_article_url=None,
            similarity_score=similarity_score,
            confidence=1.0,
            normalized_url=normalized_url,
            content_hash=content_hash,
            evaluated_at=get_utc_now_iso(),
        )

    @classmethod
    def duplicate_by_url(
        cls,
        normalized_url: str,
        content_hash: str,
        scope: DetectionScope,
        matched_id: Optional[str] = None,
        matched_title: Optional[str] = None,
        matched_url: Optional[str] = None,
    ) -> "DuplicateDecision":
        """Factory for a DUPLICATE identified via normalized URL matching."""
        return cls(
            status=DuplicateStatus.DUPLICATE,
            is_duplicate=True,
            duplicate_reason=DuplicateReason.URL_MATCH,
            detection_scope=scope,
            matched_article_id=str(matched_id) if matched_id is not None else None,
            matched_article_title=matched_title,
            matched_article_url=matched_url,
            similarity_score=None,
            confidence=1.0,
            normalized_url=normalized_url,
            content_hash=content_hash,
            evaluated_at=get_utc_now_iso(),
        )

    @classmethod
    def duplicate_by_exact_content(
        cls,
        normalized_url: str,
        content_hash: str,
        scope: DetectionScope,
        matched_id: Optional[str] = None,
        matched_title: Optional[str] = None,
        matched_url: Optional[str] = None,
    ) -> "DuplicateDecision":
        """Factory for a DUPLICATE identified via exact SHA-256 content fingerprint match."""
        return cls(
            status=DuplicateStatus.DUPLICATE,
            is_duplicate=True,
            duplicate_reason=DuplicateReason.EXACT_CONTENT,
            detection_scope=scope,
            matched_article_id=str(matched_id) if matched_id is not None else None,
            matched_article_title=matched_title,
            matched_article_url=matched_url,
            similarity_score=None,
            confidence=1.0,
            normalized_url=normalized_url,
            content_hash=content_hash,
            evaluated_at=get_utc_now_iso(),
        )

    @classmethod
    def duplicate_by_similarity(
        cls,
        normalized_url: str,
        content_hash: str,
        scope: DetectionScope,
        similarity_score: float,
        matched_id: Optional[str] = None,
        matched_title: Optional[str] = None,
        matched_url: Optional[str] = None,
    ) -> "DuplicateDecision":
        """Factory for a DUPLICATE identified via TF-IDF cosine similarity."""
        return cls(
            status=DuplicateStatus.DUPLICATE,
            is_duplicate=True,
            duplicate_reason=DuplicateReason.SIMILARITY,
            detection_scope=scope,
            matched_article_id=str(matched_id) if matched_id is not None else None,
            matched_article_title=matched_title,
            matched_article_url=matched_url,
            similarity_score=similarity_score,
            confidence=similarity_score,
            normalized_url=normalized_url,
            content_hash=content_hash,
            evaluated_at=get_utc_now_iso(),
        )
