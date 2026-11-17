"""SQLAlchemy ORM model for Plan C Daily Category Digest records."""
from datetime import date, datetime, timezone
from enum import Enum
from typing import Optional

from sqlalchemy import (
    BigInteger,
    Column,
    Date,
    DateTime,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)

from backend.database.connection.session import Base


class DigestStatus(str, Enum):
    """Lifecycle statuses for daily category digest exports."""
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    EMPTY = "EMPTY"


class DailyDigestRecord(Base):
    """Tracks compiled end-of-day category digests exported to Google Drive."""

    __tablename__ = "daily_digest_records"

    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)

    # Date and Category identifier
    digest_date = Column(
        Date,
        nullable=False,
        index=True,
        doc="Calendar date represented by this daily digest",
    )
    category = Column(
        String(100),
        nullable=False,
        index=True,
        doc="Canonical category name (e.g. Tech, Sports, Entertainment)",
    )

    # Aggregation Metrics
    article_count = Column(
        Integer,
        nullable=False,
        default=0,
        doc="Number of articles compiled into this daily digest",
    )

    # Google Drive Export Linkage
    google_document_id = Column(
        String(255),
        nullable=True,
        index=True,
        doc="Google Document file ID in Google Drive",
    )
    google_document_url = Column(
        Text,
        nullable=True,
        doc="Web edit/view link for the created Google Document",
    )
    google_drive_folder_id = Column(
        String(255),
        nullable=True,
        doc="Google Drive category folder ID where doc was placed",
    )

    # Lifecycle Status & Error Logging
    status = Column(
        String(50),
        nullable=False,
        default=DigestStatus.PENDING.value,
        index=True,
        doc="Processing status: PENDING, COMPLETED, FAILED, EMPTY",
    )
    error_message = Column(
        Text,
        nullable=True,
        doc="Error message or exception details if generation failed",
    )

    # Audit Timestamps
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
        doc="UTC timestamp when digest record was initiated",
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
        doc="UTC timestamp of last status or link update",
    )

    __table_args__ = (
        UniqueConstraint("digest_date", "category", name="uq_daily_digest_date_category"),
        Index("ix_daily_digest_date_cat", "digest_date", "category"),
    )

    def __repr__(self) -> str:
        return (
            f"<DailyDigestRecord(id={self.id}, date={self.digest_date}, "
            f"category='{self.category}', count={self.article_count}, status='{self.status}')>"
        )

