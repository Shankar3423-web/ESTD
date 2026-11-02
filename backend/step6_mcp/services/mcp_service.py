"""Unified service layer orchestrating Step 6 MCP integrations."""
from datetime import datetime, timezone
import time
from typing import Any, Dict, List, Optional

from backend.common.logging.logger import logger
from backend.step6_mcp.config.mcp_settings import MCPSettings, get_mcp_settings
from backend.step6_mcp.exceptions import (
    MCPAuthenticationError,
    MCPConfigurationError,
    MCPException,
    MCPSecurityError,
    MCPToolExecutionError,
)
from backend.step6_mcp.google.client import GoogleDriveMCPClient
from backend.step6_mcp.google.health import GoogleDriveMCPHealthChecker
from backend.step6_mcp.postgres.client import PostgresMCPClient
from backend.step6_mcp.postgres.health import PostgresMCPHealthChecker
from backend.step6_mcp.schemas.mcp_status import (
    MCPHealthState,
    MCPResourceSchema,
    MCPServerHealth,
    MCPStatusResponse,
    MCPToolCallRequest,
    MCPToolCallResult,
    MCPToolSchema,
)


class MCPService:
    """Service providing unified discovery, health checks, and tool invocations for MCP servers."""

    def __init__(
        self,
        settings: Optional[MCPSettings] = None,
        postgres_health: Optional[PostgresMCPHealthChecker] = None,
        google_health: Optional[GoogleDriveMCPHealthChecker] = None,
    ):
        self.settings = settings or get_mcp_settings()
        self.postgres_health = postgres_health or PostgresMCPHealthChecker(self.settings)
        self.google_health = google_health or GoogleDriveMCPHealthChecker(self.settings)

    def get_health_status(self) -> MCPStatusResponse:
        """Run health verification on all configured MCP servers and compile unified status."""
        logger.info("Executing comprehensive MCP health check...")
        pg_health = self.postgres_health.check_health()
        gd_health = self.google_health.check_health()

        # Compute composite status
        if pg_health.state == MCPHealthState.HEALTHY and gd_health.state == MCPHealthState.HEALTHY:
            overall = "HEALTHY"
        elif pg_health.state == MCPHealthState.HEALTHY and gd_health.state == MCPHealthState.REQUIRES_AUTHENTICATION:
            overall = "PARTIALLY_READY (GOOGLE_AUTH_PENDING)"
        elif pg_health.state == MCPHealthState.HEALTHY:
            overall = "DEGRADED (POSTGRES_READY)"
        else:
            overall = "UNHEALTHY"

        return MCPStatusResponse(
            overall_status=overall,
            postgres=pg_health,
            google_drive=gd_health,
            timestamp=datetime.now(timezone.utc),
        )

    def discover_tools(self) -> Dict[str, List[MCPToolSchema]]:
        """Discover tools exposed across all active MCP servers."""
        tools: Dict[str, List[MCPToolSchema]] = {
            "postgres": [],
            "google_drive": [],
        }

        # PostgreSQL tools
        try:
            with PostgresMCPClient(self.settings) as pg_client:
                tools["postgres"] = pg_client.list_tools()
        except Exception as exc:
            logger.error(f"Error discovering PostgreSQL MCP tools: {exc}")

        # Google Drive tools (if authenticated)
        gd_client = GoogleDriveMCPClient(self.settings)
        if gd_client.is_authenticated():
            try:
                with gd_client:
                    tools["google_drive"] = gd_client.list_tools()
            except Exception as exc:
                logger.error(f"Error discovering Google Drive MCP tools: {exc}")

        return tools

    def discover_resources(self) -> Dict[str, List[MCPResourceSchema]]:
        """Discover resources exposed across all active MCP servers."""
        resources: Dict[str, List[MCPResourceSchema]] = {
            "postgres": [],
            "google_drive": [],
        }

        try:
            with PostgresMCPClient(self.settings) as pg_client:
                resources["postgres"] = pg_client.list_resources()
        except Exception as exc:
            logger.error(f"Error discovering PostgreSQL MCP resources: {exc}")

        gd_client = GoogleDriveMCPClient(self.settings)
        if gd_client.is_authenticated():
            try:
                with gd_client:
                    resources["google_drive"] = gd_client.list_resources()
            except Exception as exc:
                logger.error(f"Error discovering Google Drive MCP resources: {exc}")

        return resources

    def query_knowledge_source(self, sql: str) -> List[Dict[str, Any]]:
        """Safely execute a read-only query against the ESTD PostgreSQL knowledge source via MCP."""
        self.settings.validate_sql_safety(sql)
        with PostgresMCPClient(self.settings) as client:
            return client.execute_query(sql)

    def search_drive(self, query: str) -> str:
        """Search Google Drive via the Google Drive MCP server."""
        with GoogleDriveMCPClient(self.settings) as client:
            return client.search_files(query)

    def invoke_tool(self, request: MCPToolCallRequest) -> MCPToolCallResult:
        """Execute a tool call against the requested server with performance timing and error handling."""
        start_time = time.monotonic()
        server_key = request.server.lower().strip()
        tool_name = request.tool.lower().strip()

        try:
            if server_key in ("postgres", "postgresql", "estd-postgres"):
                if tool_name == "query":
                    sql = request.arguments.get("sql", "")
                    data = self.query_knowledge_source(sql)
                    exec_ms = (time.monotonic() - start_time) * 1000
                    return MCPToolCallResult(
                        server="postgres",
                        tool=tool_name,
                        success=True,
                        data=data,
                        execution_time_ms=round(exec_ms, 2),
                    )
                else:
                    raise MCPToolExecutionError("postgres", tool_name, f"Unknown tool '{tool_name}' on postgres MCP.")

            elif server_key in ("google_drive", "gdrive", "estd-gdrive"):
                if tool_name == "search":
                    query = request.arguments.get("query", "")
                    data = self.search_drive(query)
                    exec_ms = (time.monotonic() - start_time) * 1000
                    return MCPToolCallResult(
                        server="google_drive",
                        tool=tool_name,
                        success=True,
                        data=data,
                        execution_time_ms=round(exec_ms, 2),
                    )
                else:
                    raise MCPToolExecutionError("google_drive", tool_name, f"Unknown tool '{tool_name}' on gdrive MCP.")
            else:
                raise MCPConfigurationError(f"Unsupported MCP server: '{request.server}'.")

        except Exception as exc:
            exec_ms = (time.monotonic() - start_time) * 1000
            err_msg = str(exc)
            # Mask any database credentials from error output
            if self.settings.postgres_password:
                pwd = self.settings.postgres_password.get_secret_value()
                if pwd and len(pwd) > 2:
                    err_msg = err_msg.replace(pwd, "***")

            return MCPToolCallResult(
                server=request.server,
                tool=request.tool,
                success=False,
                error=err_msg,
                execution_time_ms=round(exec_ms, 2),
            )
