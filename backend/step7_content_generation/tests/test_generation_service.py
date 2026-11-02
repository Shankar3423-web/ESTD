"""Unit tests for GenerationService and prompt assembly."""
from unittest.mock import MagicMock
import pytest

from backend.common.constants.categories import ESTDCategory
from backend.step7_content_generation.prompts.news_generation_prompt import (
    build_news_generation_prompt,
)
from backend.step7_content_generation.schemas.generated_news import GeneratedNews
from backend.step7_content_generation.services.generation_service import (
    GenerationService,
)


def test_build_news_generation_prompt_constraints():
    """Verify that the centralized prompt includes all required anti-hallucination and formatting directives."""
    prompt = build_news_generation_prompt(
        title="OpenAI Releases New Frontier Model",
        content="OpenAI today announced the availability of their latest reasoning system designed for mathematics and coding.",
        category="Artificial Intelligence",
        source_name="VentureBeat",
        source_url="https://venturebeat.com/ai/new-model",
        author="John Doe",
        published_at="2026-10-05T12:00:00Z",
        description="A major AI model release.",
        custom_instructions="Highlight enterprise safety guardrails.",
    )

    # Core constraint checks
    assert "ZERO HALLUCINATION" in prompt
    assert "STRICT SOURCE GROUNDING" in prompt
    assert "Artificial Intelligence" in prompt
    assert "VentureBeat" in prompt
    assert "https://venturebeat.com/ai/new-model" in prompt
    assert "Highlight enterprise safety guardrails" in prompt
    assert "DO NOT invent people" in prompt
    assert "DO NOT fabricate statistics" in prompt


def test_generation_service_orchestration():
    """Verify GenerationService coordinates prompt creation, client call, and validation."""
    mock_client = MagicMock()
    mock_validator = MagicMock()

    generated_mock = GeneratedNews(
        title="Synthesized Headline of Deep Learning Progress",
        category=ESTDCategory.TECH,
        summary="A comprehensive summary of recent advancements in reasoning architectures.",
        content="Researchers have detailed novel neural architectures that leverage test-time compute to solve complex combinatorial proofs. The model demonstrated substantial improvements across standardized benchmarks while maintaining stability.",
        source_name="MIT Tech Review",
        source_url="https://technologyreview.com/story-123",
    )
    mock_client.generate_structured.return_value = generated_mock

    service = GenerationService(client=mock_client, validator=mock_validator)

    result = service.generate_news(
        title="Raw Input Headline",
        content="Raw body content discussing deep learning progress with test-time compute.",
        category="Tech",
        source_name="MIT Tech Review",
        source_url="https://technologyreview.com/story-123",
    )

    assert result.title == "Synthesized Headline of Deep Learning Progress"
    assert result.category == "Tech"
    assert mock_client.generate_structured.call_count == 1
    assert mock_validator.validate_generated_news.call_count == 1
