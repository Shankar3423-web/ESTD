"""FastAPI HTTP routes for Step 6 MCP Integration."""
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from backend.common.logging.logger import logger
from backend.step6_mcp.exceptions import (
    MCPAuthenticationError,
    MCPConfigurationError,
    MCPConnectionError,
    MCPSecurityError,
    MCPTimeoutError,
    MCPToolExecutionError,
)
from backend.step6_mcp.schemas.mcp_status import (
    MCPServerHealth,
    MCPStatusResponse,
    MCPToolCallRequest,
    MCPToolCallResult,
    MCPToolSchema,
)
from backend.step6_mcp.services.mcp_service import MCPService

router = APIRouter(prefix="/api/mcp", tags=["Step 6 - MCP Integration"])


def get_mcp_service() -> MCPService:
    """Dependency provider for MCPService."""
    return MCPService()


class SQLQueryRequest(BaseModel):
    """Request payload for safe PostgreSQL MCP query execution."""

    sql: str = Field(..., description="Safe, read-only SQL query (SELECT, WITH, EXPLAIN)")


@router.get(
    "/health",
    response_model=MCPStatusResponse,
    summary="Get overall MCP integration health status",
)
def get_mcp_health(service: MCPService = Depends(get_mcp_service)) -> MCPStatusResponse:
    """Evaluate and return operational health of all configured MCP server integrations."""
    return service.get_health_status()


@router.get(
    "/postgres/health",
    response_model=MCPServerHealth,
    summary="Verify PostgreSQL MCP server health",
)
def get_postgres_health(service: MCPService = Depends(get_mcp_service)) -> MCPServerHealth:
    """Verify live connectivity, tool discovery, and database read capability on port 5433."""
    return service.postgres_health.check_health()


@router.get(
    "/google/health",
    response_model=MCPServerHealth,
    summary="Verify Google Drive MCP server health",
)
def get_google_health(service: MCPService = Depends(get_mcp_service)) -> MCPServerHealth:
    """Verify Google Drive MCP configuration and authentication status without faking success."""
    return service.google_health.check_health()


@router.get(
    "/tools",
    response_model=Dict[str, List[MCPToolSchema]],
    summary="Discover available MCP tools across all servers",
)
def get_mcp_tools(service: MCPService = Depends(get_mcp_service)) -> Dict[str, List[MCPToolSchema]]:
    """Return tool schemas discovered across PostgreSQL MCP and Google Drive MCP."""
    return service.discover_tools()


@router.post(
    "/postgres/query",
    response_model=List[Dict[str, Any]],
    summary="Execute a safe read-only SQL query via PostgreSQL MCP",
)
def execute_postgres_query(
    request: SQLQueryRequest,
    service: MCPService = Depends(get_mcp_service),
) -> List[Dict[str, Any]]:
    """Safely execute a read-only SQL query against the ESTD knowledge source via MCP."""
    try:
        return service.query_knowledge_source(request.sql)
    except MCPSecurityError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Security violation: {exc.message}",
        )
    except MCPTimeoutError as exc:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=f"Query timed out: {exc.message}",
        )
    except MCPConnectionError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"PostgreSQL MCP connection failure: {exc.message}",
        )
    except MCPToolExecutionError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Query execution error: {exc.message}",
        )
    except Exception as exc:
        logger.error(f"Unexpected error in MCP query endpoint: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal error executing MCP query.",
        )


@router.post(
    "/tools/invoke",
    response_model=MCPToolCallResult,
    summary="Invoke an MCP tool dynamically",
)
def invoke_mcp_tool(
    request: MCPToolCallRequest,
    service: MCPService = Depends(get_mcp_service),
) -> MCPToolCallResult:
    """Invoke a discovered MCP tool on either postgres or google_drive."""
    return service.invoke_tool(request)
