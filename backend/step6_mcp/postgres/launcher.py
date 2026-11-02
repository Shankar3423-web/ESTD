"""Executable launcher for ESTD PostgreSQL MCP Server.

Used by external MCP clients (Antigravity, Gemini, Claude Desktop) to start
the PostgreSQL MCP server without hardcoding credentials into host configuration files.
"""
import os
from pathlib import Path
import subprocess
import sys

# Ensure backend and project root are in sys.path
_BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
_PROJECT_ROOT = _BACKEND_DIR.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from backend.step6_mcp.config.mcp_settings import get_mcp_settings


def main() -> None:
    """Launch the PostgreSQL MCP server with configuration loaded dynamically from .env."""
    settings = get_mcp_settings()
    db_url = settings.get_postgres_connection_url()

    npx_binary = "npx.cmd" if sys.platform == "win32" else "npx"
    cmd = [npx_binary, "-y", "@modelcontextprotocol/server-postgres", db_url]

    # Run and forward stdio transparently
    try:
        sys.exit(subprocess.call(cmd))
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == "__main__":
    main()
