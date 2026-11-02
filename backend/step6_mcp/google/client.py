"""Client communicating with Google Drive / Docs MCP Server via JSON-RPC over stdio."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from typing import Any, Dict, List, Optional

from backend.common.logging.logger import logger
from backend.step6_mcp.config.mcp_settings import MCPSettings, get_mcp_settings
from backend.step6_mcp.exceptions import (
    MCPAuthenticationError,
    MCPConnectionError,
    MCPProtocolError,
    MCPTimeoutError,
    MCPToolExecutionError,
)
from backend.step6_mcp.schemas.mcp_status import MCPResourceSchema, MCPToolSchema


class GoogleDriveMCPClient:
    """Client for Google Drive/Docs MCP server providing safe file discovery and document reading."""

    def __init__(self, settings: Optional[MCPSettings] = None):
        self.settings = settings or get_mcp_settings()
        self._proc: Optional[subprocess.Popen] = None
        self._request_id = 0
        self._is_initialized = False

    def _next_id(self) -> int:
        self._request_id += 1
        return self._request_id

    def check_auth_state(self) -> Dict[str, Any]:
        """Check whether Google OAuth client secrets and credentials tokens exist."""
        return self.settings.get_google_auth_status()

    def is_authenticated(self) -> bool:
        """Return True if saved Google OAuth user credentials exist on disk."""
        return self.check_auth_state()["credentials_authorized"]

    def connect(self) -> None:
        """Start Google Drive MCP server process and perform initialization handshake.

        Raises:
            MCPAuthenticationError: If OAuth keys or authorized credentials are missing.
            MCPConnectionError: If server process fails to launch or complete handshake.
        """
        if self._proc is not None and self._proc.poll() is None:
            return

        auth_state = self.check_auth_state()
        if not auth_state["credentials_authorized"]:
            action = (
                "Run manual authorization: 1) Place Google OAuth client keys JSON at "
                f"'{self.settings.gdrive_oauth_path}'. "
                "2) Run command: python -m backend.step6_mcp.google.launcher --auth "
                "to log in and authorize the application."
            )
            raise MCPAuthenticationError(
                "google_drive",
                f"Missing authorized credentials at '{self.settings.gdrive_credentials_path}'.",
                manual_action_required=action,
            )

        npx_binary = "npx.cmd" if sys.platform == "win32" else "npx"
        cmd = [npx_binary, "-y", "@modelcontextprotocol/server-gdrive"]

        env = os.environ.copy()
        env["GDRIVE_OAUTH_PATH"] = str(Path(self.settings.gdrive_oauth_path).resolve())
        env["GDRIVE_CREDENTIALS_PATH"] = str(Path(self.settings.gdrive_credentials_path).resolve())

        logger.info("Starting Google Drive MCP server process...")
        try:
            self._proc = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                text=True,
                bufsize=1,
            )
        except Exception as exc:
            logger.error(f"Failed to spawn Google Drive MCP process: {exc}")
            raise MCPConnectionError("google_drive", f"Failed to spawn server process: {exc}")

        # Perform JSON-RPC initialization handshake
        try:
            init_req = {
                "jsonrpc": "2.0",
                "id": self._next_id(),
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "estd-gdrive-client", "version": "1.0.0"},
                },
            }
            init_resp = self._send_request(init_req, timeout=self.settings.mcp_init_timeout_seconds)
            if "error" in init_resp:
                error_msg = init_resp["error"].get("message", "Unknown error")
                raise MCPProtocolError("google_drive", f"Initialization error: {error_msg}")

            notif = {"jsonrpc": "2.0", "method": "notifications/initialized"}
            self._send_notification(notif)
            self._is_initialized = True
            logger.info("Google Drive MCP handshake completed successfully.")
        except Exception as exc:
            self.close()
            raise MCPConnectionError("google_drive", f"Handshake failed: {exc}")

    def _send_notification(self, payload: dict) -> None:
        """Send a notification without awaiting a response."""
        if not self._proc or self._proc.poll() is not None:
            raise MCPConnectionError("google_drive", "Server process is not running.")
        try:
            raw = json.dumps(payload) + "\n"
            self._proc.stdin.write(raw)
            self._proc.stdin.flush()
        except Exception as exc:
            raise MCPConnectionError("google_drive", f"Failed to send notification: {exc}")

    def _send_request(self, payload: dict, timeout: Optional[float] = None) -> dict:
        """Send a JSON-RPC request and await a response with timeout handling."""
        if not self._proc or self._proc.poll() is not None:
            raise MCPConnectionError("google_drive", "Server process is not running.")

        req_timeout = timeout or self.settings.mcp_timeout_seconds
        req_id = payload.get("id")

        try:
            raw = json.dumps(payload) + "\n"
            self._proc.stdin.write(raw)
            self._proc.stdin.flush()
        except Exception as exc:
            raise MCPConnectionError("google_drive", f"Failed to write to stdin: {exc}")

        start_time = time.monotonic()
        while True:
            if time.monotonic() - start_time > req_timeout:
                raise MCPTimeoutError("google_drive", req_timeout)

            if self._proc.poll() is not None:
                err_output = self._proc.stderr.read() if self._proc.stderr else ""
                raise MCPConnectionError(
                    "google_drive",
                    f"Server process terminated unexpectedly (code {self._proc.returncode}): {err_output}",
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
                continue

            if msg.get("id") == req_id:
                return msg

    def list_tools(self) -> List[MCPToolSchema]:
        """Discover tools exposed by the Google Drive MCP server."""
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
            raise MCPProtocolError("google_drive", resp["error"].get("message", "Error listing tools"))

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
        """Discover Google Drive files exposed as MCP resources."""
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
            logger.debug(f"Google Drive MCP server does not support resources/list: {resp['error']}")
            return []

        res_data = resp.get("result", {}).get("resources", [])
        return [
            MCPResourceSchema(
                uri=r.get("uri"),
                name=r.get("name"),
                mimeType=r.get("mimeType"),
            )
            for r in res_data
        ]

    def search_files(self, query: str) -> str:
        """Search for files in Google Drive using the MCP 'search' tool.

        Args:
            query: Search query text.

        Returns:
            Formatted search results string from Google Drive MCP.
        """
        if not self._is_initialized:
            self.connect()

        req = {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": "tools/call",
            "params": {
                "name": "search",
                "arguments": {"query": query},
            },
        }

        resp = self._send_request(req)
        if "error" in resp:
            raise MCPToolExecutionError("google_drive", "search", resp["error"].get("message", "Search failed"))

        result = resp.get("result", {})
        if result.get("isError"):
            content = result.get("content", [{}])
            err_text = content[0].get("text", "Search failed") if content else "Error"
            raise MCPToolExecutionError("google_drive", "search", err_text)

        content = result.get("content", [])
        if content and "text" in content[0]:
            return content[0]["text"]
        return "No files found."

    def read_resource(self, uri: str) -> dict:
        """Read a file or document resource exported by Google Drive MCP."""
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
            raise MCPProtocolError("google_drive", resp["error"].get("message", "Error reading resource"))

        contents = resp.get("result", {}).get("contents", [])
        if contents:
            return contents[0]
        return {}

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
