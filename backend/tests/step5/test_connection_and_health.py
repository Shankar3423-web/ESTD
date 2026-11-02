"""Tests verifying PostgreSQL connectivity, credentials, and database health check."""
import pytest
from sqlalchemy import create_engine, text

from backend.common.config.settings import get_settings
from backend.database.connection.session import check_db_health, get_engine


def test_postgres_connection_success():
    """Verify that backend can connect to PostgreSQL 17 on port 5433 and run SELECT 1."""
    engine = get_engine()
    with engine.connect() as conn:
        res = conn.execute(text("SELECT 1;")).scalar()
        assert res == 1

        db_name = conn.execute(text("SELECT current_database();")).scalar()
        assert db_name == "estd_knowledge"

        version_str = conn.execute(text("SELECT version();")).scalar()
        assert "PostgreSQL" in version_str


def test_db_health_check_function():
    """Verify check_db_health returns expected dictionary with database details."""
    health = check_db_health()
    assert health["status"] == "healthy"
    assert health["database"] == "connected"
    assert health["database_name"] == "estd_knowledge"
    assert health["server_version"] is not None
    assert "PostgreSQL" in health["server_version"]


def test_invalid_credentials_fail_gracefully():
    """Verify that invalid connection parameters raise an error gracefully without crash."""
    bad_url = "postgresql://postgres:wrong_password@localhost:5433/estd_knowledge"
    bad_engine = create_engine(bad_url, connect_args={"connect_timeout": 2})
    with pytest.raises(Exception) as exc_info:
        with bad_engine.connect() as conn:
            conn.execute(text("SELECT 1;"))
    assert exc_info.value is not None


def test_api_health_endpoint(client):
    """Verify GET /api/v1/knowledge/health returns 200 OK with proper payload."""
    response = client.get("/api/v1/knowledge/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"
    assert data["database_name"] == "estd_knowledge"
    assert "PostgreSQL" in data["server_version"]
