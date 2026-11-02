"""Pydantic schemas for Step 6 MCP Integration layer."""
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class MCPHealthState(str, Enum):
    """Health states for MCP servers."""

    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    UNHEALTHY = "UNHEALTHY"
    REQUIRES_AUTHENTICATION = "REQUIRES_AUTHENTICATION"
    NOT_CONFIGURED = "NOT_CONFIGURED"


class MCPToolSchema(BaseModel):
    """Schema for a discovered MCP tool."""

    name: str = Field(..., description="Tool name identifier")
    description: Optional[str] = Field(None, description="Human/LLM readable tool description")
    inputSchema: Dict[str, Any] = Field(default_factory=dict, description="JSON Schema for tool arguments")


class MCPResourceSchema(BaseModel):
    """Schema for an MCP resource exposed by the server."""

    uri: str = Field(..., description="Resource URI")
    name: str = Field(..., description="Resource display name")
    mimeType: Optional[str] = Field(None, description="MIME type of resource content")


class MCPServerHealth(BaseModel):
    """Health and status metadata for an individual MCP server integration."""

    server_name: str = Field(..., description="Name of the MCP server (e.g. 'postgres', 'google_drive')")
    state: MCPHealthState = Field(..., description="Current operational state")
    configured: bool = Field(..., description="Whether required configuration exists")
    reachable: bool = Field(..., description="Whether server process/endpoint is reachable")
    authenticated: bool = Field(..., description="Whether required credentials/auth tokens are present")
    tools_count: int = Field(default=0, description="Number of discovered tools")
    resources_count: int = Field(default=0, description="Number of discovered resources")
    latency_ms: Optional[float] = Field(None, description="Response latency in milliseconds")
    details: str = Field(..., description="Human-readable diagnostics or verification message")
    manual_action_required: Optional[str] = Field(
        None,
        description="Detailed manual action required from user if blocked at an auth or setup boundary",
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp of the health evaluation",
    )


class MCPStatusResponse(BaseModel):
    """Unified status payload representing all configured MCP integrations."""

    overall_status: str = Field(..., description="Overall system health status")
    postgres: MCPServerHealth = Field(..., description="PostgreSQL MCP server health")
    google_drive: MCPServerHealth = Field(..., description="Google Drive/Docs MCP server health")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp of the status check",
    )


class MCPToolCallRequest(BaseModel):
    """Payload to invoke a specific MCP tool."""

    server: str = Field(..., description="Target MCP server ('postgres' or 'google_drive')")
    tool: str = Field(..., description="Name of tool to call (e.g. 'query', 'search')")
    arguments: Dict[str, Any] = Field(default_factory=dict, description="Tool invocation parameters")


class MCPToolCallResult(BaseModel):
    """Result of an MCP tool invocation."""

    server: str = Field(..., description="MCP server that handled the call")
    tool: str = Field(..., description="Tool that was executed")
    success: bool = Field(..., description="Whether tool execution succeeded")
    data: Optional[Any] = Field(None, description="Returned content or structured result")
    error: Optional[str] = Field(None, description="Error message if execution failed")
    execution_time_ms: float = Field(..., description="Execution duration in milliseconds")
