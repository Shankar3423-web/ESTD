"""SQLAlchemy ORM model for Step 4 duplicate index records."""
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    Index,
    Integer,
    String,
    Text,
)

from backend.database.connection.session import Base


class DuplicateIndexRecord(Base):
    """Historical duplicate index record for ESTD article deduplication."""

    __tablename__ = "estd_duplicate_index"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    
    # Article metadata
    article_id = Column(String(255), nullable=True, index=True, doc="Optional external or pipeline article ID")
    title = Column(Text, nullable=False, doc="Title of the article")
    url = Column(Text, nullable=False, doc="Original article URL")
    normalized_url = Column(String(1024), nullable=False, index=True, doc="Normalized canonical URL")
    content_hash = Column(String(64), nullable=False, index=True, doc="SHA-256 fingerprint of normalized body")
    category = Column(String(100), nullable=False, index=True, doc="ESTD category (e.g. Technology, AI)")
    subcategory = Column(String(100), nullable=True, index=True, doc="ESTD subcategory if classified")
    source_name = Column(String(255), nullable=True, doc="Publisher or feed source name")
    source_type = Column(String(100), nullable=False, doc="Provider type (gnews, newsdata, rss)")
    author = Column(String(255), nullable=True, doc="Author if known")
    published_at = Column(String(100), nullable=True, doc="ISO 8601 publication timestamp")
    
    # Content representation for similarity candidate matching
    content_preview = Column(Text, nullable=True, doc="First 500 characters of cleaned content")
    cleaned_content = Column(Text, nullable=True, doc="Full cleaned content for similarity comparison")
    
    # Deduplication decision traceability
    is_duplicate = Column(Boolean, default=False, nullable=False, index=True, doc="True if marked as duplicate")
    duplicate_reason = Column(String(50), nullable=True, doc="URL_MATCH, EXACT_CONTENT, SIMILARITY")
    matched_record_id = Column(Integer, nullable=True, doc="Reference to the matched record ID if duplicate")
    similarity_score = Column(Float, nullable=True, doc="Cosine similarity score if matched via similarity")
    
    # Audit timestamps
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
        doc="UTC timestamp when record was indexed in Step 4",
    )

    __table_args__ = (
        Index("ix_estd_dup_url_hash", "normalized_url", "content_hash"),
        Index("ix_estd_dup_cat_created", "category", "created_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<DuplicateIndexRecord(id={self.id}, title='{self.title[:30]}...', "
            f"category='{self.category}', is_duplicate={self.is_duplicate}, "
            f"reason='{self.duplicate_reason}')>"
        )
