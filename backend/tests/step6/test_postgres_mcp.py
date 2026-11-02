"""Integration and functional tests for PostgreSQL MCP client and health checker."""
import pytest

from backend.step6_mcp.config.mcp_settings import get_mcp_settings
from backend.step6_mcp.exceptions import MCPSecurityError
from backend.step6_mcp.postgres.client import PostgresMCPClient
from backend.step6_mcp.postgres.health import PostgresMCPHealthChecker
from backend.step6_mcp.schemas.mcp_status import MCPHealthState


class TestPostgresMCP:
    """Test PostgreSQL MCP integration with the live ESTD database on port 5433."""

    @pytest.fixture
    def client(self):
        c = PostgresMCPClient()
        yield c
        c.close()

    def test_postgres_mcp_handshake_and_tool_discovery(self, client):
        """Verify client connects and discovers the read-only query tool."""
        client.connect()
        assert client._is_initialized is True

        tools = client.list_tools()
        tool_names = [t.name for t in tools]
        assert "query" in tool_names

        query_tool = next(t for t in tools if t.name == "query")
        assert "read-only" in query_tool.description.lower()
        assert "sql" in query_tool.inputSchema.get("properties", {})

    def test_postgres_mcp_resource_discovery(self, client):
        """Verify client discovers database table schema resources."""
        resources = client.list_resources()
        assert len(resources) > 0

        resource_uris = [r.uri for r in resources]
        # Verify canonical ESTD tables are discoverable
        has_categories = any("categories" in uri for uri in resource_uris)
        has_articles = any("news_articles" in uri for uri in resource_uris)
        assert has_categories or has_articles

    def test_postgres_mcp_safe_query_categories(self, client):
        """Verify executing a safe SELECT against categories table returns valid records."""
        results = client.execute_query("SELECT id, name, slug FROM categories ORDER BY id ASC LIMIT 5;")
        assert isinstance(results, list)
        assert len(results) == 5

        first = results[0]
        assert "id" in first
        assert "name" in first
        assert "slug" in first
        names = [r["name"] for r in results]
        assert "Tech" in names
        assert "Entertainment" in names

    def test_postgres_mcp_safe_query_news_articles(self, client):
        """Verify executing a safe SELECT against news_articles table succeeds."""
        results = client.execute_query("SELECT count(*) as count FROM news_articles;")
        assert isinstance(results, list)
        assert len(results) == 1
        assert "count" in results[0]

    def test_postgres_mcp_client_blocks_destructive_query(self, client):
        """Verify client rejects destructive query locally before transmitting."""
        with pytest.raises(MCPSecurityError):
            client.execute_query("DROP TABLE news_articles;")

    def test_postgres_mcp_health_checker(self):
        """Verify PostgresMCPHealthChecker end-to-end check returns HEALTHY status."""
        checker = PostgresMCPHealthChecker()
        health = checker.check_health()

        assert health.server_name == "postgres"
        assert health.state == MCPHealthState.HEALTHY
        assert health.configured is True
        assert health.reachable is True
        assert health.authenticated is True
        assert health.tools_count >= 1
        assert health.latency_ms is not None
        assert "5433" in health.details
        assert "estd_knowledge" in health.details
