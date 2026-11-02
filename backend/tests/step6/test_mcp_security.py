"""Security verification tests for Step 6 MCP Integration."""
from pathlib import Path
import pytest

from backend.step6_mcp.config.mcp_settings import get_mcp_settings
from backend.step6_mcp.exceptions import MCPSecurityError


class TestMCPSecurity:
    """Ensure strict read-only enforcement, injection protection, and credential secrecy."""

    @pytest.fixture
    def settings(self):
        return get_mcp_settings()

    @pytest.mark.parametrize(
        "destructive_sql",
        [
            "DROP TABLE news_articles;",
            "DROP DATABASE estd_knowledge;",
            "TRUNCATE TABLE categories;",
            "ALTER TABLE news_articles DROP COLUMN title;",
            "DELETE FROM news_articles WHERE id = 1;",
            "UPDATE news_articles SET title = 'hacked';",
            "INSERT INTO categories (name, slug) VALUES ('Hack', 'hack');",
            "GRANT ALL PRIVILEGES ON DATABASE estd_knowledge TO attacker;",
            "REVOKE ALL ON news_articles FROM postgres;",
            "CREATE TABLE evil (id int);",
            "EXECUTE evil_procedure();",
        ],
    )
    def test_destructive_sql_verbs_rejected(self, settings, destructive_sql):
        """Verify all destructive and administrative verbs raise MCPSecurityError."""
        with pytest.raises(MCPSecurityError) as exc_info:
            settings.validate_sql_safety(destructive_sql)
        assert "forbidden" in exc_info.value.message.lower() or "allowed read-only verb" in exc_info.value.message.lower()

    @pytest.mark.parametrize(
        "chained_sql",
        [
            "SELECT * FROM categories; DROP TABLE news_articles;",
            "SELECT count(*) FROM categories; DELETE FROM categories;",
            "WITH cte AS (SELECT 1) SELECT * FROM cte; DROP TABLE news_articles;",
        ],
    )
    def test_multi_statement_chained_queries_rejected(self, settings, chained_sql):
        """Verify semicolon statement chaining is strictly blocked."""
        with pytest.raises(MCPSecurityError) as exc_info:
            settings.validate_sql_safety(chained_sql)
        assert "semicolon" in exc_info.value.message.lower() or "forbidden" in exc_info.value.message.lower()

    @pytest.mark.parametrize(
        "safe_sql",
        [
            "SELECT * FROM categories;",
            "SELECT count(*) FROM news_articles",
            "SELECT id, title FROM news_articles WHERE category = 'Technology' ORDER BY id DESC LIMIT 10;",
            "WITH recent AS (SELECT id, title FROM news_articles LIMIT 5) SELECT * FROM recent;",
            "EXPLAIN SELECT * FROM categories WHERE id = 1;",
        ],
    )
    def test_safe_read_only_queries_allowed(self, settings, safe_sql):
        """Verify legitimate read-only queries pass validation."""
        # Should not raise exception
        settings.validate_sql_safety(safe_sql)

    def test_empty_sql_rejected(self, settings):
        """Verify empty or whitespace-only queries raise MCPSecurityError."""
        with pytest.raises(MCPSecurityError):
            settings.validate_sql_safety("")
        with pytest.raises(MCPSecurityError):
            settings.validate_sql_safety("   ")

    def test_env_file_is_gitignored(self):
        """Verify .env is gitignored and cannot be accidentally tracked."""
        backend_gitignore = Path(__file__).resolve().parent.parent.parent / ".gitignore"
        root_gitignore = backend_gitignore.parent.parent / ".gitignore"

        assert backend_gitignore.exists()
        assert root_gitignore.exists()

        backend_text = backend_gitignore.read_text(encoding="utf-8")
        root_text = root_gitignore.read_text(encoding="utf-8")

        assert ".env" in backend_text
        assert ".env" in root_text
        assert "*credentials*.json" in backend_text
        assert "*credentials*.json" in root_text

    def test_env_example_contains_placeholders_only(self):
        """Verify .env.example contains only placeholders, no real production passwords."""
        env_example = Path(__file__).resolve().parent.parent.parent / ".env.example"
        assert env_example.exists()
        content = env_example.read_text(encoding="utf-8")

        # Confirm placeholders
        assert "your_password" in content or "password" in content
        # Ensure actual known database password isn't leaked into example
        settings = get_mcp_settings()
        if settings.postgres_password:
            raw_pwd = settings.postgres_password.get_secret_value()
            if raw_pwd and raw_pwd != "your_password":
                assert f"POSTGRES_PASSWORD={raw_pwd}" not in content
