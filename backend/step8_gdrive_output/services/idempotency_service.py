"""Idempotency service guaranteeing duplicate-document protection and retry reconciliation."""
from typing import Optional, Tuple

from sqlalchemy.orm import Session

from backend.common.logging.logger import logger
from backend.database.models.google_document_record import DocumentStatus, GoogleDocumentRecord
from backend.database.repositories.google_document_repository import GoogleDocumentRepository


class DocumentIdempotencyService:
    """Enforces duplicate document protection, concurrency safety, and retry tracking."""

    @staticmethod
    def get_existing_created_document(
        session: Session,
        article_id: int,
    ) -> Optional[GoogleDocumentRecord]:
        """Check if an article already has a successfully created Google Document.

        Returns:
            GoogleDocumentRecord if status is CREATED and google_document_id is present, else None.
        """
        record = GoogleDocumentRepository.get_by_article_id(session, article_id)
        if record and record.status == DocumentStatus.CREATED.value and record.google_document_id:
            logger.info(
                f"Idempotency hit: Article {article_id} already has Google Document {record.google_document_id}. Skipping upload."
            )
            return record
        return None

    @staticmethod
    def prepare_processing_record(
        session: Session,
        article_id: int,
        category: str,
        document_title: str,
        subcategory: Optional[str] = None,
        root_folder_id: Optional[str] = None,
        category_folder_id: Optional[str] = None,
        subcategory_folder_id: Optional[str] = None,
        force_recreate: bool = False,
    ) -> Tuple[GoogleDocumentRecord, bool]:
        """Atomically prepare or retrieve the persistence record for this article.

        Returns:
            Tuple of (record, should_create_document).
            should_create_document is False if a valid document already exists and force_recreate is False.
        """
        existing = GoogleDocumentRepository.get_by_article_id(session, article_id)

        if existing:
            # If already created and not forced to recreate, return existing record
            if existing.status == DocumentStatus.CREATED.value and existing.google_document_id and not force_recreate:
                return existing, False

            # If previous attempt failed or pending, update for retry
            existing.attempt_count += 1
            existing.status = DocumentStatus.PENDING.value
            existing.document_title = document_title
            existing.category = category
            if subcategory:
                existing.subcategory = subcategory
            if root_folder_id:
                existing.google_drive_root_folder_id = root_folder_id
            if category_folder_id:
                existing.google_drive_category_folder_id = category_folder_id
            if subcategory_folder_id:
                existing.google_drive_subcategory_folder_id = subcategory_folder_id
            session.flush()
            return existing, True

        # Create new pending record
        record, _ = GoogleDocumentRepository.create_or_get_pending(
            session=session,
            article_id=article_id,
            category=category,
            subcategory=subcategory,
            document_title=document_title,
            root_folder_id=root_folder_id,
            category_folder_id=category_folder_id,
            subcategory_folder_id=subcategory_folder_id,
        )
        return record, True
