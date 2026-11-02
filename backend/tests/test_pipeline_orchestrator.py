"""Unit tests for the Pipeline Orchestrator and Dashboard API endpoints."""
import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.pipeline.models import PipelineJobStatus, PipelineMetrics
from backend.pipeline.orchestrator import pipeline_orchestrator


@pytest.fixture
def client():
    """FastAPI TestClient fixture."""
    return TestClient(app)


def test_pipeline_status_endpoint(client):
    """Verify /pipeline/status returns health and runner state."""
    response = client.get("/pipeline/status")
    assert response.status_code == 200
    data = response.json()
    assert "is_running" in data
    assert isinstance(data["is_running"], bool)


def test_pipeline_overview_endpoint(client):
    """Verify /pipeline/overview returns health of all subsystems."""
    response = client.get("/pipeline/overview")
    assert response.status_code == 200
    data = response.json()
    assert "postgres" in data
    assert "mcp" in data
    assert "gemini" in data
    assert "google_drive" in data
    assert data["postgres"]["database_name"] == "estd_knowledge"
    assert data["google_drive"]["root_folder"] == "ESTD CONTENT"
    assert len(data["google_drive"]["categories"]) == 5


def test_pipeline_articles_endpoint(client):
    """Verify /pipeline/articles returns dashboard-compatible articles."""
    response = client.get("/pipeline/articles")
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "items" in data
    assert isinstance(data["items"], list)


def test_pipeline_jobs_not_found(client):
    """Verify requesting non-existent job ID returns 404."""
    response = client.get("/pipeline/jobs/nonexistent-id")
    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "JOB_NOT_FOUND"


def test_pipeline_concurrent_run_rejection(client, monkeypatch):
    """Verify concurrent pipeline execution attempts return 409 Conflict."""
    # Temporarily simulate an active running job
    monkeypatch.setattr(pipeline_orchestrator, "is_running", lambda: True)
    monkeypatch.setattr(pipeline_orchestrator, "active_job_id", "job-test-active")

    response = client.post("/pipeline/run", json={"target_per_category": 1})
    assert response.status_code == 409
    data = response.json()
    assert data["detail"]["code"] == "PIPELINE_ALREADY_RUNNING"
