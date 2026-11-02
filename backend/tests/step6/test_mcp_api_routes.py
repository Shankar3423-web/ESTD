"""Tests for Step 6 MCP FastAPI HTTP endpoints."""
from fastapi.testclient import TestClient
import pytest

from backend.main import app


class TestMCPAPIRoutes:
    """Test REST API endpoints for MCP status, discovery, and query execution."""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_get_mcp_health_endpoint(self, client):
        """Verify GET /api/mcp/health returns HTTP 200 with complete status payload."""
        response = client.get("/api/mcp/health")
        assert response.status_code == 200
        data = response.json()
        assert "overall_status" in data
        assert "postgres" in data
        assert "google_drive" in data
        assert data["postgres"]["state"] == "HEALTHY"
        assert data["google_drive"]["state"] in ("REQUIRES_AUTHENTICATION", "HEALTHY")

    def test_get_postgres_health_endpoint(self, client):
        """Verify GET /api/mcp/postgres/health returns HTTP 200."""
        response = client.get("/api/mcp/postgres/health")
        assert response.status_code == 200
        data = response.json()
        assert data["server_name"] == "postgres"
        assert data["state"] == "HEALTHY"
        assert data["configured"] is True
        assert data["reachable"] is True

    def test_get_google_health_endpoint(self, client):
        """Verify GET /api/mcp/google/health returns HTTP 200 with auth status."""
        response = client.get("/api/mcp/google/health")
        assert response.status_code == 200
        data = response.json()
        assert data["server_name"] == "google_drive"
        assert data["state"] in ("REQUIRES_AUTHENTICATION", "HEALTHY")

    def test_get_mcp_tools_endpoint(self, client):
        """Verify GET /api/mcp/tools returns discovered tool definitions."""
        response = client.get("/api/mcp/tools")
        assert response.status_code == 200
        data = response.json()
        assert "postgres" in data
        assert any(t["name"] == "query" for t in data["postgres"])

    def test_post_postgres_query_success(self, client):
        """Verify POST /api/mcp/postgres/query executes valid query and returns rows."""
        payload = {"sql": "SELECT id, name FROM categories ORDER BY id ASC LIMIT 2;"}
        response = client.post("/api/mcp/postgres/query", json=payload)
        assert response.status_code == 200
        rows = response.json()
        assert len(rows) == 2
        assert rows[0]["name"] == "Tech"

    def test_post_postgres_query_security_rejection(self, client):
        """Verify POST /api/mcp/postgres/query returns HTTP 400 on destructive query."""
        payload = {"sql": "DROP TABLE categories;"}
        response = client.post("/api/mcp/postgres/query", json=payload)
        assert response.status_code == 400
        err = response.json()
        assert "Security violation" in err["detail"]

    def test_post_tools_invoke_endpoint(self, client):
        """Verify POST /api/mcp/tools/invoke executes tool dynamically."""
        payload = {
            "server": "postgres",
            "tool": "query",
            "arguments": {"sql": "SELECT count(*) as count FROM categories;"},
        }
        response = client.post("/api/mcp/tools/invoke", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["server"] == "postgres"
        assert data["tool"] == "query"
