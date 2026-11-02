"""Tests for centralized configuration system."""
import pytest
from pydantic import SecretStr

from backend.common.config.settings import Settings
from backend.common.exceptions.custom_exceptions import ConfigurationError


def test_config_loads_keys_correctly():
    """Verify that Settings properly exposes configured API keys via accessors."""
    settings = Settings(
        GNEWS_API_KEY="test_gnews_secret_key",
        NEWSDATA_API_KEY="test_newsdata_secret_key",
    )
    assert settings.get_gnews_api_key() == "test_gnews_secret_key"
    assert settings.get_newsdata_api_key() == "test_newsdata_secret_key"


def test_config_masks_secret_in_str_and_repr():
    """Verify that SecretStr prevents keys from leaking in string or repr outputs."""
    secret = "super_confidential_key_999"
    settings = Settings(
        GNEWS_API_KEY=secret,
        NEWSDATA_API_KEY=secret,
    )
    # The raw secret must not be contained in str(settings) or repr(settings)
    assert secret not in str(settings)
    assert secret not in repr(settings)
    assert secret not in str(settings.gnews_api_key)
    assert "**********" in str(settings.gnews_api_key)


def test_config_missing_gnews_key_raises_error():
    """Verify that attempting to access missing GNews key raises ConfigurationError."""
    settings = Settings(GNEWS_API_KEY="", NEWSDATA_API_KEY="some_key")
    with pytest.raises(ConfigurationError) as exc_info:
        settings.get_gnews_api_key()
    assert "GNews API key is not configured" in str(exc_info.value)
    assert exc_info.value.code == "CONFIGURATION_ERROR"


def test_config_missing_newsdata_key_raises_error():
    """Verify that attempting to access missing NewsData key raises ConfigurationError."""
    settings = Settings(GNEWS_API_KEY="some_key", NEWSDATA_API_KEY="")
    with pytest.raises(ConfigurationError) as exc_info:
        settings.get_newsdata_api_key()
    assert "NewsData.io API key is not configured" in str(exc_info.value)
    assert exc_info.value.code == "CONFIGURATION_ERROR"


def test_config_whitespace_only_key_treated_as_missing():
    """Verify that whitespace-only keys are rejected as unconfigured."""
    settings = Settings(GNEWS_API_KEY="   ", NEWSDATA_API_KEY=" \t ")
    with pytest.raises(ConfigurationError):
        settings.get_gnews_api_key()
    with pytest.raises(ConfigurationError):
        settings.get_newsdata_api_key()
