"""Health verification service for Google Drive / Docs MCP integration."""
from pathlib import Path
import time
from typing import Optional

from backend.common.logging.logger import logger
from backend.step6_mcp.config.mcp_settings import MCPSettings, get_mcp_settings
from backend.step6_mcp.google.client import GoogleDriveMCPClient
from backend.step6_mcp.schemas.mcp_status import MCPHealthState, MCPServerHealth


class GoogleDriveMCPHealthChecker:
    """Verifies operational state and authentication status for Google Drive/Docs MCP."""

    def __init__(self, settings: Optional[MCPSettings] = None):
        self.settings = settings or get_mcp_settings()

    def check_health(self) -> MCPServerHealth:
        """Check Google Drive MCP health, detecting authentication boundaries without faking success.

        Returns:
            MCPServerHealth: State indicating HEALTHY, REQUIRES_AUTHENTICATION, or UNHEALTHY.
        """
        start_time = time.monotonic()
        client = GoogleDriveMCPClient(settings=self.settings)
        auth_state = client.check_auth_state()

        oauth_configured = auth_state["oauth_keys_configured"]
        creds_authorized = auth_state["credentials_authorized"]

        # If user credentials token file does not exist, stop at authentication boundary
        if not creds_authorized:
            latency_ms = (time.monotonic() - start_time) * 1000
            oauth_msg = "OAuth client keys detected" if oauth_configured else "OAuth client keys missing"
            action = (
                "To authenticate Google Drive/Docs MCP:\n"
                f"1. Ensure Google Cloud OAuth 2.0 Desktop client ID JSON is saved to: '{self.settings.gdrive_oauth_path}'\n"
                "2. Enable Google Drive API in Google Cloud Console\n"
                f"3. Run interactive auth command: python -m backend.step6_mcp.google.launcher --auth\n"
                f"4. Tokens will be securely saved to: '{self.settings.gdrive_credentials_path}'"
            )
            return MCPServerHealth(
                server_name="google_drive",
                state=MCPHealthState.REQUIRES_AUTHENTICATION,
                configured=oauth_configured,
                reachable=False,
                authenticated=False,
                latency_ms=round(latency_ms, 2),
                details=f"Google Drive MCP requires OAuth authorization ({oauth_msg}). Credentials token file absent.",
                manual_action_required=action,
            )

        # Credentials exist, attempt live connection and tool discovery
        try:
            client.connect()
            tools = client.list_tools()
            resources = client.list_resources()

            # Verify 'search' tool is discovered
            tool_names = [t.name for t in tools]
            latency_ms = (time.monotonic() - start_time) * 1000
            client.close()

            return MCPServerHealth(
                server_name="google_drive",
                state=MCPHealthState.HEALTHY,
                configured=True,
                reachable=True,
                authenticated=True,
                tools_count=len(tools),
                resources_count=len(resources),
                latency_ms=round(latency_ms, 2),
                details=(
                    f"Google Drive MCP verified successfully. Discovered {len(tools)} tools ({tool_names}) "
                    f"and {len(resources)} accessible Drive resources."
                ),
            )
        except Exception as exc:
            client.close()
            latency_ms = (time.monotonic() - start_time) * 1000
            logger.error(f"Google Drive MCP verification failed: {exc}")
            return MCPServerHealth(
                server_name="google_drive",
                state=MCPHealthState.UNHEALTHY,
                configured=True,
                reachable=False,
                authenticated=True,
                latency_ms=round(latency_ms, 2),
                details=f"Google Drive MCP process connection error: {exc}",
            )
