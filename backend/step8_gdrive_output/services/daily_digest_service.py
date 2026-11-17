"""Daily Category Digest service for aggregating articles and compiling Google Docs in Google Drive."""
from datetime import date, datetime, time, timezone
from typing import Any, Dict, List, Optional
import sqlalchemy as sa
from sqlalchemy.orm import Session

from backend.common.config.settings import get_settings
from backend.common.constants.categories import VALID_CATEGORIES
from backend.common.logging.logger import logger
from backend.database.connection.session import get_db_session
from backend.database.models.daily_digest_record import DailyDigestRecord, DigestStatus
from backend.database.models.news_article import NewsArticle
from backend.step8_gdrive_output.config.gdrive_settings import FINAL_CATEGORIES
from backend.step8_gdrive_output.services.digest_formatter import DigestFormatter
from backend.step8_gdrive_output.services.folder_resolver import DriveFolderResolver
from backend.step8_gdrive_output.services.gdrive_service import GoogleDriveService


class DailyDigestService:
    """Orchestrates daily category digest generation, formatting, and Google Drive compilation."""

    def __init__(
        self,
        gdrive_service: Optional[GoogleDriveService] = None,
        folder_resolver: Optional[DriveFolderResolver] = None,
    ):
        self.gdrive_service = gdrive_service or GoogleDriveService()
        self.folder_resolver = folder_resolver or DriveFolderResolver(self.gdrive_service)

    def get_articles_for_digest(
        self,
        category: str,
        target_date: date,
        session: Session,
        fallback_recent: bool = True,
        max_limit: int = 50,
    ) -> List[NewsArticle]:
        """Fetch approved articles for a category and date.
        
        If no articles exist exactly for target_date and fallback_recent is True,
        retrieves recent approved articles in that category (useful for manual runs/testing).
        """
        # Define UTC date boundary
        start_dt = datetime.combine(target_date, time.min).replace(tzinfo=timezone.utc)
        end_dt = datetime.combine(target_date, time.max).replace(tzinfo=timezone.utc)

        # Primary query: articles created on target_date
        query = (
            session.query(NewsArticle)
            .filter(NewsArticle.category == category)
            .filter(NewsArticle.created_at >= start_dt)
            .filter(NewsArticle.created_at <= end_dt)
            .filter(NewsArticle.qa_status.in_(["APPROVED", "PUBLISHED", "AI_GENERATED"]))
            .order_by(NewsArticle.created_at.desc())
        )
        articles = query.limit(max_limit).all()

        # If zero articles on target_date, fallback to recent approved/available articles
        if not articles and fallback_recent:
            fallback_query = (
                session.query(NewsArticle)
                .filter(NewsArticle.category == category)
                .order_by(NewsArticle.created_at.desc())
            )
            articles = fallback_query.limit(max_limit).all()
            if articles:
                logger.info(
                    f"Target date {target_date} had 0 articles for '{category}'. "
                    f"Fell back to {len(articles)} recent available articles."
                )

        return articles

    def generate_category_digest(
        self,
        category: str,
        target_date: Optional[date] = None,
        dry_run: bool = False,
        force: bool = False,
        session: Optional[Session] = None,
    ) -> Dict[str, Any]:
        """Generate, compile, and upload one category digest Google Document.

        Args:
            category: Canonical category (Tech, Sports, Entertainment, etc.)
            target_date: Calendar date of digest (defaults to UTC today)
            dry_run: If True, compiles and validates document without calling Google Drive API
            force: If True, overwrites/recreates even if a completed record exists
            session: Optional SQLAlchemy session
        """
        digest_date = target_date or datetime.now(timezone.utc).date()

        def _execute(s: Session) -> Dict[str, Any]:
            # Check existing record for idempotency
            existing_record = (
                s.query(DailyDigestRecord)
                .filter(
                    DailyDigestRecord.digest_date == digest_date,
                    DailyDigestRecord.category == category,
                )
                .first()
            )

            if existing_record and existing_record.status == DigestStatus.COMPLETED.value and not force and not dry_run:
                logger.info(
                    f"Digest for '{category}' on {digest_date} already exists "
                    f"(Doc ID: {existing_record.google_document_id}). Skipping."
                )
                return {
                    "category": category,
                    "date": str(digest_date),
                    "status": "ALREADY_EXISTS",
                    "article_count": existing_record.article_count,
                    "google_document_id": existing_record.google_document_id,
                    "google_document_url": existing_record.google_document_url,
                }

            # Fetch articles from database
            articles = self.get_articles_for_digest(category, digest_date, s)

            if not articles:
                logger.warning(f"No articles found for category '{category}' on {digest_date}.")
                if not dry_run:
                    if not existing_record:
                        existing_record = DailyDigestRecord(
                            digest_date=digest_date,
                            category=category,
                            article_count=0,
                            status=DigestStatus.EMPTY.value,
                        )
                        s.add(existing_record)
                    else:
                        existing_record.status = DigestStatus.EMPTY.value
                        existing_record.article_count = 0
                    s.commit()

                return {
                    "category": category,
                    "date": str(digest_date),
                    "status": "EMPTY",
                    "article_count": 0,
                    "message": f"No articles available for category '{category}' on {digest_date}.",
                }

            # Format the consolidated document text
            doc_title = DigestFormatter.build_document_title(category, digest_date)
            doc_content = DigestFormatter.format_category_digest(category, digest_date, articles)

            if dry_run:
                return {
                    "category": category,
                    "date": str(digest_date),
                    "status": "DRY_RUN_SUCCESS",
                    "article_count": len(articles),
                    "title": doc_title,
                    "character_count": len(doc_content),
                    "preview": doc_content[:600] + "\n...",
                }

            # Resolve Google Drive category folder ID
            folder_id = self.folder_resolver.resolve_category_folder_id(category)

            # Upload Google Document via Google Drive API
            logger.info(
                f"Uploading Daily Digest '{doc_title}' ({len(articles)} stories) to Google Drive folder '{folder_id}'..."
            )
            try:
                gdrive_resp = self.gdrive_service.create_google_document(
                    title=doc_title,
                    folder_id=folder_id,
                    content=doc_content,
                )

                doc_id = gdrive_resp.get("id")
                doc_url = gdrive_resp.get("webViewLink") or f"https://docs.google.com/document/d/{doc_id}/edit"

                # Update database record on success
                if not existing_record:
                    existing_record = DailyDigestRecord(
                        digest_date=digest_date,
                        category=category,
                        article_count=len(articles),
                        google_document_id=doc_id,
                        google_document_url=doc_url,
                        google_drive_folder_id=folder_id,
                        status=DigestStatus.COMPLETED.value,
                    )
                    s.add(existing_record)
                else:
                    existing_record.article_count = len(articles)
                    existing_record.google_document_id = doc_id
                    existing_record.google_document_url = doc_url
                    existing_record.google_drive_folder_id = folder_id
                    existing_record.status = DigestStatus.COMPLETED.value
                    existing_record.error_message = None

                s.commit()
                logger.info(f"Daily Digest for '{category}' successfully compiled: {doc_url}")

                return {
                    "category": category,
                    "date": str(digest_date),
                    "status": "COMPLETED",
                    "article_count": len(articles),
                    "google_document_id": doc_id,
                    "google_document_url": doc_url,
                    "google_drive_folder_id": folder_id,
                }

            except Exception as upload_exc:
                err_str = str(upload_exc)
                logger.error(f"Failed exporting Daily Digest for '{category}' to Google Drive: {err_str}")
                if not existing_record:
                    existing_record = DailyDigestRecord(
                        digest_date=digest_date,
                        category=category,
                        article_count=len(articles),
                        status=DigestStatus.FAILED.value,
                        error_message=err_str[:1000],
                    )
                    s.add(existing_record)
                else:
                    existing_record.status = DigestStatus.FAILED.value
                    existing_record.error_message = err_str[:1000]
                s.commit()

                return {
                    "category": category,
                    "date": str(digest_date),
                    "status": "FAILED",
                    "article_count": len(articles),
                    "error": err_str,
                }

        if session is not None:
            return _execute(session)
        with get_db_session() as new_session:
            return _execute(new_session)

    def generate_all_digests_for_date(
        self,
        target_date: Optional[date] = None,
        categories: Optional[List[str]] = None,
        dry_run: bool = False,
        force: bool = False,
    ) -> Dict[str, Any]:
        """Compile daily digests across all configured categories for the target date."""
        digest_date = target_date or datetime.now(timezone.utc).date()
        target_categories = categories or list(FINAL_CATEGORIES)

        results = []
        errors = []

        logger.info(
            f"Starting Daily Digest compilation for {digest_date} across {len(target_categories)} categories "
            f"(dry_run={dry_run}, force={force})..."
        )

        for cat in target_categories:
            try:
                res = self.generate_category_digest(
                    category=cat,
                    target_date=digest_date,
                    dry_run=dry_run,
                    force=force,
                )
                results.append(res)
            except Exception as exc:
                logger.error(f"Error generating daily digest for category '{cat}': {exc}", exc_info=True)
                errors.append({"category": cat, "error": str(exc)})

        return {
            "date": str(digest_date),
            "dry_run": dry_run,
            "total_categories": len(target_categories),
            "successful_digests": len(results),
            "failed_categories": len(errors),
            "digests": results,
            "errors": errors,
        }
