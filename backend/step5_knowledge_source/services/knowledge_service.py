"""Service layer orchestrating Step 5 Knowledge Source persistence and retrieval."""
from datetime import datetime, timezone
import math
from typing import List, Optional, Tuple, Union

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.common.constants.categories import VALID_CATEGORIES
from backend.common.exceptions.custom_exceptions import InvalidCategoryError
from backend.common.logging.logger import logger
from backend.common.utils.datetime_utils import get_utc_now_iso, normalize_datetime_to_iso
from backend.database.connection.session import check_db_health, get_db_session
from backend.database.models.category import Category
from backend.database.models.news_article import NewsArticle
from backend.database.repositories.category_repository import CategoryRepository
from backend.database.repositories.news_article_repository import NewsArticleRepository
from backend.step3_content_cleaning.models.cleaned_article import CleanedArticle
from backend.step4_duplicate_detection.detectors.exact_content_detector import ExactContentDetector
from backend.step4_duplicate_detection.normalizers.url_normalizer import normalize_url
from backend.step4_duplicate_detection.schemas.duplicate_response import DuplicateCheckResult
from backend.step5_knowledge_source.exceptions import (
    ArticleDuplicateError,
    ArticleNotFoundError,
    CategoryNotFoundError,
    DatabaseConnectionError,
    InvalidArticleDataError,
)
from backend.step5_knowledge_source.schemas.article_schemas import (
    ArticleCreateRequest,
    PaginationMetadata,
)


class KnowledgeSourceService:
    """Service handling validation, persistence, and queries for the ESTD Knowledge Source."""

    def __init__(
        self,
        article_repo: Optional[NewsArticleRepository] = None,
        category_repo: Optional[CategoryRepository] = None,
    ):
        self.article_repo = article_repo or NewsArticleRepository()
        self.category_repo = category_repo or CategoryRepository()

    def persist_from_step4(
        self,
        check_result: DuplicateCheckResult,
        session: Optional[Session] = None,
    ) -> NewsArticle:
        """Persist a Step 4 evaluated article.
        
        Strict contract rule: Duplicate articles MUST NOT be persisted to the knowledge source.
        """
        if check_result.status.lower() == "duplicate" or check_result.decision.is_duplicate:
            reason = check_result.decision.duplicate_reason or "DUPLICATE_DECISION"
            matched_id = check_result.decision.matched_article_id or "unknown"
            logger.warning(
                f"[Step 5] Rejected duplicate article persistence: '{check_result.article.title}' | "
                f"reason={reason} | matched_id={matched_id}"
            )
            raise ArticleDuplicateError(
                reason=f"Step 4 decision ({reason})",
                identifier=check_result.decision.normalized_url,
            )

        article = check_result.article
        decision = check_result.decision

        return self._persist_article_fields(
            title=article.title,
            description=article.description,
            content=article.content or article.cleaned_content or "",
            url=article.url,
            normalized_url=decision.normalized_url,
            content_hash=decision.content_hash,
            source_name=article.source_name,
            source_type=article.source_type,
            author=article.author,
            published_at_str=article.published_at,
            category_name=article.category,
            subcategory_name=getattr(article, "subcategory", None),
            original_source_category=getattr(article, "original_source_category", None),
            language=getattr(article, "language", "en"),
            region=getattr(article, "region", None),
            image_url=article.image_url,
            collected_at_str=article.collected_at,
            session=session,
        )

    def persist_cleaned_article(
        self,
        cleaned_article: CleanedArticle,
        session: Optional[Session] = None,
    ) -> NewsArticle:
        """Persist a CleanedArticle directly, generating normalized URL and hash if absent."""
        content = cleaned_article.content or cleaned_article.cleaned_content
        if not content or not content.strip():
            raise InvalidArticleDataError("Cannot persist article with empty cleaned content.")

        norm_url = normalize_url(cleaned_article.url)
        content_hash = ExactContentDetector.compute_content_hash(content)

        return self._persist_article_fields(
            title=cleaned_article.title,
            description=cleaned_article.description,
            content=content,
            url=cleaned_article.url,
            normalized_url=norm_url,
            content_hash=content_hash,
            source_name=cleaned_article.source_name,
            source_type=cleaned_article.source_type,
            author=cleaned_article.author,
            published_at_str=cleaned_article.published_at,
            category_name=cleaned_article.category,
            subcategory_name=getattr(cleaned_article, "subcategory", None),
            original_source_category=getattr(cleaned_article, "original_source_category", None),
            language=getattr(cleaned_article, "language", "en"),
            region=getattr(cleaned_article, "region", None),
            image_url=cleaned_article.image_url,
            collected_at_str=cleaned_article.collected_at,
            session=session,
        )

    def create_article(
        self,
        request: ArticleCreateRequest,
        session: Optional[Session] = None,
    ) -> NewsArticle:
        """Persist a new article from an API request payload."""
        if not request.title or not request.title.strip():
            raise InvalidArticleDataError("Article title cannot be empty.")
        if not request.content or not request.content.strip():
            raise InvalidArticleDataError("Article content cannot be empty.")
        if not request.url or not request.url.strip():
            raise InvalidArticleDataError("Article URL cannot be empty.")

        norm_url = request.normalized_url or normalize_url(request.url)
        content_hash = request.content_hash or ExactContentDetector.compute_content_hash(request.content)

        return self._persist_article_fields(
            title=request.title.strip(),
            description=request.description.strip() if request.description else None,
            content=request.content.strip(),
            url=request.url.strip(),
            normalized_url=norm_url,
            content_hash=content_hash,
            source_name=request.source_name,
            source_type=request.source_type,
            author=request.author,
            published_at_str=request.published_at,
            category_name=request.category,
            subcategory_name=request.subcategory,
            original_source_category=request.original_source_category,
            language=request.language or "en",
            region=request.region,
            image_url=request.image_url,
            collected_at_str=request.collected_at or get_utc_now_iso(),
            session=session,
        )

    def _persist_article_fields(
        self,
        title: str,
        description: Optional[str],
        content: str,
        url: str,
        normalized_url: str,
        content_hash: str,
        source_name: Optional[str],
        source_type: str,
        author: Optional[str],
        published_at_str: Optional[str],
        category_name: str,
        image_url: Optional[str],
        collected_at_str: Optional[str],
        subcategory_name: Optional[str] = None,
        original_source_category: Optional[str] = None,
        language: Optional[str] = "en",
        region: Optional[str] = None,
        session: Optional[Session] = None,
    ) -> NewsArticle:
        """Internal worker persisting validated article attributes within transactional scope."""
        from backend.common.constants.categories import resolve_canonical_category, resolve_subcategory
        canonical_cat = resolve_canonical_category(category_name)
        if not canonical_cat:
            raise InvalidCategoryError(category_name)

        if not content or not content.strip():
            raise InvalidArticleDataError("Article content cannot be empty.")

        def _execute(sess: Session) -> NewsArticle:
            # Check for existing duplicate before attempting insert
            duplicate = self.article_repo.find_duplicate(
                sess,
                normalized_url=normalized_url,
                content_hash=content_hash,
            )
            if duplicate:
                reason = "normalized_url" if duplicate.normalized_url == normalized_url else "content_hash"
                identifier = normalized_url if reason == "normalized_url" else content_hash
                logger.info(
                    f"[Step 5] Duplicate prevented by database check: {reason}='{identifier}' | "
                    f"existing_article_id={duplicate.id}"
                )
                raise ArticleDuplicateError(reason=reason, identifier=identifier)

            # Resolve category FK
            category_record = self.category_repo.get_by_name(sess, canonical_cat)
            if not category_record:
                # Idempotently seed if missing or raise
                seeded = self.category_repo.seed_categories(sess)
                for cat in seeded:
                    if cat.name == canonical_cat:
                        category_record = cat
                        break
                if not category_record:
                    raise CategoryNotFoundError(canonical_cat)

            # Resolve subcategory FK if provided
            subcat_record = None
            resolved_subcat_name = subcategory_name
            if subcategory_name:
                from backend.database.repositories.category_repository import SubcategoryRepository
                try:
                    resolved_subcat_name = resolve_subcategory(subcategory_name, canonical_cat)
                    subcat_record = SubcategoryRepository.get_by_name(sess, resolved_subcat_name)
                except Exception:
                    subcat_record = SubcategoryRepository.get_by_name(sess, subcategory_name)

            # Parse timestamps to timezone-aware UTC datetime
            published_at_dt = self._parse_datetime(published_at_str)
            collected_at_dt = self._parse_datetime(collected_at_str) or datetime.now(timezone.utc)

            new_article = NewsArticle(
                title=title,
                description=description,
                content=content,
                url=url,
                normalized_url=normalized_url,
                content_hash=content_hash,
                source_name=source_name,
                source_type=source_type.lower() if source_type else "custom",
                author=author,
                published_at=published_at_dt,
                category=canonical_cat,
                category_id=category_record.id,
                subcategory=subcat_record.name if subcat_record else resolved_subcat_name,
                subcategory_id=subcat_record.id if subcat_record else None,
                original_source_category=original_source_category,
                language=language or "en",
                region=region,
                image_url=image_url,
                collected_at=collected_at_dt,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )

            try:
                persisted = self.article_repo.create(sess, new_article)
                logger.info(
                    f"[Step 5] Persisted article: ID={persisted.id} | title='{persisted.title[:40]}...' | "
                    f"category='{persisted.category}' | source='{persisted.source_name}'"
                )
                return persisted
            except IntegrityError as exc:
                sess.rollback()
                err_msg = str(exc).lower()
                if "normalized_url" in err_msg or "uq_news_articles_normalized_url" in err_msg:
                    raise ArticleDuplicateError(reason="normalized_url", identifier=normalized_url)
                if "content_hash" in err_msg or "uq_news_articles_content_hash" in err_msg:
                    raise ArticleDuplicateError(reason="content_hash", identifier=content_hash)
                logger.error(f"Database constraint violation during article persistence: {exc}")
                raise InvalidArticleDataError(f"Database integrity constraint violated: {exc}")

        if session is not None:
            return _execute(session)
        with get_db_session() as managed_session:
            return _execute(managed_session)

    def get_article_by_id(
        self,
        article_id: int,
        session: Optional[Session] = None,
    ) -> NewsArticle:
        """Retrieve a persisted article by its primary key ID."""
        def _execute(sess: Session) -> NewsArticle:
            article = self.article_repo.get_by_id(sess, article_id)
            if not article:
                raise ArticleNotFoundError(article_id)
            return article

        if session is not None:
            return _execute(session)
        with get_db_session() as managed_session:
            return _execute(managed_session)

    def get_article_by_url(
        self,
        url: str,
        session: Optional[Session] = None,
    ) -> Optional[NewsArticle]:
        """Retrieve an article by its original URL."""
        def _execute(sess: Session) -> Optional[NewsArticle]:
            return self.article_repo.get_by_url(sess, url)

        if session is not None:
            return _execute(session)
        with get_db_session() as managed_session:
            return _execute(managed_session)

    def list_articles(
        self,
        category: Optional[str] = None,
        subcategory: Optional[str] = None,
        source: Optional[str] = None,
        source_type: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        page: int = 1,
        page_size: int = 10,
        session: Optional[Session] = None,
    ) -> Tuple[List[NewsArticle], PaginationMetadata]:
        """Query and paginate articles with validation of filters."""
        from backend.common.constants.categories import resolve_canonical_category
        resolved_category = None
        if category is not None and category != "":
            resolved_category = resolve_canonical_category(category)
            if not resolved_category:
                raise InvalidCategoryError(category)

        # Enforce page and page_size bounds
        effective_page = max(1, page)
        effective_page_size = min(100, max(1, page_size))
        offset = (effective_page - 1) * effective_page_size

        start_dt = self._parse_datetime(start_date) if start_date else None
        end_dt = self._parse_datetime(end_date) if end_date else None

        def _execute(sess: Session) -> Tuple[List[NewsArticle], PaginationMetadata]:
            items = self.article_repo.list_articles(
                sess,
                category=resolved_category,
                subcategory=subcategory,
                source=source,
                source_type=source_type,
                start_date=start_dt,
                end_date=end_dt,
                offset=offset,
                limit=effective_page_size,
            )
            total_items = self.article_repo.count_articles(
                sess,
                category=resolved_category,
                subcategory=subcategory,
                source=source,
                source_type=source_type,
                start_date=start_dt,
                end_date=end_dt,
            )
            total_pages = math.ceil(total_items / effective_page_size) if total_items > 0 else 0

            pagination = PaginationMetadata(
                page=effective_page,
                page_size=effective_page_size,
                total_items=total_items,
                total_pages=total_pages,
                has_next=effective_page < total_pages,
                has_prev=effective_page > 1 and total_pages > 0,
            )
            return items, pagination

        if session is not None:
            return _execute(session)
        with get_db_session() as managed_session:
            return _execute(managed_session)

    def delete_article(
        self,
        article_id: int,
        session: Optional[Session] = None,
    ) -> bool:
        """Delete an article by ID."""
        def _execute(sess: Session) -> bool:
            deleted = self.article_repo.delete(sess, article_id)
            if not deleted:
                raise ArticleNotFoundError(article_id)
            logger.info(f"[Step 5] Deleted article ID={article_id}")
            return True

        if session is not None:
            return _execute(session)
        with get_db_session() as managed_session:
            return _execute(managed_session)

    def list_categories(self, session: Optional[Session] = None) -> List[Category]:
        """Fetch all canonical categories."""
        def _execute(sess: Session) -> List[Category]:
            cats = self.category_repo.list_all(sess)
            if not cats or len(cats) < len(VALID_CATEGORIES):
                cats = self.category_repo.seed_categories(sess)
            return cats

        if session is not None:
            return _execute(session)
        with get_db_session() as managed_session:
            return _execute(managed_session)

    def list_subcategories(
        self,
        category: Optional[str] = None,
        session: Optional[Session] = None,
    ):
        """Fetch canonical subcategories, optionally filtered by parent category."""
        from backend.database.models.subcategory import Subcategory
        from backend.database.repositories.category_repository import SubcategoryRepository
        from backend.common.constants.categories import resolve_canonical_category

        def _execute(sess: Session):
            if category:
                try:
                    canonical_cat = resolve_canonical_category(category)
                except Exception:
                    canonical_cat = category
                cat = self.category_repo.get_by_name(sess, canonical_cat)
                if cat:
                    return SubcategoryRepository.list_by_category(sess, cat.id)
                return []
            return list(sess.query(Subcategory).order_by(Subcategory.category_id, Subcategory.id).all())

        if session is not None:
            return _execute(session)
        with get_db_session() as managed_session:
            return _execute(managed_session)

    def check_health(self) -> dict:
        """Perform database health verification."""
        try:
            return check_db_health()
        except Exception as exc:
            logger.error(f"Database health check failed: {exc}")
            raise DatabaseConnectionError(f"Database health check failed: {exc}")

    @staticmethod
    def _parse_datetime(dt_str: Optional[str]) -> Optional[datetime]:
        """Convert an ISO string or arbitrary datetime format to a UTC aware datetime."""
        if not dt_str:
            return None
        iso_str = normalize_datetime_to_iso(dt_str)
        if not iso_str:
            return None
        try:
            if iso_str.endswith("Z"):
                iso_str = iso_str[:-1] + "+00:00"
            dt = datetime.fromisoformat(iso_str)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            else:
                dt = dt.astimezone(timezone.utc)
            return dt
        except Exception:
            return None
