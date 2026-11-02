"""Client communicating with PostgreSQL MCP Server via JSON-RPC over stdio."""
import json
import os
import re
import subprocess
import sys
import time
from typing import Any, Dict, List, Optional

from backend.common.logging.logger import logger
from backend.step6_mcp.config.mcp_settings import MCPSettings, get_mcp_settings
from backend.step6_mcp.exceptions import (
    MCPConnectionError,
    MCPProtocolError,
    MCPSecurityError,
    MCPTimeoutError,
    MCPToolExecutionError,
)
from backend.step6_mcp.schemas.mcp_status import MCPResourceSchema, MCPToolSchema


class PostgresMCPClient:
    """Client for PostgreSQL MCP Server providing safe, read-only database access."""

    def __init__(self, settings: Optional[MCPSettings] = None):
        self.settings = settings or get_mcp_settings()
        self._proc: Optional[subprocess.Popen] = None
        self._request_id = 0
        self._is_initialized = False

    def _next_id(self) -> int:
        self._request_id += 1
        return self._request_id

    def connect(self) -> None:
        """Start the PostgreSQL MCP server process and complete protocol initialization."""
        if self._proc is not None and self._proc.poll() is None:
            return

        db_url = self.settings.get_postgres_connection_url()
        safe_url = self.settings.get_safe_postgres_url()

        # On Windows, npx requires npx.cmd
        npx_binary = "npx.cmd" if sys.platform == "win32" else "npx"
        cmd = [npx_binary, "-y", "@modelcontextprotocol/server-postgres", db_url]

        logger.info(f"Starting PostgreSQL MCP server process connecting to {safe_url}")
        try:
            self._proc = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
            )
        except Exception as exc:
            masked_exc = self._mask_credentials(str(exc))
            logger.error(f"Failed to spawn PostgreSQL MCP process: {masked_exc}")
            raise MCPConnectionError("postgres", f"Failed to spawn server process: {masked_exc}")

        # Perform JSON-RPC initialization handshake
        try:
            init_req = {
                "jsonrpc": "2.0",
                "id": self._next_id(),
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "estd-postgres-client", "version": "1.0.0"},
                },
            }
            init_resp = self._send_request(init_req, timeout=self.settings.mcp_init_timeout_seconds)
            if "error" in init_resp:
                error_msg = init_resp["error"].get("message", "Unknown error")
                raise MCPProtocolError("postgres", f"Initialization error: {error_msg}")

            # Send initialized notification (notifications do not produce a response)
            notif = {"jsonrpc": "2.0", "method": "notifications/initialized"}
            self._send_notification(notif)
            self._is_initialized = True
            logger.info("PostgreSQL MCP handshake completed successfully")
        except Exception as exc:
            self.close()
            masked_exc = self._mask_credentials(str(exc))
            raise MCPConnectionError("postgres", f"Handshake failed: {masked_exc}")

    def _send_notification(self, payload: dict) -> None:
        """Send a JSON-RPC notification to the server without waiting for a reply."""
        if not self._proc or self._proc.poll() is not None:
            raise MCPConnectionError("postgres", "Server process is not running.")
        try:
            raw = json.dumps(payload) + "\n"
            self._proc.stdin.write(raw)
            self._proc.stdin.flush()
        except Exception as exc:
            masked_exc = self._mask_credentials(str(exc))
            raise MCPConnectionError("postgres", f"Failed to send notification: {masked_exc}")

    def _send_request(self, payload: dict, timeout: Optional[float] = None) -> dict:
        """Send a JSON-RPC request and await a response with timeout handling."""
        if not self._proc or self._proc.poll() is not None:
            raise MCPConnectionError("postgres", "Server process is not running.")

        req_timeout = timeout or self.settings.mcp_timeout_seconds
        req_id = payload.get("id")

        try:
            raw = json.dumps(payload) + "\n"
            self._proc.stdin.write(raw)
            self._proc.stdin.flush()
        except Exception as exc:
            masked_exc = self._mask_credentials(str(exc))
            raise MCPConnectionError("postgres", f"Failed to write to server stdin: {masked_exc}")

        # Read line from stdout with polling timeout
        start_time = time.monotonic()
        while True:
            if time.monotonic() - start_time > req_timeout:
                raise MCPTimeoutError("postgres", req_timeout)

            # Check if process died
            if self._proc.poll() is not None:
                err_output = self._proc.stderr.read() if self._proc.stderr else ""
                masked_err = self._mask_credentials(err_output)
                raise MCPConnectionError(
                    "postgres",
                    f"Server process terminated unexpectedly (code {self._proc.returncode}): {masked_err}",
                )

            line = self._proc.stdout.readline()
            if not line:
                time.sleep(0.05)
                continue

            line = line.strip()
            if not line:
                continue

            try:
                msg = json.loads(line)
            except json.JSONDecodeError:
                # Discard non-JSON log lines
                continue

            if msg.get("id") == req_id:
                return msg

    def list_tools(self) -> List[MCPToolSchema]:
        """Discover tools exposed by the PostgreSQL MCP server."""
        if not self._is_initialized:
            self.connect()

        req = {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": "tools/list",
            "params": {},
        }
        resp = self._send_request(req)
        if "error" in resp:
            raise MCPProtocolError("postgres", resp["error"].get("message", "Error listing tools"))

        tools_data = resp.get("result", {}).get("tools", [])
        return [
            MCPToolSchema(
                name=t.get("name"),
                description=t.get("description"),
                inputSchema=t.get("inputSchema", {}),
            )
            for t in tools_data
        ]

    def list_resources(self) -> List[MCPResourceSchema]:
        """Discover database schema resources exposed by the server."""
        if not self._is_initialized:
            self.connect()

        req = {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": "resources/list",
            "params": {},
        }
        resp = self._send_request(req)
        if "error" in resp:
            raise MCPProtocolError("postgres", resp["error"].get("message", "Error listing resources"))

        res_data = resp.get("result", {}).get("resources", [])
        return [
            MCPResourceSchema(
                uri=r.get("uri"),
                name=r.get("name"),
                mimeType=r.get("mimeType"),
            )
            for r in res_data
        ]

    def read_resource(self, uri: str) -> dict:
        """Read a database resource schema definition."""
        if not self._is_initialized:
            self.connect()

        req = {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": "resources/read",
            "params": {"uri": uri},
        }
        resp = self._send_request(req)
        if "error" in resp:
            raise MCPProtocolError("postgres", resp["error"].get("message", "Error reading resource"))

        contents = resp.get("result", {}).get("contents", [])
        if contents and "text" in contents[0]:
            try:
                return json.loads(contents[0]["text"])
            except json.JSONDecodeError:
                return {"raw": contents[0]["text"]}
        return {}

    def execute_query(self, sql: str) -> List[Dict[str, Any]]:
        """Safely execute a read-only SQL query via the PostgreSQL MCP query tool.

        Args:
            sql: Read-only SQL query string.

        Returns:
            List of dictionaries representing returned rows.

        Raises:
            MCPSecurityError: If query violates read-only safety rules.
            MCPToolExecutionError: If query execution fails.
        """
        # Enforce security validation before sending to MCP
        self.settings.validate_sql_safety(sql)

        if not self._is_initialized:
            self.connect()

        req = {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": "tools/call",
            "params": {
                "name": "query",
                "arguments": {"sql": sql},
            },
        }

        resp = self._send_request(req)
        if "error" in resp:
            err_msg = resp["error"].get("message", "Query execution error")
            masked_err = self._mask_credentials(err_msg)
            raise MCPToolExecutionError("postgres", "query", masked_err)

        result = resp.get("result", {})
        if result.get("isError"):
            content = result.get("content", [{}])
            err_text = content[0].get("text", "Unknown query execution failure") if content else "Error"
            masked_err = self._mask_credentials(err_text)
            raise MCPToolExecutionError("postgres", "query", masked_err)

        content = result.get("content", [])
        if not content:
            return []

        text_data = content[0].get("text", "[]")
        try:
            return json.loads(text_data)
        except json.JSONDecodeError as exc:
            logger.warning(f"Could not parse query result as JSON array: {exc}")
            return [{"raw": text_data}]

    def _mask_credentials(self, text: str) -> str:
        """Redact passwords and secrets from error strings."""
        if not text:
            return ""
        # Mask postgresql://user:password@host
        masked = re.sub(r":([^@/]+)@", ":***@", text)
        if self.settings.postgres_password:
            pwd = self.settings.postgres_password.get_secret_value()
            if pwd and len(pwd) > 2:
                masked = masked.replace(pwd, "***")
        return masked

    def close(self) -> None:
        """Cleanly terminate the MCP server process."""
        self._is_initialized = False
        if self._proc is not None:
            try:
                self._proc.terminate()
                self._proc.wait(timeout=2.0)
            except Exception:
                try:
                    self._proc.kill()
                except Exception:
                    pass
            finally:
                self._proc = None

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
