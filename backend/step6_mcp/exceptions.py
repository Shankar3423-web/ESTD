"""Domain exceptions for Step 6 MCP Integration layer."""
from typing import Optional

from backend.common.exceptions.custom_exceptions import ESTDException


class MCPException(ESTDException):
    """Base exception for all MCP-related errors."""

    def __init__(self, message: str, code: str = "MCP_ERROR"):
        super().__init__(message=message, code=code)


class MCPConfigurationError(MCPException):
    """Raised when MCP environment or server configuration is invalid or missing."""

    def __init__(self, message: str):
        super().__init__(message=message, code="MCP_CONFIGURATION_ERROR")


class MCPConnectionError(MCPException):
    """Raised when the MCP client cannot establish or maintain connection to an MCP server."""

    def __init__(self, server_name: str, message: str = "Failed to connect to MCP server."):
        super().__init__(
            message=f"[{server_name}] {message}",
            code="MCP_CONNECTION_ERROR",
        )
        self.server_name = server_name


class MCPTimeoutError(MCPException):
    """Raised when an MCP operation times out."""

    def __init__(self, server_name: str, timeout_seconds: float):
        super().__init__(
            message=f"[{server_name}] Operation timed out after {timeout_seconds:.1f} seconds.",
            code="MCP_TIMEOUT_ERROR",
        )
        self.server_name = server_name
        self.timeout_seconds = timeout_seconds


class MCPProtocolError(MCPException):
    """Raised when an MCP server returns a malformed or unexpected protocol response."""

    def __init__(self, server_name: str, message: str):
        super().__init__(
            message=f"[{server_name}] Protocol error: {message}",
            code="MCP_PROTOCOL_ERROR",
        )
        self.server_name = server_name


class MCPSecurityError(MCPException):
    """Raised when an attempted operation violates MCP security constraints (e.g. destructive SQL)."""

    def __init__(self, message: str):
        super().__init__(message=message, code="MCP_SECURITY_VIOLATION")


class MCPToolExecutionError(MCPException):
    """Raised when an MCP tool call fails or returns an execution error."""

    def __init__(self, server_name: str, tool_name: str, message: str):
        super().__init__(
            message=f"[{server_name}] Tool '{tool_name}' execution failed: {message}",
            code="MCP_TOOL_EXECUTION_ERROR",
        )
        self.server_name = server_name
        self.tool_name = tool_name


class MCPAuthenticationError(MCPException):
    """Raised when an MCP server requires manual or external authentication."""

    def __init__(self, server_name: str, message: str, manual_action_required: Optional[str] = None):
        super().__init__(
            message=f"[{server_name}] Authentication required: {message}",
            code="MCP_AUTH_REQUIRED",
        )
        self.server_name = server_name
        self.manual_action_required = manual_action_required
