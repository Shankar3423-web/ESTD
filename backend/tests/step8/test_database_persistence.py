"""Database tests for GoogleDocumentRecord model and repository."""
from datetime import datetime, timezone
import pytest

from backend.database.models.category import Category
from backend.database.models.google_document_record import DocumentStatus, GoogleDocumentRecord
from backend.database.models.news_article import NewsArticle
from backend.database.repositories.google_document_repository import GoogleDocumentRepository


class TestDatabasePersistence:
    """Test database persistence for GoogleDocumentRecord in PostgreSQL."""

    @pytest.fixture
    def test_session(self, db_session):
        """Prepare test article in the database."""
        cat = db_session.query(Category).filter_by(name="Tech").first()
        article = NewsArticle(
            id=100,
            title="Advanced Semiconductor Breakthrough",
            content="Detailed article content on semiconductors.",
            url="https://example.com/semiconductors",
            normalized_url="example.com/semiconductors",
            content_hash="abc123hash",
            category="Tech",
            category_id=cat.id,
            source_name="TechDaily",
            source_type="rss",
            collected_at=datetime.now(timezone.utc),
        )
        db_session.add(article)
        db_session.commit()
        return db_session

    def test_create_and_retrieve_pending_record(self, test_session):
        """Verify creating a PENDING document record."""
        article = test_session.query(NewsArticle).filter_by(id=100).first()
        record, is_new = GoogleDocumentRepository.create_or_get_pending(
            session=test_session,
            article_id=article.id,
            category="Tech",
            document_title="ESTD - Advanced Semiconductor Breakthrough",
            root_folder_id="root_123",
            category_folder_id="tech_456",
        )
        test_session.commit()

        assert is_new is True
        assert record.id is not None
        assert record.article_id == article.id
        assert record.status == DocumentStatus.PENDING.value
        assert record.attempt_count == 1
        assert record.google_drive_root_folder_id == "root_123"
        assert record.google_drive_category_folder_id == "tech_456"

    def test_idempotent_get_pending_returns_existing(self, test_session):
        """Verify calling create_or_get_pending twice returns the existing record."""
        article = test_session.query(NewsArticle).filter_by(id=100).first()
        rec1, is_new1 = GoogleDocumentRepository.create_or_get_pending(
            session=test_session,
            article_id=article.id,
            category="Tech",
            document_title="ESTD - Advanced Semiconductor Breakthrough",
        )
        test_session.commit()
        assert is_new1 is True

        rec2, is_new2 = GoogleDocumentRepository.create_or_get_pending(
            session=test_session,
            article_id=article.id,
            category="Tech",
            document_title="ESTD - Advanced Semiconductor Breakthrough",
        )
        assert is_new2 is False
        assert rec1.id == rec2.id

    def test_mark_created_transition(self, test_session):
        """Verify transitioning a record from PENDING to CREATED."""
        article = test_session.query(NewsArticle).filter_by(id=100).first()
        record, _ = GoogleDocumentRepository.create_or_get_pending(
            session=test_session,
            article_id=article.id,
            category="Tech",
            document_title="ESTD - Advanced Semiconductor Breakthrough",
        )
        test_session.commit()

        updated = GoogleDocumentRepository.mark_created(
            session=test_session,
            record_id=record.id,
            google_document_id="doc_xyz_789",
            google_document_url="https://docs.google.com/document/d/doc_xyz_789/edit",
        )
        test_session.commit()

        assert updated.status == DocumentStatus.CREATED.value
        assert updated.google_document_id == "doc_xyz_789"
        assert updated.google_document_url == "https://docs.google.com/document/d/doc_xyz_789/edit"
        assert updated.completed_at is not None
        assert updated.last_error is None

    def test_mark_failed_transition(self, test_session):
        """Verify transitioning a record to FAILED with error message."""
        article = test_session.query(NewsArticle).filter_by(id=100).first()
        record, _ = GoogleDocumentRepository.create_or_get_pending(
            session=test_session,
            article_id=article.id,
            category="Tech",
            document_title="ESTD - Advanced Semiconductor Breakthrough",
        )
        test_session.commit()

        failed = GoogleDocumentRepository.mark_failed(
            session=test_session,
            record_id=record.id,
            error_message="Drive API 503 Backend Error",
        )
        test_session.commit()

        assert failed.status == DocumentStatus.FAILED.value
        assert failed.last_error == "Drive API 503 Backend Error"
        assert failed.completed_at is None

    def test_list_records_filtering(self, test_session):
        """Verify filtering records by category and status."""
        article = test_session.query(NewsArticle).filter_by(id=100).first()
        record, _ = GoogleDocumentRepository.create_or_get_pending(
            session=test_session,
            article_id=article.id,
            category="Tech",
            document_title="ESTD - Tech Article",
        )
        GoogleDocumentRepository.mark_created(test_session, record.id, "doc_1", "http://doc1")
        test_session.commit()

        # Query all
        all_recs = GoogleDocumentRepository.list_records(test_session)
        assert len(all_recs) >= 1

        # Query by category
        tech_recs = GoogleDocumentRepository.list_records(test_session, category="Tech")
        assert len(tech_recs) >= 1

        ent_recs = GoogleDocumentRepository.list_records(test_session, category="NonExistentCategory")
        assert len(ent_recs) == 0

        # Query by status
        created_recs = GoogleDocumentRepository.list_records(test_session, status="CREATED")
        assert len(created_recs) >= 1

        failed_recs = GoogleDocumentRepository.list_records(test_session, category="Tech", status="FAILED")
        assert len(failed_recs) == 0
