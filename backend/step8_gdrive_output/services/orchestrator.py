"""Step 8 Master Orchestrator linking Step 7 validated content to Google Drive and Google Docs."""
import time
from typing import Optional

from sqlalchemy.orm import Session

from backend.common.logging.logger import logger
from backend.database.connection.session import get_db_session
from backend.database.models.google_document_record import DocumentStatus, GoogleDocumentRecord
from backend.database.models.news_article import NewsArticle
from backend.database.repositories.google_document_repository import GoogleDocumentRepository
from backend.step7_content_generation.schemas.generated_news import GeneratedNews
from backend.step8_gdrive_output.exceptions import (
    ArticleIneligibleForOutputError,
    DocumentCreationError,
    DocumentRecordNotFoundError,
    GoogleDriveAPIError,
    Step8Exception,
)
from backend.step8_gdrive_output.schemas.document_record import (
    Step8DocumentRecordSchema,
    Step8DocumentResponse,
)
from backend.step8_gdrive_output.services.document_formatter import DocumentFormatter
from backend.step8_gdrive_output.services.folder_resolver import DriveFolderResolver
from backend.step8_gdrive_output.services.gdrive_service import GoogleDriveService
from backend.step8_gdrive_output.services.idempotency_service import DocumentIdempotencyService
from backend.step8_gdrive_output.validators.eligibility_validator import (
    validate_category,
    validate_step8_eligibility,
)


class Step8Orchestrator:
    """Orchestrates validation, folder resolution, document creation, idempotency, and persistence."""

    def __init__(
        self,
        gdrive_service: Optional[GoogleDriveService] = None,
        folder_resolver: Optional[DriveFolderResolver] = None,
    ):
        self.gdrive_service = gdrive_service or GoogleDriveService()
        self.folder_resolver = folder_resolver or DriveFolderResolver(self.gdrive_service)

    def process_approved_content(
        self,
        news: GeneratedNews,
        article_id: int,
        session: Session,
        original_published_at: Optional[str] = None,
        force_recreate: bool = False,
    ) -> Step8DocumentResponse:
        """Process validated Step 7 GeneratedNews into a Google Document stored in the category folder.

        Guarantees:
        - Strict validation of inputs.
        - Strict idempotency (never creates duplicate documents for the same article_id).
        - Source traceability preserved.
        - Persistence of Google Document ID, URL, and folder references.
        """
        start_time = time.monotonic()

        # 1. Eligibility validation
        validate_step8_eligibility(news, article_id=article_id)
        canonical_category = validate_category(news.category)

        # 2. Document title and body formatting
        document_title = DocumentFormatter.sanitize_title(news.title, article_id=article_id)
        formatted_content = DocumentFormatter.format_document_content(
            news=news,
            article_id=article_id,
            original_published_at=original_published_at,
        )

        # 3. Idempotency Check & PENDING Record Creation
        root_folder_id = None
        category_folder_id = None
        subcategory_folder_id = None
        try:
            category_folder_id = self.folder_resolver.resolve_category_folder_id(canonical_category)
            root_folder_id = self.folder_resolver.get_root_folder_id()
            if getattr(news, "subcategory", None):
                subcategory_folder_id = self.folder_resolver.resolve_subcategory_folder_id(
                    canonical_category, news.subcategory
                )
        except Exception as exc:
            logger.error(f"Failed resolving folder for category '{canonical_category}': {exc}")
            # If folder resolution fails, we still record failure or raise
            raise

        record, should_create = DocumentIdempotencyService.prepare_processing_record(
            session=session,
            article_id=article_id,
            category=canonical_category,
            subcategory=getattr(news, "subcategory", None),
            document_title=document_title,
            root_folder_id=root_folder_id,
            category_folder_id=category_folder_id,
            subcategory_folder_id=subcategory_folder_id,
            force_recreate=force_recreate,
        )

        # If already created, return immediately (Idempotency protection)
        if not should_create and record.status == DocumentStatus.CREATED.value:
            exec_ms = (time.monotonic() - start_time) * 1000
            return Step8DocumentResponse(
                success=True,
                status=DocumentStatus.CREATED.value,
                article_id=article_id,
                data=Step8DocumentRecordSchema.model_validate(record),
                is_duplicate_prevented=True,
                processing_time_ms=round(exec_ms, 2),
            )

        # 4. Create Google Document in Google Drive
        try:
            target_folder_id = subcategory_folder_id or category_folder_id
            target_label = f"subcategory '{news.subcategory}' ({subcategory_folder_id})" if subcategory_folder_id else f"category '{canonical_category}' ({category_folder_id})"
            logger.info(
                f"Uploading Google Document for article {article_id} ('{document_title}') "
                f"into {target_label}..."
            )
            doc_data = self.gdrive_service.create_google_document(
                title=document_title,
                content=formatted_content,
                folder_id=target_folder_id,
            )
            doc_id = doc_data["id"]
            doc_url = doc_data.get("webViewLink")

            # 5. Persist success state
            updated_record = GoogleDocumentRepository.mark_created(
                session=session,
                record_id=record.id,
                google_document_id=doc_id,
                google_document_url=doc_url,
                root_folder_id=root_folder_id,
                category_folder_id=category_folder_id,
                subcategory_folder_id=subcategory_folder_id,
                subcategory=getattr(news, "subcategory", None),
            )
            session.commit()

            exec_ms = (time.monotonic() - start_time) * 1000
            logger.info(
                f"Successfully created Google Document for article {article_id}: "
                f"ID={doc_id}, URL={doc_url}"
            )
            return Step8DocumentResponse(
                success=True,
                status=DocumentStatus.CREATED.value,
                article_id=article_id,
                data=Step8DocumentRecordSchema.model_validate(updated_record),
                is_duplicate_prevented=False,
                processing_time_ms=round(exec_ms, 2),
            )

        except Exception as exc:
            err_msg = str(exc)
            logger.error(f"Error creating Google Document for article {article_id}: {err_msg}")
            # Safely record failure state without losing article
            try:
                GoogleDocumentRepository.mark_failed(
                    session=session,
                    record_id=record.id,
                    error_message=err_msg,
                )
                session.commit()
            except Exception as persist_exc:
                logger.error(f"Failed to record failure status in database: {persist_exc}")

            exec_ms = (time.monotonic() - start_time) * 1000
            raise DocumentCreationError(
                f"Google Document upload failed: {err_msg}",
                article_id=article_id,
            )

    def process_article_by_id(
        self,
        article_id: int,
        session: Session,
        force_recreate: bool = False,
    ) -> Step8DocumentResponse:
        """Fetch article from PostgreSQL knowledge base, generate validated content (via Step 7), and output to Google Docs."""
        # 1. Fetch knowledge source article
        article = session.query(NewsArticle).filter(NewsArticle.id == article_id).first()
        if not article:
            raise ArticleIneligibleForOutputError(
                f"Article ID {article_id} not found in PostgreSQL knowledge source.",
                article_id=article_id,
            )

        # 2. Check idempotency before doing generation
        if not force_recreate:
            existing = DocumentIdempotencyService.get_existing_created_document(session, article_id)
            if existing:
                return Step8DocumentResponse(
                    success=True,
                    status=DocumentStatus.CREATED.value,
                    article_id=article_id,
                    data=Step8DocumentRecordSchema.model_validate(existing),
                    is_duplicate_prevented=True,
                    processing_time_ms=0.0,
                )

        # 3. Generate validated news via Step 7 service
        from backend.step7_content_generation.services.generation_service import GenerationService
        gen_service = GenerationService()

        pub_date_str = str(article.published_at) if article.published_at else None
        generated_news = gen_service.generate_news(
            title=article.title,
            content=article.content,
            category=article.category,
            source_name=article.source_name or "Unknown Source",
            source_url=article.url,
            author=article.author,
            published_at=pub_date_str,
            description=article.description,
            subcategory=article.subcategory,
        )

        return self.process_approved_content(
            news=generated_news,
            article_id=article_id,
            session=session,
            original_published_at=pub_date_str,
            force_recreate=force_recreate,
        )

    def retry_article(
        self,
        article_id: int,
        session: Session,
    ) -> Step8DocumentResponse:
        """Retry a previously failed or pending document creation."""
        record = GoogleDocumentRepository.get_by_article_id(session, article_id)
        if not record:
            raise DocumentRecordNotFoundError(article_id)

        if record.status == DocumentStatus.CREATED.value and record.google_document_id:
            # Already created, return record
            return Step8DocumentResponse(
                success=True,
                status=DocumentStatus.CREATED.value,
                article_id=article_id,
                data=Step8DocumentRecordSchema.model_validate(record),
                is_duplicate_prevented=True,
            )

        return self.process_article_by_id(
            article_id=article_id,
            session=session,
            force_recreate=False,
        )
