"""Unit and integration tests for Step 9 Multi-Angle Video Rail."""
import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.step9_video_rail.services.video_service import (
    clean_headline_for_search,
    get_cached_video_rail,
    resolve_story_video_rail,
    search_youtube_videos,
    CANONICAL_ROLES,
)


@pytest.fixture
def client():
    return TestClient(app)


def test_clean_headline_for_search():
    """Verify that editorial noise and publisher markers are cleanly stripped."""
    raw1 = "EXCLUSIVE: 5 Tech Stocks to Watch in 2027: AI, Semiconductors - The Indian Express"
    clean1 = clean_headline_for_search(raw1)
    assert "EXCLUSIVE" not in clean1
    assert "The Indian Express" not in clean1
    assert "5 Tech Stocks to Watch in 2027" in clean1

    raw2 = "WATCH: Why Indian football federation could receive Rs 237 crore from FIFA | The Hindu"
    clean2 = clean_headline_for_search(raw2)
    assert "WATCH" not in clean2
    assert "The Hindu" not in clean2
    assert "Indian football federation" in clean2


def test_resolve_story_video_rail_structure():
    """Verify that resolving video rail produces 5 canonical perspectives without dummy placeholders."""
    rail = resolve_story_video_rail(
        article_id=99991,
        title="5 Tech Stocks to Watch in 2027: AI, Semiconductors and Quantum Computing",
        category="Tech",
        subcategory="Emerging Tech & Semiconductors",
        source_name="entARABI",
        force_refresh=True,
    )

    assert len(rail) == 5
    roles = [p["role"] for p in rail]
    assert roles == CANONICAL_ROLES

    # Verify no hardcoded Rick Astley or Fireplace dummy video IDs exist
    banned_ids = ["dQw4w9WgXcQ", "L_LUpnjgPso", "aircAruvnKk", "M7lc1UVf-VE", "jNQXAC9IVRw"]
    for p in rail:
        assert p["videoId"] not in banned_ids, f"Found banned placeholder video ID: {p['videoId']}"
        assert p["embedUrl"], "Every perspective must have a valid embedUrl"
        assert p["title"], "Every perspective must have a title"
        assert p["duration"], "Every perspective must have duration"
        assert p["summary"], "Every perspective must have summary"
        assert p["thumbnail"], "Every perspective must have a thumbnail"


def test_video_rail_caching():
    """Verify that video rails are cached in memory for sub-millisecond retrieval."""
    rail1 = resolve_story_video_rail(
        article_id=99992,
        title="Sensex down 500 points today: Market update",
        category="Business & Finance",
        subcategory="Financial Markets & Banking",
        source_name="Moneycontrol",
        force_refresh=True,
    )
    cached = get_cached_video_rail(99992)
    assert cached is not None
    assert len(cached) == 5
    assert cached[0]["role"] == "Official"


def test_api_video_story_endpoint(client):
    """Test GET /api/v1/videos/story/{article_id} endpoint."""
    response = client.get("/api/v1/videos/story/18")
    assert response.status_code == 200
    data = response.json()
    assert data["article_id"] == 18
    assert data["total"] == 5
    assert len(data["video_rail"]) == 5
    assert data["video_rail"][0]["role"] == "Official"
    assert data["video_rail"][1]["role"] == "Broadcast"
    assert data["video_rail"][2]["role"] == "Analysis"
    assert data["video_rail"][3]["role"] == "Creator"
    assert data["video_rail"][4]["role"] == "Fan"


def test_api_video_search_endpoint(client):
    """Test GET /api/v1/videos/search dynamic query endpoint."""
    response = client.get("/api/v1/videos/search?query=AI+Tech+Stocks+2027&limit=3")
    assert response.status_code == 200
    data = response.json()
    assert "query" in data
    assert "items" in data
    assert len(data["items"]) <= 3
