"""Health verification service for PostgreSQL MCP integration."""
import time
from typing import Optional

from backend.common.logging.logger import logger
from backend.step6_mcp.config.mcp_settings import MCPSettings, get_mcp_settings
from backend.step6_mcp.postgres.client import PostgresMCPClient
from backend.step6_mcp.schemas.mcp_status import MCPHealthState, MCPServerHealth


class PostgresMCPHealthChecker:
    """Verifies end-to-end health and accessibility of the ESTD PostgreSQL knowledge source via MCP."""

    def __init__(self, settings: Optional[MCPSettings] = None):
        self.settings = settings or get_mcp_settings()

    def check_health(self) -> MCPServerHealth:
        """Execute full verification pipeline:

        1. Configuration validation
        2. MCP server process reachability & handshake
        3. Database connectivity and tool discovery
        4. Safe knowledge-source table read (SELECT from categories)
        """
        start_time = time.monotonic()
        safe_url = self.settings.get_safe_postgres_url()

        # Step 1: Configuration Validation
        if not self.settings.postgres_host or not self.settings.postgres_port or not self.settings.postgres_db:
            return MCPServerHealth(
                server_name="postgres",
                state=MCPHealthState.NOT_CONFIGURED,
                configured=False,
                reachable=False,
                authenticated=False,
                details="PostgreSQL MCP settings are missing required host, port, or database.",
            )

        client = PostgresMCPClient(settings=self.settings)
        try:
            # Step 2 & 3: Connect, Handshake, and Discover Tools/Resources
            client.connect()
            tools = client.list_tools()
            resources = client.list_resources()

            # Verify 'query' tool exists
            tool_names = [t.name for t in tools]
            if "query" not in tool_names:
                client.close()
                latency_ms = (time.monotonic() - start_time) * 1000
                return MCPServerHealth(
                    server_name="postgres",
                    state=MCPHealthState.DEGRADED,
                    configured=True,
                    reachable=True,
                    authenticated=True,
                    tools_count=len(tools),
                    resources_count=len(resources),
                    latency_ms=round(latency_ms, 2),
                    details=f"PostgreSQL MCP connected, but 'query' tool is missing. Available tools: {tool_names}",
                )

            # Step 4: Safe knowledge-source database read
            # Read from canonical categories table
            records = client.execute_query("SELECT id, name, slug FROM categories ORDER BY id ASC LIMIT 5;")
            cat_count = len(records)

            latency_ms = (time.monotonic() - start_time) * 1000
            client.close()

            return MCPServerHealth(
                server_name="postgres",
                state=MCPHealthState.HEALTHY,
                configured=True,
                reachable=True,
                authenticated=True,
                tools_count=len(tools),
                resources_count=len(resources),
                latency_ms=round(latency_ms, 2),
                details=(
                    f"PostgreSQL MCP verified successfully on port {self.settings.postgres_port} ({safe_url}). "
                    f"ESTD knowledge source accessible: retrieved {cat_count} categories via MCP query tool."
                ),
            )
        except Exception as exc:
            client.close()
            latency_ms = (time.monotonic() - start_time) * 1000
            masked_error = client._mask_credentials(str(exc))
            logger.error(f"PostgreSQL MCP health check failed: {masked_error}")
            return MCPServerHealth(
                server_name="postgres",
                state=MCPHealthState.UNHEALTHY,
                configured=True,
                reachable=False,
                authenticated=False,
                latency_ms=round(latency_ms, 2),
                details=f"PostgreSQL MCP verification failed: {masked_error}",
            )
