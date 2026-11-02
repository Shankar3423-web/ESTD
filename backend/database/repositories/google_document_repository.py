"""Repository for GoogleDocumentRecord database operations."""
from datetime import datetime, timezone
from typing import List, Optional, Tuple

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.common.logging.logger import logger
from backend.database.models.google_document_record import DocumentStatus, GoogleDocumentRecord


class GoogleDocumentRepository:
    """Provides database operations for tracking Step 8 Google Document status and references."""

    @staticmethod
    def get_by_article_id(session: Session, article_id: int) -> Optional[GoogleDocumentRecord]:
        """Fetch record by associated news article ID."""
        stmt = select(GoogleDocumentRecord).where(GoogleDocumentRecord.article_id == article_id)
        return session.execute(stmt).scalar_one_or_none()

    @staticmethod
    def get_by_document_id(session: Session, doc_id: str) -> Optional[GoogleDocumentRecord]:
        """Fetch record by assigned Google Document ID."""
        stmt = select(GoogleDocumentRecord).where(GoogleDocumentRecord.google_document_id == doc_id)
        return session.execute(stmt).scalar_one_or_none()

    @staticmethod
    def get_by_id(session: Session, record_id: int) -> Optional[GoogleDocumentRecord]:
        """Fetch record by primary key ID."""
        stmt = select(GoogleDocumentRecord).where(GoogleDocumentRecord.id == record_id)
        return session.execute(stmt).scalar_one_or_none()

    @staticmethod
    def create_or_get_pending(
        session: Session,
        article_id: int,
        category: str,
        document_title: str,
        subcategory: Optional[str] = None,
        root_folder_id: Optional[str] = None,
        category_folder_id: Optional[str] = None,
        subcategory_folder_id: Optional[str] = None,
    ) -> Tuple[GoogleDocumentRecord, bool]:
        """Atomically create a PENDING record or retrieve an existing one.

        Returns:
            Tuple of (record, is_newly_created).
        """
        existing = GoogleDocumentRepository.get_by_article_id(session, article_id)
        if existing:
            return existing, False

        record = GoogleDocumentRecord(
            article_id=article_id,
            category=category,
            subcategory=subcategory,
            document_title=document_title,
            google_drive_root_folder_id=root_folder_id,
            google_drive_category_folder_id=category_folder_id,
            google_drive_subcategory_folder_id=subcategory_folder_id,
            status=DocumentStatus.PENDING.value,
            attempt_count=1,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        try:
            session.add(record)
            session.flush()
            return record, True
        except IntegrityError:
            session.rollback()
            existing = GoogleDocumentRepository.get_by_article_id(session, article_id)
            if existing:
                return existing, False
            raise

    @staticmethod
    def mark_created(
        session: Session,
        record_id: int,
        google_document_id: str,
        google_document_url: Optional[str] = None,
        root_folder_id: Optional[str] = None,
        category_folder_id: Optional[str] = None,
        subcategory_folder_id: Optional[str] = None,
        subcategory: Optional[str] = None,
    ) -> GoogleDocumentRecord:
        """Update record to CREATED status upon successful Google Drive upload."""
        record = GoogleDocumentRepository.get_by_id(session, record_id)
        if not record:
            raise ValueError(f"GoogleDocumentRecord with ID {record_id} not found.")

        now = datetime.now(timezone.utc)
        record.google_document_id = google_document_id
        record.google_document_url = google_document_url
        if root_folder_id:
            record.google_drive_root_folder_id = root_folder_id
        if category_folder_id:
            record.google_drive_category_folder_id = category_folder_id
        if subcategory_folder_id:
            record.google_drive_subcategory_folder_id = subcategory_folder_id
        if subcategory:
            record.subcategory = subcategory
        record.status = DocumentStatus.CREATED.value
        record.last_error = None
        record.completed_at = now
        record.updated_at = now
        session.flush()
        return record

    @staticmethod
    def mark_failed(
        session: Session,
        record_id: int,
        error_message: str,
    ) -> GoogleDocumentRecord:
        """Update record to FAILED status and store diagnostic error message."""
        record = GoogleDocumentRepository.get_by_id(session, record_id)
        if not record:
            raise ValueError(f"GoogleDocumentRecord with ID {record_id} not found.")

        now = datetime.now(timezone.utc)
        record.status = DocumentStatus.FAILED.value
        record.last_error = error_message[:2000] if error_message else "Unknown error"
        record.updated_at = now
        session.flush()
        return record

    @staticmethod
    def increment_attempt(
        session: Session,
        record_id: int,
    ) -> GoogleDocumentRecord:
        """Increment execution attempt count for retry operations."""
        record = GoogleDocumentRepository.get_by_id(session, record_id)
        if not record:
            raise ValueError(f"GoogleDocumentRecord with ID {record_id} not found.")

        record.attempt_count += 1
        record.updated_at = datetime.now(timezone.utc)
        session.flush()
        return record

    @staticmethod
    def list_records(
        session: Session,
        category: Optional[str] = None,
        subcategory: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[GoogleDocumentRecord]:
        """List records with optional category, subcategory, and status filtering."""
        stmt = select(GoogleDocumentRecord)
        if category:
            stmt = stmt.where(GoogleDocumentRecord.category == category)
        if subcategory:
            stmt = stmt.where(GoogleDocumentRecord.subcategory == subcategory)
        if status:
            stmt = stmt.where(GoogleDocumentRecord.status == status)
        stmt = stmt.order_by(GoogleDocumentRecord.created_at.desc()).limit(limit).offset(offset)
        return list(session.execute(stmt).scalars().all())
