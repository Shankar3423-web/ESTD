"""Unit tests for Step 7 generation validation and anti-hallucination grounding."""
import pytest

from backend.common.constants.categories import ESTDCategory
from backend.step7_content_generation.exceptions import GenerationValidationError
from backend.step7_content_generation.schemas.generated_news import GeneratedNews
from backend.step7_content_generation.validators.generation_validator import (
    GenerationValidator,
)


@pytest.fixture
def sample_valid_news():
    return GeneratedNews(
        title="European Researchers Deploy Next-Gen Particle Detector",
        subtitle="CERN completes major upgrade to the High-Luminosity Large Hadron Collider",
        category=ESTDCategory.DEVELOPMENTS,
        summary="CERN engineers have installed advanced silicon pixel detectors designed to monitor high-density subatomic collisions.",
        content="The European Organization for Nuclear Research announced the completion of its detector installation phase. The upgraded instrumentation will capture billions of particle tracks per second, providing unprecedented precision in Higgs boson coupling measurements.",
        source_name="CERN Press",
        source_url="https://home.cern/news/detector-upgrade",
    )


def test_validator_accepts_valid_news(sample_valid_news):
    """Verify that a compliant GeneratedNews object passes validation."""
    source_content = (
        "CERN engineers have installed advanced silicon pixel detectors designed to monitor "
        "subatomic collisions with high precision for Higgs boson coupling measurements."
    )
    # Should complete without error
    GenerationValidator.validate_generated_news(
        news=sample_valid_news,
        expected_category="Developments",
        expected_url="https://home.cern/news/detector-upgrade",
        source_content=source_content,
    )


def test_validator_detects_category_mismatch(sample_valid_news):
    """Verify that mismatch between requested category and generated category is caught."""
    with pytest.raises(GenerationValidationError) as exc_info:
        GenerationValidator.validate_generated_news(
            news=sample_valid_news,
            expected_category="Entertainment",  # Expected Entertainment but news is Developments
        )
    assert "Category mismatch" in str(exc_info.value)


def test_validator_detects_url_mismatch(sample_valid_news):
    """Verify that mismatch between source URL and generated URL is caught."""
    with pytest.raises(GenerationValidationError) as exc_info:
        GenerationValidator.validate_generated_news(
            news=sample_valid_news,
            expected_url="https://different-source.org/article",
        )
    assert "Source URL mismatch" in str(exc_info.value)


def test_validator_rejects_invalid_url():
    """Verify that invalid URL formats are rejected."""
    assert GenerationValidator.validate_url("not-a-valid-url") is False
    assert GenerationValidator.validate_url("ftp://unsupported.com") is False
    assert GenerationValidator.validate_url("") is False
    assert GenerationValidator.validate_url("https://valid.example.com/path") is True
    assert GenerationValidator.validate_url("http://insecure.example.com") is True


def test_validator_grounding_failure(sample_valid_news):
    """Verify that generated news completely unrelated to source fails grounding check."""
    completely_unrelated_source = (
        "Local bakery in Minneapolis wins national sourdough competition with whole grain rye loaf. "
        "Judges praised the crumb structure and fermented sourdough hydration level."
    )
    with pytest.raises(GenerationValidationError) as exc_info:
        GenerationValidator.validate_generated_news(
            news=sample_valid_news,
            expected_category="Developments",
            source_content=completely_unrelated_source,
        )
    assert "grounding" in str(exc_info.value).lower()
