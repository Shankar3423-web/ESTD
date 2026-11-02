"""SQLAlchemy ORM model for ESTD subcategories."""
from datetime import datetime, timezone
from typing import List

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from backend.database.connection.session import Base


class Subcategory(Base):
    """Reference table for ESTD subcategories belonging to a parent category."""

    __tablename__ = "subcategories"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    category_id = Column(
        Integer,
        ForeignKey("categories.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        doc="Foreign key to parent category in categories table",
    )
    code = Column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
        doc="Stable canonical subcategory code e.g. ENT_MOVIES, TECH_AI",
    )
    name = Column(
        String(100),
        nullable=False,
        index=True,
        doc="Human-readable subcategory display name",
    )
    slug = Column(
        String(100),
        nullable=False,
        index=True,
        doc="URL-safe kebab-case slug",
    )
    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
        doc="Whether subcategory is active for routing",
    )
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        doc="UTC timestamp when subcategory was created",
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
        doc="UTC timestamp of last update",
    )

    # Relationships
    category_ref = relationship("Category", back_populates="subcategories")
    articles = relationship("NewsArticle", back_populates="subcategory_ref")

    __table_args__ = (
        UniqueConstraint("category_id", "slug", name="uq_subcategories_category_slug"),
        UniqueConstraint("category_id", "name", name="uq_subcategories_category_name"),
    )

    def __repr__(self) -> str:
        return f"<Subcategory(id={self.id}, code='{self.code}', name='{self.name}', category_id={self.category_id})>"
