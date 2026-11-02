"""Shared test fixtures for Step 4 Duplicate Detection test suite."""
import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.database.connection.session import get_db_session, get_engine, init_db
from backend.step3_content_cleaning.models.cleaned_article import CleanedArticle
from backend.step3_content_cleaning.models.cleaning_enums import CleaningStatus
from backend.step4_duplicate_detection.config import DuplicateDetectionConfig
from backend.step4_duplicate_detection.services.duplicate_detection_service import (
    DuplicateDetectionService,
)


@pytest.fixture(scope="session", autouse=True)
def ensure_db_schema():
    """Ensure database schema exists before running any Step 4 tests."""
    init_db()


@pytest.fixture
def db_session():
    """Provide an isolated database session that cleans up created records."""
    with get_db_session() as session:
        yield session
        # Clean up records created during testing
        try:
            session.execute(text("DELETE FROM estd_duplicate_index WHERE url LIKE '%test%' OR title LIKE '%Test%' OR title LIKE '%OpenAI%' OR title LIKE '%Apple%' OR title LIKE '%NASA%';"))
            session.commit()
        except Exception:
            session.rollback()


@pytest.fixture
def clean_db():
    """Truncate the duplicate index table for a completely pristine test environment."""
    engine = get_engine()
    with engine.connect() as conn:
        conn.execute(text("TRUNCATE TABLE estd_duplicate_index RESTART IDENTITY CASCADE;"))
        conn.commit()
    yield
    with engine.connect() as conn:
        conn.execute(text("TRUNCATE TABLE estd_duplicate_index RESTART IDENTITY CASCADE;"))
        conn.commit()


@pytest.fixture
def sample_cleaned_article() -> CleanedArticle:
    """Canonical test CleanedArticle on OpenAI reasoning model."""
    content = (
        "OpenAI released a new reasoning model for software developers today. "
        "The system demonstrates enhanced capabilities across mathematical problem solving, "
        "complex algorithmic code generation, and multi-step logical deduction. "
        "Software engineers can integrate the new model immediately using the standard chat completions API endpoint."
    )
    return CleanedArticle(
        title="OpenAI released a new model for developers",
        description="A new reasoning model designed for developers.",
        url="https://techcrunch.com/2026/10/01/openai-reasoning-model",
        canonical_url="https://techcrunch.com/2026/10/01/openai-reasoning-model",
        source_name="TechCrunch",
        source_type="gnews",
        author="Jane Doe",
        published_at="2026-10-01T10:00:00Z",
        category="Artificial Intelligence",
        collected_at="2026-10-01T10:15:00Z",
        cleaned_content=content,
        content=content,
        cleaning_status=CleaningStatus.SUCCESS,
        cleaned_content_length=len(content),
        original_content_length=len(content),
    )


@pytest.fixture
def sample_exact_duplicate_article(sample_cleaned_article: CleanedArticle) -> CleanedArticle:
    """Exact content duplicate of sample_cleaned_article but with a different publisher URL."""
    return CleanedArticle(
        title="OpenAI Releases New Developer Model",
        description="Developer-focused reasoning system launched.",
        url="https://theverge.com/2026/10/01/openai-developer-reasoning-release",
        canonical_url="https://theverge.com/2026/10/01/openai-developer-reasoning-release",
        source_name="The Verge",
        source_type="rss",
        author="John Smith",
        published_at="2026-10-01T10:30:00Z",
        category="Artificial Intelligence",
        collected_at="2026-10-01T10:35:00Z",
        cleaned_content=sample_cleaned_article.cleaned_content,
        content=sample_cleaned_article.cleaned_content,
        cleaning_status=CleaningStatus.SUCCESS,
        cleaned_content_length=len(sample_cleaned_article.cleaned_content or ""),
        original_content_length=len(sample_cleaned_article.cleaned_content or ""),
    )


@pytest.fixture
def sample_similar_article() -> CleanedArticle:
    """Similar wording duplicate covering the exact same news event."""
    content = (
        "OpenAI released a new reasoning model for software developers today. "
        "The system demonstrates enhanced capabilities across mathematical problem solving, "
        "complex algorithmic code generation, and multi-step logical deduction. "
        "Software engineers can integrate the model immediately using the standard API endpoint."
    )
    return CleanedArticle(
        title="OpenAI launches a new AI model for developers",
        description="New reasoning capabilities launched for developers.",
        url="https://venturebeat.com/2026/10/01/openai-new-dev-model",
        canonical_url="https://venturebeat.com/2026/10/01/openai-new-dev-model",
        source_name="VentureBeat",
        source_type="newsdata",
        author="Alice Johnson",
        published_at="2026-10-01T11:00:00Z",
        category="Artificial Intelligence",
        collected_at="2026-10-01T11:05:00Z",
        cleaned_content=content,
        content=content,
        cleaning_status=CleaningStatus.SUCCESS,
        cleaned_content_length=len(content),
        original_content_length=len(content),
    )


@pytest.fixture
def sample_different_article() -> CleanedArticle:
    """Completely different article on astronomy / science."""
    content = (
        "NASA astronomers have discovered an exoplanet orbiting a nearby red dwarf star. "
        "The planet lies within the habitable zone where liquid water could theoretically exist on the surface. "
        "Spectroscopic observations from the James Webb Space Telescope suggest the presence of atmospheric water vapor."
    )
    return CleanedArticle(
        title="NASA discovered a new habitable exoplanet",
        description="Astronomers identify promising world in nearby star system.",
        url="https://space.com/2026/10/01/nasa-discovers-habitable-exoplanet",
        canonical_url="https://space.com/2026/10/01/nasa-discovers-habitable-exoplanet",
        source_name="Space.com",
        source_type="rss",
        author="Dr. Sagan",
        published_at="2026-10-01T12:00:00Z",
        category="Science",
        collected_at="2026-10-01T12:10:00Z",
        cleaned_content=content,
        content=content,
        cleaning_status=CleaningStatus.SUCCESS,
        cleaned_content_length=len(content),
        original_content_length=len(content),
    )


@pytest.fixture
def sample_related_different_article() -> CleanedArticle:
    """Related-but-different article: same company and topic, but distinctly different event."""
    content = (
        "Apple announces plans for next generation iPhone models arriving late next year. "
        "Supply chain reports suggest that the upcoming devices will feature custom silicon displays, "
        "thinner battery cells, and revised haptic buttons intended for the 2027 product cycle."
    )
    return CleanedArticle(
        title="Apple plans next year iPhone models with redesigned chassis",
        description="Preview of future iPhone roadmap.",
        url="https://9to5mac.com/2026/10/01/apple-future-iphone-plans",
        canonical_url="https://9to5mac.com/2026/10/01/apple-future-iphone-plans",
        source_name="9to5Mac",
        source_type="rss",
        author="Mark Gurman",
        published_at="2026-10-01T14:00:00Z",
        category="Technology",
        collected_at="2026-10-01T14:15:00Z",
        cleaned_content=content,
        content=content,
        cleaning_status=CleaningStatus.SUCCESS,
        cleaned_content_length=len(content),
        original_content_length=len(content),
    )


@pytest.fixture
def duplicate_service() -> DuplicateDetectionService:
    """Default DuplicateDetectionService instance with standard configuration."""
    config = DuplicateDetectionConfig(
        similarity_threshold=0.82,
        persist_unique_articles=False,
        persist_duplicate_records=False,
    )
    return DuplicateDetectionService(config=config)
