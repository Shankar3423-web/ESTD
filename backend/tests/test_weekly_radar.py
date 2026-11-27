"""Unit and integration tests for Step 10 Dynamic Weekly Radar."""
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.database.connection.session import Base, get_db
from backend.database.models.category import Category
from backend.database.models.news_article import NewsArticle
from backend.database.models.radar_drop import RadarDrop
from backend.main import app
from backend.step10_weekly_radar.services.radar_service import (
    ExtractedRadarItem,
    RadarExtractionOutput,
    RadarService,
    clear_radar_cache,
)


@pytest.fixture
def radar_test_env(monkeypatch):
    """Isolated SQLite DB + FastAPI TestClient for Weekly Radar tests."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    for table in Base.metadata.tables.values():
        seen_idx = set()
        for idx in list(table.indexes):
            if idx.name in seen_idx:
                table.indexes.discard(idx)
            else:
                seen_idx.add(idx.name)

    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    now = datetime.now(timezone.utc)
    with TestingSession() as sess:
        sess.add_all(
            [
                Category(id=1, code="TECH", name="Tech", slug="tech", is_active=True),
                Category(id=2, code="ENT", name="Entertainment", slug="entertainment", is_active=True),
                Category(id=3, code="SPORTS", name="Sports", slug="sports", is_active=True),
                Category(id=4, code="DEV", name="Developments", slug="developments", is_active=True),
                Category(id=5, code="BIZ_FIN", name="Business & Finance", slug="business-finance", is_active=True),
            ]
        )
        sess.flush()

        sess.add_all(
            [
                NewsArticle(
                    id=1,
                    title="Next-Gen AI Developer Summit Scheduled For Tomorrow",
                    description="Major AI labs will unveil new multimodal tooling tomorrow at the annual summit.",
                    content="Full details on upcoming AI developer releases scheduled this week.",
                    url="https://example.com/ai-summit",
                    normalized_url="https://example.com/ai-summit",
                    content_hash="hash_radar_1",
                    source_name="TechWire",
                    source_type="rss",
                    category="Tech",
                    category_id=1,
                    subcategory="Artificial Intelligence",
                    published_at=now,
                    collected_at=now,
                    created_at=now,
                    updated_at=now,
                ),
                NewsArticle(
                    id=2,
                    title="Championship T20 Final Clash Set For This Weekend",
                    description="Top two cricket franchises prepare for Sunday's title decider.",
                    content="High-stakes weekend cricket match expected to draw record viewership.",
                    url="https://example.com/t20-final",
                    normalized_url="https://example.com/t20-final",
                    content_hash="hash_radar_2",
                    source_name="SportsDesk",
                    source_type="rss",
                    category="Sports",
                    category_id=3,
                    subcategory="Cricket",
                    published_at=now,
                    collected_at=now,
                    created_at=now,
                    updated_at=now,
                ),
                NewsArticle(
                    id=3,
                    title="Global Streaming Slate Premieres New Sci-Fi Series Friday",
                    description="Flagship sci-fi original drops globally this Friday evening.",
                    content="Streaming networks prepare major weekend releases.",
                    url="https://example.com/ott-drop",
                    normalized_url="https://example.com/ott-drop",
                    content_hash="hash_radar_3",
                    source_name="VarietyWire",
                    source_type="rss",
                    category="Entertainment",
                    category_id=2,
                    subcategory="TV & OTT",
                    published_at=now,
                    collected_at=now,
                    created_at=now,
                    updated_at=now,
                ),
                NewsArticle(
                    id=4,
                    title="Central Bank Policy Rate Decision Expected Next Week",
                    description="Markets watch benchmark interest rate commentary next week.",
                    content="Quarterly corporate earnings and central bank rate outlook.",
                    url="https://example.com/rate-decision",
                    normalized_url="https://example.com/rate-decision",
                    content_hash="hash_radar_4",
                    source_name="MarketPulse",
                    source_type="rss",
                    category="Business & Finance",
                    category_id=5,
                    subcategory="Financial Markets & Banking",
                    published_at=now,
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

    monkeypatch.setattr("backend.main.init_db", lambda *a, **kw: None)
    app.dependency_overrides[get_db] = override_get_db
    clear_radar_cache()

    try:
        yield TestClient(app), TestingSession
    finally:
        app.dependency_overrides.pop(get_db, None)
        clear_radar_cache()


def test_radar_drop_relative_date_formatting():
    """RadarDrop.to_dict dynamically computes Today, Tomorrow, In 2 Days, Next Week, and Past."""
    ref_now = datetime(2026, 11, 27, 10, 0, 0, tzinfo=timezone.utc)  # Friday

    drop_today_future = RadarDrop(
        id=1,
        drop_key="k1",
        title="Today Future",
        description="Desc",
        category="Tech",
        tag="Launch",
        event_date=datetime(2026, 11, 27, 16, 0, 0, tzinfo=timezone.utc),
    )
    assert drop_today_future.to_dict(ref_now)["relative_time"] == "Dropping Today"
    assert drop_today_future.to_dict(ref_now)["status_urgency"] == "urgent"

    drop_today_live = RadarDrop(
        id=2,
        drop_key="k2",
        title="Today Live",
        description="Desc",
        category="Tech",
        tag="Launch",
        event_date=datetime(2026, 11, 27, 8, 0, 0, tzinfo=timezone.utc),
    )
    assert drop_today_live.to_dict(ref_now)["relative_time"] == "Live Today"

    drop_tomorrow = RadarDrop(
        id=3,
        drop_key="k3",
        title="Tomorrow",
        description="Desc",
        category="Sports",
        tag="Match",
        event_date=datetime(2026, 11, 28, 15, 0, 0, tzinfo=timezone.utc),
    )
    assert drop_tomorrow.to_dict(ref_now)["relative_time"] == "Tomorrow"

    drop_in_2_days = RadarDrop(
        id=4,
        drop_key="k4",
        title="In 2 Days",
        description="Desc",
        category="Entertainment",
        tag="OTT",
        event_date=datetime(2026, 11, 29, 15, 0, 0, tzinfo=timezone.utc),
    )
    assert drop_in_2_days.to_dict(ref_now)["relative_time"] == "In 2 Days"

    drop_past = RadarDrop(
        id=5,
        drop_key="k5",
        title="Yesterday",
        description="Desc",
        category="Tech",
        tag="Old",
        event_date=datetime(2026, 11, 26, 15, 0, 0, tzinfo=timezone.utc),
    )
    assert drop_past.to_dict(ref_now)["relative_time"] == "Past"


def test_radar_auto_extracts_with_gemini_and_filters_past(radar_test_env, monkeypatch):
    """GET /api/v1/radar/drops extracts events via Gemini, grounds source metadata, and drops past dates."""
    client, TestingSession = radar_test_env
    now = datetime.now(timezone.utc)
    tomorrow_iso = (now + timedelta(days=1)).strftime("%Y-%m-%dT14:00:00Z")
    in_3_days_iso = (now + timedelta(days=3)).strftime("%Y-%m-%dT18:00:00Z")
    past_iso = (now - timedelta(days=5)).strftime("%Y-%m-%dT12:00:00Z")

    mock_gemini = MagicMock()
    mock_gemini.generate_structured.return_value = RadarExtractionOutput(
        items=[
            ExtractedRadarItem(
                title="AI Developer Summit Multimodal Launch",
                description="Major AI labs unveil multimodal developer APIs at tomorrow's summit.",
                category="Tech",
                tag="Product Launch",
                event_date_iso=tomorrow_iso,
                source_article_id=1,
                confidence=94,
            ),
            ExtractedRadarItem(
                title="Central Bank Benchmark Rate Briefing",
                description="Policy committee delivers benchmark interest rate commentary next week.",
                category="Business & Finance",
                tag="Market Watch",
                event_date_iso=in_3_days_iso,
                source_article_id=4,
                confidence=90,
            ),
            ExtractedRadarItem(
                title="Expired Past Event Should Be Ignored",
                description="Old news from last week.",
                category="Sports",
                tag="Past",
                event_date_iso=past_iso,
                source_article_id=2,
                confidence=80,
            ),
        ]
    )

    monkeypatch.setattr(
        "backend.step10_weekly_radar.apis.radar_routes._radar_service",
        RadarService(gemini_client=mock_gemini),
    )

    res = client.get("/api/v1/radar/drops")
    assert res.status_code == 200
    body = res.json()

    # Gemini returned 2 valid future items + heuristic filled remaining 2 categories = 4 total
    assert body["total"] >= 2
    titles = [item["title"] for item in body["items"]]
    assert "AI Developer Summit Multimodal Launch" in titles
    assert "Expired Past Event Should Be Ignored" not in titles

    ai_item = next(i for i in body["items"] if i["title"] == "AI Developer Summit Multimodal Launch")
    assert ai_item["source_name"] == "TechWire"
    assert ai_item["source_article_id"] == 1
    assert ai_item["relative_time"] == "Tomorrow"

    # Category filter works
    res_tech = client.get("/api/v1/radar/drops?category=Tech")
    assert res_tech.status_code == 200
    assert all(i["category"] == "Tech" for i in res_tech.json()["items"])


def test_radar_heuristic_fallback_when_gemini_unavailable(radar_test_env, monkeypatch):
    """If Gemini fails, RadarService gracefully falls back to deterministic extraction from NewsArticle rows."""
    client, _ = radar_test_env

    broken_gemini = MagicMock()
    broken_gemini.generate_structured.side_effect = RuntimeError("Simulated Gemini outage")

    monkeypatch.setattr(
        "backend.step10_weekly_radar.apis.radar_routes._radar_service",
        RadarService(gemini_client=broken_gemini),
    )

    res = client.post("/api/v1/radar/refresh?force=true")
    assert res.status_code == 200
    body = res.json()
    assert body["refreshed"] is True
    assert body["mode"] == "heuristic_fallback"
    assert body["total"] == 4
    categories = {item["category"] for item in body["items"]}
    assert {"Tech", "Sports", "Entertainment", "Business & Finance"}.issubset(categories)
