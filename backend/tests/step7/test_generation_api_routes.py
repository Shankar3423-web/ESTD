"""Tests for Step 7 FastAPI HTTP endpoints."""
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
import pytest

from backend.common.constants.categories import ESTDCategory
from backend.main import app
from backend.step7_content_generation.api.generation_routes import (
    get_client,
    get_gen_service,
    get_mcp_gen_service,
)
from backend.step7_content_generation.schemas.generated_news import GeneratedNews
from backend.step7_content_generation.schemas.generation_request import GenerationResponse


class TestGenerationAPIRoutes:
    """Test REST API endpoints for Step 7 content generation."""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_get_step7_health_endpoint(self, client):
        """Verify GET /step7/health returns HTTP 200 and configuration summary without exposing API key."""
        response = client.get("/step7/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "configuration" in data
        assert data["configuration"]["model"] == "gemini-2.5-flash"
        assert "api_key_configured" in data["configuration"]
        # Absolute security check: API key must NOT be anywhere in response
        raw_text = response.text
        assert "AIza" not in raw_text

    def test_get_eligible_articles_endpoint(self, client):
        """Verify GET /step7/eligible-articles returns eligible articles via MCP."""
        response = client.get("/step7/eligible-articles?limit=5")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        if len(data) > 0:
            first = data[0]
            assert "id" in first
            assert "title" in first
            assert "category" in first
            assert "url" in first

    def test_post_generate_ineligible_article_id(self, client):
        """Verify POST /step7/generate with invalid article ID returns 400."""
        payload = {"article_id": 999999}
        response = client.post("/step7/generate", json=payload)
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert data["detail"]["code"] == "ARTICLE_INELIGIBLE_FOR_GENERATION"

    def test_post_generate_direct_success(self, client):
        """Verify POST /step7/generate/direct returns 200 with generated news."""
        mock_gen_service = MagicMock()
        mock_news = GeneratedNews(
            title="Next-Generation Semiconductor Architecture Unveiled",
            subtitle="New materials allow 1nm precision in extreme ultraviolet lithography",
            category=ESTDCategory.TECH,
            summary="Engineers have demonstrated stable 1nm lithography using novel metal-oxide photoresists.",
            content="A consortium of semiconductor manufacturers has published operational benchmarks for next-generation lithography tools. The findings suggest production readiness ahead of industry roadmap targets, enabling higher transistor density while reducing power leakage.",
            source_name="IEEE Spectrum",
            source_url="https://spectrum.ieee.org/semiconductor-1nm",
        )
        mock_gen_service.generate_news.return_value = mock_news

        app.dependency_overrides[get_gen_service] = lambda: mock_gen_service
        try:
            payload = {
                "title": "Raw Semiconductor Discovery",
                "content": "Engineers have demonstrated stable 1nm lithography using novel metal-oxide photoresists with extreme ultraviolet systems.",
                "category": "Tech",
                "source_name": "IEEE Spectrum",
                "source_url": "https://spectrum.ieee.org/semiconductor-1nm",
            }
            response = client.post("/step7/generate/direct", json=payload)
            assert response.status_code == 200
            data = response.json()
            assert data["title"] == "Next-Generation Semiconductor Architecture Unveiled"
            assert data["category"] == "Tech"
            assert data["source_name"] == "IEEE Spectrum"
        finally:
            app.dependency_overrides.clear()
