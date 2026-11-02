"""SQLAlchemy ORM model for Step 5 NewsArticle persistence."""
from datetime import datetime, timezone
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

from backend.common.constants.categories import VALID_CATEGORIES
from backend.database.connection.session import Base


class NewsArticle(Base):
    """Primary knowledge source article table storing validated, unique, cleaned news."""

    __tablename__ = "news_articles"

    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)

    # Core Content
    title = Column(Text, nullable=False, doc="Headline or title of the news article")
    description = Column(Text, nullable=True, doc="Short synopsis or description")
    content = Column(Text, nullable=False, doc="Cleaned, normalized, and validated article body")
    url = Column(Text, nullable=False, doc="Original article URL")

    # Identifiers & Duplicate Protection
    normalized_url = Column(
        String(1024),
        nullable=False,
        unique=True,
        index=True,
        doc="Normalized canonical URL used for deduplication",
    )
    content_hash = Column(
        String(64),
        nullable=False,
        unique=True,
        index=True,
        doc="SHA-256 hex digest of normalized content",
    )

    # Provenance & Metadata
    source_name = Column(String(255), nullable=True, index=True, doc="Publisher or source publication name")
    source_type = Column(String(100), nullable=False, index=True, doc="Provider identifier: gnews, newsdata, rss")
    author = Column(String(255), nullable=True, doc="Author or creator if identified")
    published_at = Column(DateTime(timezone=True), nullable=True, index=True, doc="UTC publication timestamp")
    image_url = Column(Text, nullable=True, doc="URL to primary article image")

    # Category & Subcategory Reference
    category = Column(String(100), nullable=False, index=True, doc="Canonical category name")
    category_id = Column(
        Integer,
        ForeignKey("categories.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        doc="Foreign key to categories table",
    )
    subcategory = Column(String(100), nullable=True, index=True, doc="Canonical subcategory display name")
    subcategory_id = Column(
        Integer,
        ForeignKey("subcategories.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="Foreign key to subcategories table",
    )
    original_source_category = Column(
        String(100),
        nullable=True,
        index=True,
        doc="Original source or legacy category provenance",
    )
    language = Column(
        String(20),
        default="en",
        nullable=True,
        index=True,
        doc="Language code e.g. en, te, hi",
    )
    region = Column(
        String(50),
        nullable=True,
        index=True,
        doc="Geographic or market scope e.g. national, international",
    )
    likes_count = Column(
        Integer,
        default=0,
        server_default="0",
        nullable=False,
        index=True,
        doc="Total persistent likes for this article",
    )

    # Audit Timestamps
    collected_at = Column(DateTime(timezone=True), nullable=False, doc="UTC timestamp when collected in Step 1")
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
        doc="UTC timestamp when record was persisted in Step 5",
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
        doc="UTC timestamp of last update",
    )

    # Relational links
    category_ref = relationship("Category", back_populates="articles")
    subcategory_ref = relationship("Subcategory", back_populates="articles")

    __table_args__ = (
        CheckConstraint("length(trim(title)) > 0", name="ck_news_articles_title_not_empty"),
        CheckConstraint("length(trim(url)) > 0", name="ck_news_articles_url_not_empty"),
        CheckConstraint("length(trim(content)) > 0", name="ck_news_articles_content_not_empty"),
        CheckConstraint(
            f"category IN {tuple(VALID_CATEGORIES)}",
            name="ck_news_articles_valid_category",
        ),
        Index("ix_news_articles_cat_pub", "category", "published_at"),
        Index("ix_news_articles_cat_subcat", "category", "subcategory"),
        Index("ix_news_articles_source_pub", "source_name", "published_at"),
        Index("ix_news_articles_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<NewsArticle(id={self.id}, title='{self.title[:30]}...', "
            f"category='{self.category}', source='{self.source_name}')>"
        )
