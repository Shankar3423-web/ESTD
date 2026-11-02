"""Tests for Google Drive / Docs MCP client and health verification."""
from unittest.mock import MagicMock, patch
import pytest

from backend.step6_mcp.config.mcp_settings import MCPSettings
from backend.step6_mcp.exceptions import MCPAuthenticationError
from backend.step6_mcp.google.client import GoogleDriveMCPClient
from backend.step6_mcp.google.health import GoogleDriveMCPHealthChecker
from backend.step6_mcp.schemas.mcp_status import MCPHealthState, MCPToolSchema


class TestGoogleDriveMCP:
    """Test Google Drive MCP integration, auth boundary detection, and health checks."""

    @pytest.fixture
    def unauthenticated_settings(self, tmp_path):
        """Settings pointing to non-existent OAuth/credentials paths."""
        return MCPSettings(
            GDRIVE_OAUTH_PATH=str(tmp_path / "nonexistent-oauth.json"),
            GDRIVE_CREDENTIALS_PATH=str(tmp_path / "nonexistent-creds.json"),
        )

    def test_unauthenticated_state_detected(self, unauthenticated_settings):
        """Verify client recognizes unauthenticated state and does not fake credentials."""
        client = GoogleDriveMCPClient(settings=unauthenticated_settings)
        auth_state = client.check_auth_state()

        assert auth_state["oauth_keys_configured"] is False
        assert auth_state["credentials_authorized"] is False
        assert client.is_authenticated() is False

    def test_connect_raises_auth_error_when_unauthenticated(self, unauthenticated_settings):
        """Verify attempting to connect without credentials raises MCPAuthenticationError."""
        client = GoogleDriveMCPClient(settings=unauthenticated_settings)
        with pytest.raises(MCPAuthenticationError) as exc_info:
            client.connect()

        assert exc_info.value.server_name == "google_drive"
        assert exc_info.value.manual_action_required is not None
        assert "python -m backend.step6_mcp.google.launcher --auth" in exc_info.value.manual_action_required

    def test_health_checker_returns_auth_required(self, unauthenticated_settings):
        """Verify health checker returns REQUIRES_AUTHENTICATION and instructions."""
        checker = GoogleDriveMCPHealthChecker(settings=unauthenticated_settings)
        health = checker.check_health()

        assert health.server_name == "google_drive"
        assert health.state == MCPHealthState.REQUIRES_AUTHENTICATION
        assert health.authenticated is False
        assert health.reachable is False
        assert health.manual_action_required is not None
        assert "Google Cloud Console" in health.manual_action_required
        assert "--auth" in health.manual_action_required

    def test_authenticated_mock_client_tool_discovery(self, tmp_path):
        """Verify client discovers 'search' tool when authenticated."""
        creds_file = tmp_path / "mock-creds.json"
        creds_file.write_text('{"token": "mock"}', encoding="utf-8")

        oauth_file = tmp_path / "mock-oauth.json"
        oauth_file.write_text('{"installed": {}}', encoding="utf-8")

        settings = MCPSettings(
            GDRIVE_OAUTH_PATH=str(oauth_file),
            GDRIVE_CREDENTIALS_PATH=str(creds_file),
        )
        client = GoogleDriveMCPClient(settings=settings)
        assert client.is_authenticated() is True

        # Mock JSON-RPC communication
        mock_tools_resp = {
            "jsonrpc": "2.0",
            "id": 2,
            "result": {
                "tools": [
                    {
                        "name": "search",
                        "description": "Search for files in Google Drive",
                        "inputSchema": {"type": "object", "properties": {"query": {"type": "string"}}},
                    }
                ]
            },
        }

        with patch.object(client, "_send_request", return_value=mock_tools_resp):
            client._is_initialized = True
            tools = client.list_tools()
            assert len(tools) == 1
            assert tools[0].name == "search"
            assert "Google Drive" in tools[0].description
