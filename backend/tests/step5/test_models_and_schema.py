"""Tests verifying database schema, tables, constraints, and category system."""
import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.common.constants.categories import ESTDCategory, VALID_CATEGORIES
from backend.database.connection.session import get_db_session, get_engine
from backend.database.models.category import Category
from backend.database.models.news_article import NewsArticle
from backend.database.repositories.category_repository import CategoryRepository


def test_canonical_categories_exist():
    """Verify that exactly 5 canonical categories exist in the database."""
    with get_db_session() as session:
        categories = CategoryRepository.list_all(session)
        assert len(categories) == 5
        names = {c.name for c in categories}
        expected = {
            "Entertainment",
            "Sports",
            "Tech",
            "Developments",
            "Business & Finance",
        }
        assert names == expected


def test_category_seeding_is_idempotent():
    """Verify that repeatedly running seed_categories does NOT create duplicates."""
    with get_db_session() as session:
        # Run seed multiple times
        CategoryRepository.seed_categories(session)
        CategoryRepository.seed_categories(session)
        CategoryRepository.seed_categories(session)
        session.commit()

        # Count total rows
        categories = CategoryRepository.list_all(session)
        assert len(categories) == 5


def test_news_articles_table_structure():
    """Verify that news_articles table has all required columns and constraints."""
    engine = get_engine()
    with engine.connect() as conn:
        # Check column names
        cols_res = conn.execute(text("""
            SELECT column_name, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'news_articles';
        """)).fetchall()
        cols = {r[0]: r[1] for r in cols_res}

        required_cols = [
            "id", "title", "description", "content", "url",
            "normalized_url", "content_hash", "source_name", "source_type",
            "author", "published_at", "category", "category_id",
            "image_url", "collected_at", "created_at", "updated_at",
        ]
        for c in required_cols:
            assert c in cols, f"Column '{c}' missing from news_articles table"

        # Check required columns are NOT NULL
        assert cols["title"] == "NO"
        assert cols["content"] == "NO"
        assert cols["url"] == "NO"
        assert cols["normalized_url"] == "NO"
        assert cols["content_hash"] == "NO"
        assert cols["category"] == "NO"
        assert cols["category_id"] == "NO"
        assert cols["collected_at"] == "NO"


def test_invalid_category_check_constraint(clean_knowledge_db):
    """Verify database-level check constraint rejects non-canonical category."""
    with get_db_session() as session:
        cat = CategoryRepository.get_by_name(session, "Tech")
        # Attempt to insert article with invalid category 'NonExistentCategory'
        article = NewsArticle(
            title="Sports headline",
            content="Sports content body...",
            url="https://example.com/test-sports-1",
            normalized_url="https://example.com/test-sports-1",
            content_hash="dummy_hash_12345",
            source_type="rss",
            category="NonExistentCategory",  # Invalid category
            category_id=cat.id,
            collected_at=text("now()"),
        )
        session.add(article)
        with pytest.raises(IntegrityError) as exc_info:
            session.flush()
        session.rollback()
        assert "ck_news_articles_valid_category" in str(exc_info.value).lower()
