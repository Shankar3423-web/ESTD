"""Repository layer for ESTD category and subcategory reference operations."""
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.common.constants.categories import (
    CATEGORY_METADATA,
    ESTDCategory,
    ESTDSubcategory,
    SUBCATEGORY_METADATA,
)
from backend.common.logging.logger import logger
from backend.database.models.category import Category
from backend.database.models.subcategory import Subcategory


class CategoryRepository:
    """Encapsulates data access and idempotent seeding for reference categories."""

    CANONICAL_CATEGORIES = [
        CATEGORY_METADATA[cat.value] for cat in ESTDCategory
    ]

    @staticmethod
    def get_by_id(session: Session, category_id: int) -> Optional[Category]:
        """Fetch category by its primary key ID."""
        return session.get(Category, category_id)

    @staticmethod
    def get_by_code(session: Session, code: str) -> Optional[Category]:
        """Fetch category by canonical code (e.g. 'ENT', 'TECH')."""
        stmt = select(Category).where(Category.code == code.upper())
        return session.execute(stmt).scalar_one_or_none()

    @staticmethod
    def get_by_name(session: Session, name: str) -> Optional[Category]:
        """Fetch category by exact display name (e.g. 'Entertainment')."""
        stmt = select(Category).where(Category.name == name)
        return session.execute(stmt).scalar_one_or_none()

    @staticmethod
    def get_by_slug(session: Session, slug: str) -> Optional[Category]:
        """Fetch category by slug (e.g. 'entertainment')."""
        stmt = select(Category).where(Category.slug == slug.lower())
        return session.execute(stmt).scalar_one_or_none()

    @staticmethod
    def list_all(session: Session, active_only: bool = False) -> List[Category]:
        """List all canonical categories ordered by ID."""
        stmt = select(Category)
        if active_only:
            stmt = stmt.where(Category.is_active == True)
        stmt = stmt.order_by(Category.id.asc())
        return list(session.execute(stmt).scalars().all())

    @classmethod
    def seed_categories(cls, session: Session) -> List[Category]:
        """Deterministically and idempotently seed the 5 canonical ESTD categories and subcategories.

        Running this repeatedly will never produce duplicates.
        """
        seeded = []
        for cat_info in cls.CANONICAL_CATEGORIES:
            existing = cls.get_by_code(session, cat_info["code"])
            if existing is None:
                # Also check by name in case code wasn't set previously
                existing = cls.get_by_name(session, cat_info["name"])
            
            if existing is None:
                new_cat = Category(
                    code=cat_info["code"],
                    name=cat_info["name"],
                    slug=cat_info["slug"],
                    is_active=True,
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                )
                session.add(new_cat)
                session.flush()
                seeded.append(new_cat)
                logger.info(f"Seeded category: '{cat_info['name']}' (ID={new_cat.id})")
            else:
                existing.code = cat_info["code"]
                existing.name = cat_info["name"]
                existing.slug = cat_info["slug"]
                existing.is_active = True
                existing.updated_at = datetime.now(timezone.utc)
                session.flush()
                seeded.append(existing)

        # Also seed subcategories
        SubcategoryRepository.seed_subcategories(session)
        return seeded


class SubcategoryRepository:
    """Encapsulates data access and idempotent seeding for reference subcategories."""

    @staticmethod
    def get_by_id(session: Session, subcategory_id: int) -> Optional[Subcategory]:
        """Fetch subcategory by ID."""
        return session.get(Subcategory, subcategory_id)

    @staticmethod
    def get_by_code(session: Session, code: str) -> Optional[Subcategory]:
        """Fetch subcategory by canonical code (e.g. 'ENT_MOVIES')."""
        stmt = select(Subcategory).where(Subcategory.code == code.upper())
        return session.execute(stmt).scalar_one_or_none()

    @staticmethod
    def get_by_name(session: Session, name: str) -> Optional[Subcategory]:
        """Fetch subcategory by display name."""
        stmt = select(Subcategory).where(Subcategory.name == name)
        return session.execute(stmt).scalars().first()

    @staticmethod
    def get_by_category_and_name(
        session: Session, category_id: int, name: str
    ) -> Optional[Subcategory]:
        """Fetch subcategory by category_id and display name."""
        stmt = select(Subcategory).where(
            Subcategory.category_id == category_id,
            Subcategory.name == name,
        )
        return session.execute(stmt).scalar_one_or_none()

    @staticmethod
    def get_by_category_and_slug(
        session: Session, category_id: int, slug: str
    ) -> Optional[Subcategory]:
        """Fetch subcategory by category_id and slug."""
        stmt = select(Subcategory).where(
            Subcategory.category_id == category_id,
            Subcategory.slug == slug.lower(),
        )
        return session.execute(stmt).scalar_one_or_none()

    @staticmethod
    def list_by_category(
        session: Session, category_id: int, active_only: bool = False
    ) -> List[Subcategory]:
        """List all subcategories for a given parent category."""
        stmt = select(Subcategory).where(Subcategory.category_id == category_id)
        if active_only:
            stmt = stmt.where(Subcategory.is_active == True)
        stmt = stmt.order_by(Subcategory.id.asc())
        return list(session.execute(stmt).scalars().all())

    @classmethod
    def seed_subcategories(cls, session: Session) -> List[Subcategory]:
        """Idempotently seed all approved canonical subcategories."""
        seeded = []
        now_utc = datetime.now(timezone.utc)
        for sub_name, meta in SUBCATEGORY_METADATA.items():
            parent_cat = CategoryRepository.get_by_name(session, meta["parent_category"])
            if not parent_cat:
                continue

            existing = cls.get_by_code(session, meta["code"])
            if existing is None:
                existing = cls.get_by_category_and_name(session, parent_cat.id, sub_name)

            if existing is None:
                new_sub = Subcategory(
                    category_id=parent_cat.id,
                    code=meta["code"],
                    name=sub_name,
                    slug=meta["slug"],
                    is_active=True,
                    created_at=now_utc,
                    updated_at=now_utc,
                )
                session.add(new_sub)
                session.flush()
                seeded.append(new_sub)
            else:
                existing.category_id = parent_cat.id
                existing.code = meta["code"]
                existing.name = sub_name
                existing.slug = meta["slug"]
                existing.is_active = True
                existing.updated_at = now_utc
                session.flush()
                seeded.append(existing)

        return seeded

