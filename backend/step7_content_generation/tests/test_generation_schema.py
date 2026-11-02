"""Unit tests for Step 7 Pydantic schemas."""
from datetime import datetime, timezone
import pytest
from pydantic import ValidationError

from backend.common.constants.categories import ESTDCategory
from backend.step7_content_generation.schemas.generated_news import GeneratedNews
from backend.step7_content_generation.schemas.generation_request import (
    ArticleGenerationRequest,
    DirectGenerationRequest,
    EligibleArticleSummary,
    GenerationResponse,
)


def test_valid_generated_news_schema():
    """Verify that a complete, valid GeneratedNews model instantiates successfully."""
    news = GeneratedNews(
        title="Breakthrough in Quantum Computing Architecture Announced",
        subtitle="Researchers achieve record coherence times using topological qubits",
        category=ESTDCategory.TECH,
        summary="A international consortium of physicists has demonstrated a resilient topological quantum processor. The development promises fault-tolerant computing for cryptography and simulation.",
        content="In a landmark paper published this week, researchers demonstrated scalable quantum error correction using Majorana zero modes. The architecture sustained coherence ten times longer than prior systems. The breakthrough overcomes physical decoherence obstacles that have challenged commercial quantum development.",
        source_name="MIT Technology Review",
        source_url="https://technologyreview.com/quantum-leap",
        generated_at=datetime.now(timezone.utc),
    )
    assert news.title.startswith("Breakthrough in Quantum")
    assert news.category == "Tech"
    assert news.source_name == "MIT Technology Review"
    assert "https://technologyreview.com" in news.source_url
    assert len(news.content) >= 100
    assert len(news.summary) >= 20


def test_generated_news_missing_title():
    """Verify that omitting title raises ValidationError."""
    with pytest.raises(ValidationError):
        GeneratedNews(
            subtitle="Subtitle",
            category=ESTDCategory.BUSINESS_FINANCE,
            summary="A short summary of sufficient length here for validation.",
            content="A substantial body of content that exceeds the one hundred character minimum length threshold specified by the schema.",
            source_name="Financial Times",
            source_url="https://ft.com/story",
        )


def test_generated_news_short_title():
    """Verify that a title with < 5 characters fails validation."""
    with pytest.raises(ValidationError):
        GeneratedNews(
            title="AI",
            category=ESTDCategory.TECH,
            summary="A short summary of sufficient length here for validation.",
            content="A substantial body of content that exceeds the one hundred character minimum length threshold specified by the schema.",
            source_name="AI News",
            source_url="https://ai.example.com",
        )


def test_generated_news_short_content():
    """Verify that content < 100 characters fails validation."""
    with pytest.raises(ValidationError):
        GeneratedNews(
            title="Valid Headline of News",
            category=ESTDCategory.DEVELOPMENTS,
            summary="A short summary of sufficient length here for validation.",
            content="Too short body text.",
            source_name="EdWeek",
            source_url="https://edweek.org/story",
        )


def test_generated_news_invalid_category():
    """Verify that an unsupported category string fails validation."""
    with pytest.raises(ValidationError):
        GeneratedNews(
            title="Sports News Today Headline",
            category="Sports and Gaming",  # Not one of the 5 ESTD categories
            summary="A short summary of sufficient length here for validation.",
            content="A substantial body of content that exceeds the one hundred character minimum length threshold specified by the schema.",
            source_name="Sports Weekly",
            source_url="https://sports.example.com",
        )


def test_generated_news_extra_fields_ignored():
    """Verify that arbitrary extra fields are safely ignored for API schema compatibility."""
    news = GeneratedNews(
        title="Valid Headline of News",
        category=ESTDCategory.DEVELOPMENTS,
        summary="A short summary of sufficient length here for validation.",
        content="A substantial body of content that exceeds the one hundred character minimum length threshold specified by the schema.",
        source_name="Nature",
        source_url="https://nature.com/story",
        unauthorized_field="hallucinated_data",
    )
    assert not hasattr(news, "unauthorized_field")


def test_article_generation_request():
    """Verify ArticleGenerationRequest validation."""
    req = ArticleGenerationRequest(article_id=42, custom_instructions="Focus on economic impacts")
    assert req.article_id == 42
    assert req.custom_instructions == "Focus on economic impacts"

    with pytest.raises(ValidationError):
        ArticleGenerationRequest(article_id=-5)


def test_direct_generation_request():
    """Verify DirectGenerationRequest validation."""
    req = DirectGenerationRequest(
        title="Direct Source Title",
        content="This is a direct source content body that is at least fifty characters long for test purposes.",
        category=ESTDCategory.BUSINESS_FINANCE,
        source_url="https://example.com/biz",
    )
    assert req.category == ESTDCategory.BUSINESS_FINANCE
    assert req.source_name == "Unknown"


def test_generation_response_serialization():
    """Verify GenerationResponse serialization."""
    news = GeneratedNews(
        title="Global Economic Summit Concludes with Historic Agreement",
        category=ESTDCategory.BUSINESS_FINANCE,
        summary="World leaders established new digital taxation standards today at the summit.",
        content="Delegates from sixty nations concluded three days of intense negotiations with a unified communique. The agreement addresses multinational technology taxation and cross-border digital services trade barriers.",
        source_name="Reuters",
        source_url="https://reuters.com/summit",
    )
    resp = GenerationResponse(
        success=True,
        article_id=10,
        data=news,
        generation_time_ms=1250.5,
        model_used="gemini-2.5-flash",
    )
    data_dict = resp.model_dump()
    assert data_dict["success"] is True
    assert data_dict["article_id"] == 10
    assert data_dict["model_used"] == "gemini-2.5-flash"
    assert data_dict["data"]["category"] == "Business & Finance"
