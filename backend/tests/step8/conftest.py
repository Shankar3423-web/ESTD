"""Pytest fixtures for Step 8 tests."""
import pytest
from sqlalchemy import text

from backend.database.connection.session import get_db_session, get_engine


@pytest.fixture
def clean_step8_db():
    """Clean test google_document_records and news_articles without touching historical records."""
    engine = get_engine()
    with engine.connect() as conn:
        conn.execute(text("DELETE FROM google_document_records WHERE article_id BETWEEN 10 AND 200;"))
        conn.execute(text("DELETE FROM news_articles WHERE id BETWEEN 10 AND 200;"))
        conn.commit()
    yield
    with engine.connect() as conn:
        conn.execute(text("DELETE FROM google_document_records WHERE article_id BETWEEN 10 AND 200;"))
        conn.execute(text("DELETE FROM news_articles WHERE id BETWEEN 10 AND 200;"))
        conn.commit()


@pytest.fixture
def db_session(clean_step8_db):
    """Provide a clean PostgreSQL database session for Step 8 tests."""
    with get_db_session() as session:
        yield session
