"""Tests for backend payload slimming, unified feed caching, and HTTP Cache-Control headers."""
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.database.connection.session import Base, get_db
from backend.database.models.category import Category
from backend.database.models.news_article import NewsArticle
from backend.main import app
from backend.pipeline.router import clear_dashboard_cache


@pytest.fixture
def sqlite_client(monkeypatch):
    """FastAPI TestClient backed by an isolated in-memory SQLite database."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Deduplicate any duplicate index names across metadata tables for SQLite compatibility
    for table in Base.metadata.tables.values():
        seen_idx = set()
        for idx in list(table.indexes):
            if idx.name in seen_idx:
                table.indexes.discard(idx)
            else:
                seen_idx.add(idx.name)

    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    with TestingSession() as sess:
        cat_tech = Category(id=1, code="TECH", name="Tech", slug="tech", is_active=True)
        cat_sports = Category(id=2, code="SPORTS", name="Sports", slug="sports", is_active=True)
        sess.add_all([cat_tech, cat_sports])
        sess.flush()

        long_body = "A" * 2000
        now = datetime.now(timezone.utc)
        sess.add_all(
            [
                NewsArticle(
                    id=101,
                    title="Tech Chip Breakthrough",
                    slug="tech-chip-breakthrough",
                    description=None,
                    content=long_body,
                    url="https://example.com/tech-1",
                    normalized_url="https://example.com/tech-1",
                    content_hash="hash_tech_1",
                    source_name="TechWire",
                    source_type="rss",
                    category="Tech",
                    category_id=1,
                    subcategory="Artificial Intelligence",
                    collected_at=now,
                    created_at=now,
                    updated_at=now,
                ),
                NewsArticle(
                    id=102,
                    title="Cricket Final Highlights",
                    slug="cricket-final-highlights",
                    description="Match summary",
                    content=long_body,
                    url="https://example.com/sports-1",
                    normalized_url="https://example.com/sports-1",
                    content_hash="hash_sports_1",
                    source_name="SportsDesk",
                    source_type="rss",
                    category="Sports",
                    category_id=2,
                    subcategory="Cricket",
                    collected_at=now,
                    created_at=now,
                    updated_at=now,
                ),
            ]
        )
        sess.commit()

    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    # Prevent TestClient startup lifespan from touching remote DB or scheduler
    monkeypatch.setattr("backend.main.init_db", lambda *a, **kw: None)
    app.dependency_overrides[get_db] = override_get_db
    clear_dashboard_cache()
    try:
        client = TestClient(app)
        yield client
    finally:
        app.dependency_overrides.pop(get_db, None)
        clear_dashboard_cache()


def test_pipeline_articles_slim_by_default_and_cache_slicing(sqlite_client):
    """Feed omits full body content by default and serves category/limit slices from warm cache."""
    res_all = sqlite_client.get("/pipeline/articles?limit=150")
    assert res_all.status_code == 200
    assert "max-age=60" in res_all.headers.get("cache-control", "")

    data_all = res_all.json()
    assert data_all["total"] == 2
    for item in data_all["items"]:
        assert item["content"] is None
        assert len(item["content_snippet"]) <= 243

    # Category filter should slice cleanly from unified warm cache
    res_tech = sqlite_client.get("/pipeline/articles?category=Tech&limit=100")
    assert res_tech.status_code == 200
    data_tech = res_tech.json()
    assert data_tech["total"] == 1
    assert data_tech["items"][0]["id"] == 101

    # Opt-in include_content=true returns full body
    res_full = sqlite_client.get("/pipeline/articles?limit=10&include_content=true")
    assert res_full.status_code == 200
    assert len(res_full.json()["items"][0]["content"]) == 2000


def test_metadata_and_overview_cache_headers(sqlite_client):
    """Metadata and overview endpoints emit Cache-Control headers."""
    cat_res = sqlite_client.get("/api/v1/knowledge/categories")
    assert cat_res.status_code == 200
    assert "max-age=300" in cat_res.headers.get("cache-control", "")

    sub_res = sqlite_client.get("/api/v1/knowledge/subcategories?category=Tech")
    assert sub_res.status_code == 200
    assert "max-age=300" in sub_res.headers.get("cache-control", "")

    ov_res = sqlite_client.get("/pipeline/overview")
    assert ov_res.status_code == 200
    assert "max-age=60" in ov_res.headers.get("cache-control", "")
