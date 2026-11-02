"""Integration and unit tests for Step8Orchestrator."""
from datetime import datetime, timezone
from unittest.mock import MagicMock
import pytest

from backend.common.constants.categories import ESTDCategory
from backend.database.models.category import Category
from backend.database.models.google_document_record import DocumentStatus, GoogleDocumentRecord
from backend.database.models.news_article import NewsArticle
from backend.step7_content_generation.schemas.generated_news import GeneratedNews
from backend.step8_gdrive_output.exceptions import (
    ArticleIneligibleForOutputError,
    DocumentCreationError,
    GoogleDriveAPIError,
    InvalidStep8CategoryError,
)
from backend.step8_gdrive_output.services.folder_resolver import DriveFolderResolver
from backend.step8_gdrive_output.services.gdrive_service import GoogleDriveService
from backend.step8_gdrive_output.services.orchestrator import Step8Orchestrator


class TestStep8Orchestrator:
    """Test full Step 7 -> Step 8 flow, idempotency, failure recovery, and category routing."""

    @pytest.fixture
    def test_session(self, db_session):
        """Seed news articles for testing in PostgreSQL."""
        cat_tech = db_session.query(Category).filter_by(name="Tech").first()
        cat_ent = db_session.query(Category).filter_by(name="Entertainment").first()

        for i in range(101, 130):
            art = NewsArticle(
                id=i,
                title=f"Sample News Article {i}",
                content=f"Detailed body content for article {i} meeting length requirements.",
                url=f"https://example.com/article-{i}",
                normalized_url=f"example.com/article-{i}",
                content_hash=f"hash_art_{i}",
                category="Entertainment" if i % 2 == 0 else "Tech",
                category_id=cat_ent.id if i % 2 == 0 else cat_tech.id,
                source_name="Global Wire",
                source_type="rss",
                collected_at=datetime.now(timezone.utc),
            )
            db_session.add(art)
        db_session.commit()
        return db_session

    @pytest.fixture
    def mock_gdrive_service(self):
        """Mock GoogleDriveService."""
        service = MagicMock(spec=GoogleDriveService)
        service._doc_counter = 0

        def fake_create_folder(name: str, parent_id: str = None):
            return {
                "id": f"folder_{name.replace(' ', '_').lower()}",
                "name": name,
                "webViewLink": f"https://drive.google.com/folders/{name}",
            }

        def fake_get_or_create_folder(name: str, parent_id: str = None):
            return fake_create_folder(name, parent_id)

        def fake_create_doc(title: str, content: str, folder_id: str):
            service._doc_counter += 1
            doc_id = f"gdoc_id_{service._doc_counter}"
            return {
                "id": doc_id,
                "name": title,
                "webViewLink": f"https://docs.google.com/document/d/{doc_id}/edit",
            }

        service.create_folder.side_effect = fake_create_folder
        service.get_or_create_folder.side_effect = fake_get_or_create_folder
        service.create_google_document.side_effect = fake_create_doc
        return service

    @pytest.fixture
    def orchestrator(self, mock_gdrive_service):
        folder_resolver = DriveFolderResolver(gdrive_service=mock_gdrive_service)
        return Step8Orchestrator(
            gdrive_service=mock_gdrive_service,
            folder_resolver=folder_resolver,
        )

    def _sample_news(self, category=ESTDCategory.TECH, title="Test Headline"):
        return GeneratedNews(
            title=title,
            subtitle="Context subtitle",
            category=category,
            summary="A concise summary of key developments.",
            content=(
                "Comprehensive body content explaining the announcement in full technical detail, "
                "synthesizing the latest benchmarks and outlining future milestones for industry adoption."
            ),
            source_name="Tech Times",
            source_url="https://techtimes.com/sample",
            generated_at=datetime.now(timezone.utc),
        )

    def test_process_approved_content_success(self, orchestrator, test_session, mock_gdrive_service):
        """Verify processing validated GeneratedNews creates document and saves reference."""
        news = self._sample_news(category=ESTDCategory.TECH, title="New LLM Architecture Unveiled")

        resp = orchestrator.process_approved_content(
            news=news,
            article_id=101,
            session=test_session,
        )

        assert resp.success is True
        assert resp.status == DocumentStatus.CREATED.value
        assert resp.article_id == 101
        assert resp.data is not None
        assert resp.data.google_document_id == "gdoc_id_1"
        assert resp.data.google_document_url == "https://docs.google.com/document/d/gdoc_id_1/edit"
        assert resp.data.category == "Tech"
        assert resp.data.document_title == "ESTD - New LLM Architecture Unveiled"
        assert resp.is_duplicate_prevented is False

        # Verify Google Drive service was called once
        assert mock_gdrive_service.create_google_document.call_count == 1

        # Verify database record
        record = test_session.query(GoogleDocumentRecord).filter_by(article_id=101).first()
        assert record is not None
        assert record.status == DocumentStatus.CREATED.value
        assert record.google_document_id == "gdoc_id_1"

    def test_idempotency_prevents_duplicate_documents(self, orchestrator, test_session, mock_gdrive_service):
        """Verify calling process_approved_content twice for the same article does NOT create a second document."""
        news = self._sample_news(title="Idempotency Article")

        # Run 1: Document is created
        resp1 = orchestrator.process_approved_content(news=news, article_id=102, session=test_session)
        assert resp1.success is True
        assert resp1.is_duplicate_prevented is False
        assert mock_gdrive_service.create_google_document.call_count == 1

        # Run 2: Exact same article is submitted again
        resp2 = orchestrator.process_approved_content(news=news, article_id=102, session=test_session)
        assert resp2.success is True
        assert resp2.is_duplicate_prevented is True
        assert resp2.data.google_document_id == resp1.data.google_document_id

        # Crucial check: Google Drive was NOT called again! (Call count remains 1)
        assert mock_gdrive_service.create_google_document.call_count == 1

    def test_all_five_categories_routed_to_correct_folders(self, orchestrator, test_session, mock_gdrive_service):
        """Verify every one of the 5 finalized ESTD categories routes to its specific category folder."""
        categories = [
            (ESTDCategory.ENTERTAINMENT, "Entertainment", "folder_entertainment"),
            (ESTDCategory.SPORTS, "Sports", "folder_sports"),
            (ESTDCategory.TECH, "Tech", "folder_tech"),
            (ESTDCategory.DEVELOPMENTS, "Developments", "folder_developments"),
            (ESTDCategory.BUSINESS_FINANCE, "Business & Finance", "folder_business_&_finance"),
        ]

        for i, (cat_enum, expected_name, expected_folder_id) in enumerate(categories, start=110):
            news = self._sample_news(category=cat_enum, title=f"Report on {expected_name}")
            resp = orchestrator.process_approved_content(news=news, article_id=i, session=test_session)

            assert resp.success is True
            assert resp.data.category == expected_name
            assert resp.data.google_drive_category_folder_id == expected_folder_id

            # Verify the call to create_google_document specified the exact folder_id
            last_call_args = mock_gdrive_service.create_google_document.call_args[1]
            assert last_call_args["folder_id"] == expected_folder_id

    def test_failure_handling_and_recovery(self, orchestrator, test_session, mock_gdrive_service):
        """Verify failed Drive upload records FAILED in DB and successful retry transitions to CREATED."""
        news = self._sample_news(title="Network Failure Test")

        # Simulate Drive failure
        mock_gdrive_service.create_google_document.side_effect = GoogleDriveAPIError(
            "create_document", "503 Service Unavailable", 503
        )

        with pytest.raises(DocumentCreationError):
            orchestrator.process_approved_content(news=news, article_id=103, session=test_session)

        # Record in database must exist in FAILED state
        record = test_session.query(GoogleDocumentRecord).filter_by(article_id=103).first()
        assert record is not None
        assert record.status == DocumentStatus.FAILED.value
        assert "503 Service Unavailable" in record.last_error

        # Now simulate Drive recovery
        mock_gdrive_service.create_google_document.side_effect = lambda title, content, folder_id: {
            "id": "recovered_doc_id",
            "name": title,
            "webViewLink": "https://docs.google.com/document/d/recovered_doc_id/edit",
        }

        # Retry processing
        resp = orchestrator.process_approved_content(
            news=news, article_id=103, session=test_session, force_recreate=False
        )

        assert resp.success is True
        assert resp.status == DocumentStatus.CREATED.value
        assert resp.data.google_document_id == "recovered_doc_id"

        # Check DB updated
        test_session.refresh(record)
        assert record.status == DocumentStatus.CREATED.value
        assert record.last_error is None

    def test_ineligible_article_rejected(self, orchestrator, test_session):
        """Verify invalid article content is rejected safely."""
        with pytest.raises(ArticleIneligibleForOutputError):
            orchestrator.process_approved_content(news=None, article_id=99, session=test_session)
