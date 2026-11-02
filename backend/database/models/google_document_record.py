"""SQLAlchemy ORM model for Step 8 Google Document persistence and traceability."""
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from backend.database.connection.session import Base


class DocumentStatus(str, Enum):
    """Lifecycle statuses for Step 8 Google Document creation."""
    PENDING = "PENDING"
    CREATED = "CREATED"
    FAILED = "FAILED"


class GoogleDocumentRecord(Base):
    """Persistence record linking an ESTD NewsArticle to its output Google Document in Google Drive."""

    __tablename__ = "google_document_records"

    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)

    # Relational link to the knowledge source NewsArticle (idempotency anchor)
    article_id = Column(
        BigInteger,
        ForeignKey("news_articles.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
        doc="Reference to the underlying knowledge base article",
    )

    # Google Drive / Docs artifact metadata
    google_document_id = Column(
        String(255),
        nullable=True,
        index=True,
        doc="Google Document ID assigned by Google Drive API",
    )
    google_document_url = Column(
        Text,
        nullable=True,
        doc="Web URL for viewing and editing the Google Document",
    )
    google_drive_root_folder_id = Column(
        String(255),
        nullable=True,
        doc="Drive folder ID of the ESTD CONTENT root directory",
    )
    google_drive_category_folder_id = Column(
        String(255),
        nullable=True,
        doc="Drive folder ID of the category subfolder",
    )
    google_drive_subcategory_folder_id = Column(
        String(255),
        nullable=True,
        doc="Drive folder ID of the subcategory folder if classified",
    )

    # Document details & routing
    category = Column(
        String(100),
        nullable=False,
        index=True,
        doc="ESTD category under which the document is classified",
    )
    subcategory = Column(
        String(100),
        nullable=True,
        index=True,
        doc="ESTD subcategory under which the document is classified",
    )
    document_title = Column(
        Text,
        nullable=False,
        doc="Deterministic title given to the Google Document",
    )

    # Execution state & error handling
    status = Column(
        String(50),
        nullable=False,
        default=DocumentStatus.PENDING.value,
        index=True,
        doc="Processing status: PENDING, CREATED, or FAILED",
    )
    attempt_count = Column(
        Integer,
        nullable=False,
        default=0,
        doc="Number of creation/upload attempts performed",
    )
    last_error = Column(
        Text,
        nullable=True,
        doc="Diagnostic message recorded if document generation encountered an error",
    )

    # Audit timestamps
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
        doc="UTC timestamp when record was initialized",
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
        doc="UTC timestamp of last status update",
    )
    completed_at = Column(
        DateTime(timezone=True),
        nullable=True,
        doc="UTC timestamp when document was successfully created",
    )

    # Relationship back to NewsArticle
    article = relationship("NewsArticle", backref="google_document_record")

    __table_args__ = (
        CheckConstraint("length(trim(document_title)) > 0", name="ck_google_doc_title_not_empty"),
        CheckConstraint(
            "status IN ('PENDING', 'CREATED', 'FAILED')",
            name="ck_google_doc_valid_status",
        ),
        Index("ix_google_doc_cat_status", "category", "status"),
        Index("ix_google_doc_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<GoogleDocumentRecord(id={self.id}, article_id={self.article_id}, "
            f"doc_id='{self.google_document_id}', status='{self.status}', category='{self.category}')>"
        )
