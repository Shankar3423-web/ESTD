"""Unit tests for GeminiClient error handling, retries, and security."""
from unittest.mock import MagicMock, patch
import pytest
from pydantic import BaseModel, SecretStr
from google.genai.errors import APIError

from backend.step7_content_generation.client.gemini_client import GeminiClient
from backend.step7_content_generation.config.gemini_settings import GeminiSettings
from backend.step7_content_generation.exceptions import (
    GeminiAuthenticationError,
    GeminiConfigurationError,
    GeminiModelError,
    GeminiRateLimitError,
    GeminiTimeoutError,
    GenerationExecutionError,
)
from backend.step7_content_generation.schemas.generated_news import GeneratedNews


class DummySchema(BaseModel):
    title: str
    summary: str


@pytest.fixture
def mock_settings():
    return GeminiSettings(
        gemini_api_key=SecretStr("AIzaSyFakeKeyForTesting1234567890abcde"),
        gemini_model="gemini-2.5-flash",
        gemini_temperature=0.2,
        gemini_max_retries=1,
        gemini_timeout_seconds=5.0,
    )


def test_settings_secret_masking(mock_settings):
    """Verify that mask_secret removes the real API key and AIza patterns."""
    raw_key = mock_settings.get_gemini_api_key()
    leak_attempt = f"Error communicating with Gemini: key={raw_key} unauthorized"
    sanitized = mock_settings.mask_secret(leak_attempt)
    assert raw_key not in sanitized
    assert "[REDACTED_API_KEY]" in sanitized


def test_client_missing_key_raises_config_error():
    """Verify that initializing client without API key raises GeminiConfigurationError."""
    empty_settings = GeminiSettings(gemini_api_key=None)
    client = GeminiClient(settings=empty_settings)
    with pytest.raises(GeminiConfigurationError):
        client._get_client()


def test_client_successful_generation(mock_settings):
    """Verify successful generation flow with mocked genai Client."""
    mock_genai_client = MagicMock()
    mock_response = MagicMock()
    mock_response.parsed = DummySchema(title="Test Headline", summary="Test Summary")
    mock_genai_client.models.generate_content.return_value = mock_response

    client = GeminiClient(settings=mock_settings, client=mock_genai_client)
    res = client.generate_structured(
        prompt="Test Prompt",
        response_schema=DummySchema,
    )
    assert res.title == "Test Headline"
    assert res.summary == "Test Summary"
    assert mock_genai_client.models.generate_content.call_count == 1


def test_client_authentication_failure_not_retried(mock_settings):
    """Verify that a 401 or 403 APIError raises GeminiAuthenticationError immediately without retrying."""
    mock_genai_client = MagicMock()
    err = APIError(403, "API_KEY_INVALID: Permission Denied")
    mock_genai_client.models.generate_content.side_effect = err

    client = GeminiClient(settings=mock_settings, client=mock_genai_client)
    with pytest.raises(GeminiAuthenticationError):
        client.generate_structured(prompt="Test", response_schema=DummySchema)

    # Must NOT retry auth failures
    assert mock_genai_client.models.generate_content.call_count == 1


def test_client_model_not_found_not_retried(mock_settings):
    """Verify that a 404 APIError raises GeminiModelError immediately without retrying."""
    mock_genai_client = MagicMock()
    err = APIError(404, "models/invalid-model NOT_FOUND")
    mock_genai_client.models.generate_content.side_effect = err

    client = GeminiClient(settings=mock_settings, client=mock_genai_client)
    with pytest.raises(GeminiModelError):
        client.generate_structured(prompt="Test", response_schema=DummySchema)

    assert mock_genai_client.models.generate_content.call_count == 1


def test_client_rate_limit_retries_and_exhausts(mock_settings):
    """Verify that a 429 rate limit is retried up to gemini_max_retries and then raises GeminiRateLimitError."""
    mock_genai_client = MagicMock()
    err = APIError(429, "RESOURCE_EXHAUSTED: Quota exceeded")
    mock_genai_client.models.generate_content.side_effect = err

    client = GeminiClient(settings=mock_settings, client=mock_genai_client)
    with patch("time.sleep"):  # Avoid actual sleep delays in tests
        with pytest.raises(GeminiRateLimitError):
            client.generate_structured(prompt="Test", response_schema=DummySchema)

    # max_retries=1 -> initial attempt (1) + retry (1) = 2 calls
    assert mock_genai_client.models.generate_content.call_count == 2


def test_client_empty_response_raises_execution_error(mock_settings):
    """Verify that an empty response from Gemini raises GenerationExecutionError."""
    mock_genai_client = MagicMock()
    mock_resp = MagicMock()
    mock_resp.parsed = None
    mock_resp.text = ""
    mock_genai_client.models.generate_content.return_value = mock_resp

    client = GeminiClient(settings=mock_settings, client=mock_genai_client)
    with patch("time.sleep"):
        with pytest.raises(GenerationExecutionError):
            client.generate_structured(prompt="Test", response_schema=DummySchema)


def test_client_test_connectivity_success(mock_settings):
    """Verify connectivity ping returns connected status."""
    mock_genai_client = MagicMock()
    mock_resp = MagicMock()
    mock_resp.text = "Pong"
    mock_genai_client.models.generate_content.return_value = mock_resp

    client = GeminiClient(settings=mock_settings, client=mock_genai_client)
    res = client.test_connectivity()
    assert res["status"] == "connected"
    assert res["model"] == "gemini-2.5-flash"
    assert res["response_received"] is True
