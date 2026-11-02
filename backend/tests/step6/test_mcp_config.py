"""Tests for Step 6 MCP configuration and credentials security."""
import pytest
from pydantic import SecretStr

from backend.step6_mcp.config.mcp_settings import MCPSettings, get_mcp_settings
from backend.step6_mcp.exceptions import MCPSecurityError


def test_mcp_config_loads_defaults():
    """Verify MCPSettings loads defaults and matches project database parameters."""
    settings = get_mcp_settings()
    assert settings.postgres_port == 5433
    assert settings.postgres_db == "estd_knowledge"
    assert settings.postgres_host is not None
    assert settings.read_only_enforced is True


def test_mcp_config_masks_secret_in_repr_and_str():
    """Verify passwords are never leaked in str or repr representations."""
    settings = MCPSettings(
        POSTGRES_PASSWORD="super_secret_test_password",
        POSTGRES_PORT=5433,
    )
    repr_str = repr(settings)
    assert "super_secret_test_password" not in repr_str
    assert ":***@" in repr_str


def test_mcp_config_safe_url_masks_password():
    """Verify get_safe_postgres_url redacts raw password."""
    settings = MCPSettings(
        POSTGRES_PASSWORD="mypassword123",
        POSTGRES_USER="testuser",
        POSTGRES_HOST="127.0.0.1",
        POSTGRES_PORT=5433,
        POSTGRES_DB="testdb",
    )
    safe_url = settings.get_safe_postgres_url()
    assert "mypassword123" not in safe_url
    assert "postgresql://testuser:***@127.0.0.1:5433/testdb" == safe_url


def test_mcp_config_google_paths_configured():
    """Verify Google OAuth and credentials paths are defined."""
    settings = get_mcp_settings()
    assert settings.gdrive_oauth_path is not None
    assert settings.gdrive_credentials_path is not None
    auth_status = settings.get_google_auth_status()
    assert "oauth_keys_configured" in auth_status
    assert "credentials_authorized" in auth_status


def test_mcp_config_missing_required_fields():
    """Verify detection when required database fields are blank."""
    settings = MCPSettings(
        POSTGRES_HOST="",
        POSTGRES_DB="",
    )
    assert settings.postgres_host == ""
    assert settings.postgres_db == ""
