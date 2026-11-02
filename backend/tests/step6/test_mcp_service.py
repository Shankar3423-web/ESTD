"""Tests for unified MCPService layer."""
import pytest

from backend.step6_mcp.exceptions import MCPSecurityError
from backend.step6_mcp.schemas.mcp_status import (
    MCPHealthState,
    MCPToolCallRequest,
    MCPToolCallResult,
)
from backend.step6_mcp.services.mcp_service import MCPService


class TestMCPService:
    """Test unified MCP service operations."""

    @pytest.fixture
    def service(self):
        return MCPService()

    def test_mcp_service_health_status_composite(self, service):
        """Verify composite health status correctly aggregates postgres and google health."""
        status_resp = service.get_health_status()
        assert status_resp.overall_status in ("HEALTHY", "PARTIALLY_READY (GOOGLE_AUTH_PENDING)")
        assert status_resp.postgres.state == MCPHealthState.HEALTHY
        assert status_resp.google_drive.state in (MCPHealthState.REQUIRES_AUTHENTICATION, MCPHealthState.HEALTHY)

    def test_mcp_service_tool_discovery(self, service):
        """Verify discovery returns dictionary with postgres and google_drive entries."""
        tools_dict = service.discover_tools()
        assert "postgres" in tools_dict
        assert "google_drive" in tools_dict

        pg_tools = tools_dict["postgres"]
        assert len(pg_tools) >= 1
        assert any(t.name == "query" for t in pg_tools)

    def test_mcp_service_query_knowledge_source(self, service):
        """Verify query_knowledge_source executes valid SELECT and returns rows."""
        rows = service.query_knowledge_source("SELECT id, name FROM categories ORDER BY id ASC LIMIT 2;")
        assert isinstance(rows, list)
        assert len(rows) == 2
        assert rows[0]["name"] == "Tech"

    def test_mcp_service_query_knowledge_source_security(self, service):
        """Verify query_knowledge_source pre-validates and rejects DROP TABLE."""
        with pytest.raises(MCPSecurityError):
            service.query_knowledge_source("DROP TABLE news_articles;")

    def test_mcp_service_invoke_tool_postgres_query(self, service):
        """Verify invoke_tool routes to postgres query tool and returns structured result."""
        req = MCPToolCallRequest(
            server="postgres",
            tool="query",
            arguments={"sql": "SELECT count(*) as total FROM categories;"},
        )
        result = service.invoke_tool(req)
        assert isinstance(result, MCPToolCallResult)
        assert result.success is True
        assert result.server == "postgres"
        assert result.tool == "query"
        assert result.data[0]["total"] in (5, "5")
        assert result.execution_time_ms > 0

    def test_mcp_service_invoke_tool_unsupported_server(self, service):
        """Verify invoke_tool handles unknown server gracefully."""
        req = MCPToolCallRequest(
            server="nonexistent_mcp",
            tool="ping",
            arguments={},
        )
        result = service.invoke_tool(req)
        assert result.success is False
        assert "Unsupported MCP server" in result.error
