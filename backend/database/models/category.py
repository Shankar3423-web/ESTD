"""SQLAlchemy ORM model for ESTD canonical categories."""
from datetime import datetime, timezone
from typing import List

from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.orm import relationship

from backend.database.connection.session import Base


class Category(Base):
    """Reference table for canonical ESTD categories."""

    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    code = Column(String(50), unique=True, nullable=False, index=True, doc="Stable canonical category code e.g. ENT, TECH")
    name = Column(String(100), unique=True, nullable=False, index=True, doc="Display name of category")
    slug = Column(String(100), unique=True, nullable=False, index=True, doc="URL-safe kebab-case slug")
    is_active = Column(Boolean, default=True, nullable=False, index=True, doc="Whether category is active for routing")
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        doc="UTC timestamp when category row was created",
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
        doc="UTC timestamp of last update",
    )

    # Relational link to articles and subcategories in this category
    articles = relationship(
        "NewsArticle",
        back_populates="category_ref",
        cascade="all, delete-orphan",
    )
    subcategories = relationship(
        "Subcategory",
        back_populates="category_ref",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Category(id={self.id}, code='{self.code}', name='{self.name}', slug='{self.slug}')>"
