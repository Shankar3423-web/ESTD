"""Test fixtures for Step 5 Knowledge Source test suite."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from backend.database.connection.session import get_db_session, get_engine, init_db
from backend.database.repositories.category_repository import CategoryRepository
from backend.main import app
from backend.step3_content_cleaning.models.cleaned_article import CleanedArticle
from backend.step3_content_cleaning.models.cleaning_enums import CleaningStatus
from backend.step4_duplicate_detection.detectors.exact_content_detector import ExactContentDetector
from backend.step4_duplicate_detection.models.duplicate_record import (
    DetectionScope,
    DuplicateDecision,
    DuplicateReason,
    DuplicateStatus,
)
from backend.step4_duplicate_detection.normalizers.url_normalizer import normalize_url
from backend.step4_duplicate_detection.schemas.duplicate_response import DuplicateCheckResult
from backend.step5_knowledge_source.schemas.article_schemas import ArticleCreateRequest


@pytest.fixture(scope="session", autouse=True)
def setup_test_knowledge_db():
    """Ensure database tables exist and canonical categories are seeded."""
    init_db()
    with get_db_session() as session:
        CategoryRepository.seed_categories(session)


@pytest.fixture
def clean_knowledge_db():
    """Clean test articles before and after each test for pristine isolation without wiping persistent records."""
    engine = get_engine()
    with engine.connect() as conn:
        conn.execute(text("DELETE FROM news_articles WHERE title LIKE 'Test%' OR url LIKE '%example.com%' OR source_name LIKE '%Test%' OR title LIKE 'Quantum%' OR title LIKE 'Next-Gen%' OR title LIKE 'Breakthrough%';"))
        conn.execute(text("DELETE FROM estd_duplicate_index WHERE title LIKE 'Test%' OR url LIKE '%example.com%' OR source_name LIKE '%Test%' OR title LIKE 'Quantum%' OR title LIKE 'Next-Gen%' OR title LIKE 'Breakthrough%';"))
        conn.commit()
    yield
    with engine.connect() as conn:
        conn.execute(text("DELETE FROM news_articles WHERE title LIKE 'Test%' OR url LIKE '%example.com%' OR source_name LIKE '%Test%' OR title LIKE 'Quantum%' OR title LIKE 'Next-Gen%' OR title LIKE 'Breakthrough%';"))
        conn.execute(text("DELETE FROM estd_duplicate_index WHERE title LIKE 'Test%' OR url LIKE '%example.com%' OR source_name LIKE '%Test%' OR title LIKE 'Quantum%' OR title LIKE 'Next-Gen%' OR title LIKE 'Breakthrough%';"))
        conn.commit()


@pytest.fixture
def client():
    """FastAPI TestClient fixture."""
    return TestClient(app)


@pytest.fixture
def sample_ai_article_payload():
    """Payload for creating a valid Artificial Intelligence article."""
    return {
        "title": "Test AI Reasoning Breakthrough Announced",
        "description": "Researchers reveal state-of-the-art neural architecture for formal reasoning.",
        "content": "A team of computer scientists today published landmark benchmark results for deep reasoning systems.",
        "url": "https://example.com/test-ai-reasoning-breakthrough",
        "source_name": "AI Chronicle",
        "source_type": "rss",
        "author": "Dr. Alan Turing",
        "published_at": "2026-10-01T10:00:00Z",
        "category": "Artificial Intelligence",
        "image_url": "https://example.com/images/ai-brain.jpg",
    }


@pytest.fixture
def sample_science_cleaned_article():
    """CleanedArticle instance for Science category."""
    body = "Deep space telescope spectroscopic observations confirm water vapor absorption bands in the atmosphere of exoplanet K2-18b."
    return CleanedArticle(
        title="Test Water Vapor Detected on Habitable Exoplanet",
        description="Spectroscopic data confirms atmospheric moisture.",
        url="https://example.com/test-water-vapor-exoplanet",
        canonical_url="https://example.com/test-water-vapor-exoplanet",
        source_name="Astronomy Today",
        source_type="rss",
        author="Dr. Carl Sagan",
        published_at="2026-10-02T14:30:00Z",
        category="Science",
        collected_at="2026-10-02T14:35:00Z",
        cleaned_content=body,
        content=body,
        cleaning_status=CleaningStatus.SUCCESS,
        cleaned_content_length=len(body),
        original_content_length=len(body),
    )


@pytest.fixture
def sample_step4_unique_result(sample_science_cleaned_article):
    """Step 4 DuplicateCheckResult classified as UNIQUE."""
    norm_url = normalize_url(sample_science_cleaned_article.url)
    c_hash = ExactContentDetector.compute_content_hash(sample_science_cleaned_article.content)
    decision = DuplicateDecision.unique(
        normalized_url=norm_url,
        content_hash=c_hash,
    )
    return DuplicateCheckResult(
        status="unique",
        decision=decision,
        article=sample_science_cleaned_article,
    )


@pytest.fixture
def sample_step4_duplicate_result(sample_science_cleaned_article):
    """Step 4 DuplicateCheckResult classified as DUPLICATE."""
    norm_url = normalize_url(sample_science_cleaned_article.url)
    c_hash = ExactContentDetector.compute_content_hash(sample_science_cleaned_article.content)
    decision = DuplicateDecision.duplicate_by_url(
        normalized_url=norm_url,
        content_hash=c_hash,
        scope=DetectionScope.HISTORICAL,
        matched_id="99",
        matched_title="Existing Published Story",
    )
    return DuplicateCheckResult(
        status="duplicate",
        decision=decision,
        article=sample_science_cleaned_article,
    )
