"""Repository layer for ESTD Knowledge Source NewsArticle operations."""
from datetime import datetime
from typing import List, Optional, Tuple

from sqlalchemy import desc, func, or_, select
from sqlalchemy.orm import Session, joinedload

from backend.database.models.news_article import NewsArticle


class NewsArticleRepository:
    """Encapsulates all database persistence and retrieval operations for news_articles."""

    @staticmethod
    def create(session: Session, article: NewsArticle) -> NewsArticle:
        """Persist a new unique news article to the database."""
        session.add(article)
        session.flush()
        return article

    @staticmethod
    def get_by_id(session: Session, article_id: int) -> Optional[NewsArticle]:
        """Fetch article by primary key ID, eagerly loading its category relationship."""
        stmt = (
            select(NewsArticle)
            .options(joinedload(NewsArticle.category_ref))
            .where(NewsArticle.id == article_id)
        )
        return session.execute(stmt).scalar_one_or_none()

    @staticmethod
    def get_by_url(session: Session, url: str) -> Optional[NewsArticle]:
        """Fetch article by exact original URL."""
        stmt = (
            select(NewsArticle)
            .options(joinedload(NewsArticle.category_ref))
            .where(NewsArticle.url == url)
            .order_by(NewsArticle.id.desc())
            .limit(1)
        )
        return session.execute(stmt).scalar_one_or_none()

    @staticmethod
    def get_by_normalized_url(session: Session, normalized_url: str) -> Optional[NewsArticle]:
        """Fetch article by canonical normalized URL."""
        stmt = (
            select(NewsArticle)
            .options(joinedload(NewsArticle.category_ref))
            .where(NewsArticle.normalized_url == normalized_url)
            .limit(1)
        )
        return session.execute(stmt).scalar_one_or_none()

    @staticmethod
    def get_by_content_hash(session: Session, content_hash: str) -> Optional[NewsArticle]:
        """Fetch article by SHA-256 content fingerprint."""
        stmt = (
            select(NewsArticle)
            .options(joinedload(NewsArticle.category_ref))
            .where(NewsArticle.content_hash == content_hash)
            .limit(1)
        )
        return session.execute(stmt).scalar_one_or_none()

    @staticmethod
    def find_duplicate(
        session: Session,
        normalized_url: str,
        content_hash: str,
    ) -> Optional[NewsArticle]:
        """Check if an article with either the same normalized URL or content hash exists."""
        stmt = (
            select(NewsArticle)
            .where(
                or_(
                    NewsArticle.normalized_url == normalized_url,
                    NewsArticle.content_hash == content_hash,
                )
            )
            .limit(1)
        )
        return session.execute(stmt).scalar_one_or_none()

    @staticmethod
    def list_articles(
        session: Session,
        category: Optional[str] = None,
        subcategory: Optional[str] = None,
        source: Optional[str] = None,
        source_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        offset: int = 0,
        limit: int = 10,
    ) -> List[NewsArticle]:
        """Retrieve paginated and filtered articles ordered by published_at / created_at desc."""
        stmt = select(NewsArticle).options(joinedload(NewsArticle.category_ref))

        if category:
            stmt = stmt.where(NewsArticle.category == category)
        if subcategory:
            stmt = stmt.where(NewsArticle.subcategory == subcategory)
        if source:
            stmt = stmt.where(NewsArticle.source_name.ilike(f"%{source}%"))
        if source_type:
            stmt = stmt.where(NewsArticle.source_type == source_type.lower())
        if start_date:
            stmt = stmt.where(NewsArticle.published_at >= start_date)
        if end_date:
            stmt = stmt.where(NewsArticle.published_at <= end_date)

        # Order by published_at descending (nulls last), then created_at descending
        stmt = stmt.order_by(
            NewsArticle.published_at.desc().nullslast(),
            NewsArticle.created_at.desc(),
        ).offset(offset).limit(limit)

        return list(session.execute(stmt).scalars().all())

    @staticmethod
    def count_articles(
        session: Session,
        category: Optional[str] = None,
        subcategory: Optional[str] = None,
        source: Optional[str] = None,
        source_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> int:
        """Count total matching articles matching the given criteria."""
        stmt = select(func.count(NewsArticle.id))

        if category:
            stmt = stmt.where(NewsArticle.category == category)
        if subcategory:
            stmt = stmt.where(NewsArticle.subcategory == subcategory)
        if source:
            stmt = stmt.where(NewsArticle.source_name.ilike(f"%{source}%"))
        if source_type:
            stmt = stmt.where(NewsArticle.source_type == source_type.lower())
        if start_date:
            stmt = stmt.where(NewsArticle.published_at >= start_date)
        if end_date:
            stmt = stmt.where(NewsArticle.published_at <= end_date)

        return session.execute(stmt).scalar() or 0

    @staticmethod
    def delete(session: Session, article_id: int) -> bool:
        """Delete an article by primary key ID."""
        article = session.get(NewsArticle, article_id)
        if article:
            session.delete(article)
            session.flush()
            return True
        return False
