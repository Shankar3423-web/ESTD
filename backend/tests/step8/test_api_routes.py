"""API route tests for Step 8 Google Docs and Drive endpoints."""
from datetime import datetime, timezone
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
import pytest

from backend.database.connection.session import get_db_session
from backend.database.models.category import Category
from backend.database.models.google_document_record import DocumentStatus, GoogleDocumentRecord
from backend.database.models.news_article import NewsArticle
from backend.main import app
from backend.step8_gdrive_output.api.routes import get_gdrive_service
from backend.step8_gdrive_output.services.gdrive_service import GoogleDriveService


class TestStep8APIRoutes:
    """Test Step 8 endpoints mounted on FastAPI."""

    @pytest.fixture
    def test_db_session(self, clean_step8_db):
        """Prepare sample article in PostgreSQL database."""
        with get_db_session() as session:
            cat = session.query(Category).filter_by(name="Tech").first()
            article = NewsArticle(
                id=10,
                title="AI Revolution in Computing",
                content="Detailed content regarding modern compute acceleration.",
                url="https://example.com/ai-compute",
                normalized_url="example.com/ai-compute",
                content_hash="hash10",
                category="Tech",
                category_id=cat.id,
                source_name="AI Gazette",
                source_type="rss",
                collected_at=datetime.now(timezone.utc),
            )
            session.add(article)
            session.commit()

        with get_db_session() as session:
            yield session

    @pytest.fixture
    def mock_gdrive(self):
        mock = MagicMock(spec=GoogleDriveService)
        mock.get_or_create_folder.side_effect = lambda name, parent_id=None: {
            "id": f"folder_{name.replace(' ', '_').lower()}",
            "name": name,
            "webViewLink": f"https://drive.google.com/folders/{name}",
        }
        mock.create_google_document.side_effect = lambda title, content, folder_id: {
            "id": "mock_gdoc_id_999",
            "name": title,
            "webViewLink": "https://docs.google.com/document/d/mock_gdoc_id_999/edit",
        }
        mock.search_files.return_value = [{"id": "f1", "name": "ESTD CONTENT"}]
        return mock

    @pytest.fixture
    def client(self, test_db_session, mock_gdrive):
        def override_get_gdrive():
            return mock_gdrive

        app.dependency_overrides[get_gdrive_service] = override_get_gdrive
        with TestClient(app) as test_client:
            yield test_client
        app.dependency_overrides.clear()

    def test_initialize_folders_endpoint(self, client):
        """Verify POST /step8/initialize-folders returns folder hierarchy."""
        resp = client.post("/step8/initialize-folders")
        assert resp.status_code == 200
        data = resp.json()
        assert data["root_folder"]["name"] == "ESTD CONTENT"
        assert len(data["category_folders"]) == 5
        assert "Entertainment" in data["category_folders"]
        assert "Sports" in data["category_folders"]
        assert "Tech" in data["category_folders"]
        assert "Developments" in data["category_folders"]
        assert "Business & Finance" in data["category_folders"]
        assert data["is_fully_initialized"] is True

    def test_get_folders_endpoint(self, client):
        """Verify GET /step8/folders returns folder hierarchy."""
        resp = client.get("/step8/folders")
        assert resp.status_code == 200
        data = resp.json()
        assert data["root_folder"]["name"] == "ESTD CONTENT"
        assert len(data["category_folders"]) == 5

    def test_process_direct_endpoint(self, client):
        """Verify POST /step8/process-direct processes a GeneratedNews payload."""
        payload = {
            "article_id": 10,
            "news": {
                "title": "Novel Neural Network Architecture",
                "subtitle": "Efficiency gains reach 40% across benchmarks",
                "category": "Tech",
                "summary": "Researchers announced a new architecture reducing parameter count while boosting throughput.",
                "content": "A detailed evaluation of the new model reveals consistent accuracy improvements across standard NLP and multimodal benchmarks, demonstrating significant power savings.",
                "source_name": "Arxiv AI",
                "source_url": "https://arxiv.org/abs/2601.12345",
            },
        }

        resp = client.post("/step8/process-direct", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["status"] == "CREATED"
        assert data["article_id"] == 10
        assert data["data"]["google_document_id"] == "mock_gdoc_id_999"
        assert data["data"]["category"] == "Tech"

    def test_get_document_status_404(self, client):
        """Verify GET /step8/documents/{id} returns 404 for unknown article."""
        resp = client.get("/step8/documents/9999")
        assert resp.status_code == 404
        assert resp.json()["detail"]["code"] == "DOCUMENT_NOT_FOUND"

    def test_get_document_status_found(self, client, test_db_session):
        """Verify GET /step8/documents/{id} returns document metadata when present."""
        record = GoogleDocumentRecord(
            article_id=10,
            category="Tech",
            document_title="ESTD - Test Doc",
            google_document_id="doc_123",
            google_document_url="https://docs.google.com/document/d/doc_123/edit",
            status=DocumentStatus.CREATED.value,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        test_db_session.add(record)
        test_db_session.commit()

        resp = client.get("/step8/documents/10")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["data"]["google_document_id"] == "doc_123"

    def test_health_endpoint(self, client):
        """Verify GET /step8/health returns operational health."""
        resp = client.get("/step8/health")
        assert resp.status_code == 200
        data = resp.json()
        assert "status" in data
