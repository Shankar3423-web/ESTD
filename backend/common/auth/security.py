"""Centralized authentication and security dependencies for ESTD Backend."""
import secrets
from typing import Optional
from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader, HTTPAuthorizationCredentials, HTTPBearer

from backend.common.config.settings import get_settings
from backend.common.logging.logger import logger

# Support both X-API-KEY header and Authorization: Bearer <token>
api_key_header = APIKeyHeader(name="X-API-KEY", auto_error=False)
bearer_auth = HTTPBearer(auto_error=False)


def verify_admin_api_key(
    header_key: Optional[str] = Security(api_key_header),
    bearer_creds: Optional[HTTPAuthorizationCredentials] = Security(bearer_auth),
) -> str:
    """Validate incoming request against configured ADMIN_API_KEY.
    
    Accepts:
    1. Header `X-API-KEY: <key>`
    2. Header `Authorization: Bearer <key>`
    
    Raises HTTP 401 if key is missing or invalid.
    """
    settings = get_settings()
    configured_key = settings.get_admin_api_key()

    provided_key: Optional[str] = None
    if header_key and header_key.strip():
        provided_key = header_key.strip()
    elif bearer_creds and bearer_creds.credentials and bearer_creds.credentials.strip():
        provided_key = bearer_creds.credentials.strip()

    if not provided_key:
        logger.warning("Unauthenticated request rejected on protected operational endpoint.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "AUTHENTICATION_REQUIRED",
                "message": "Operational endpoint requires valid 'X-API-KEY' header or 'Bearer' token.",
            },
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Constant-time comparison to prevent timing attacks
    if not secrets.compare_digest(provided_key, configured_key):
        logger.warning("Invalid API key rejected on protected operational endpoint.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "INVALID_CREDENTIALS",
                "message": "The provided API key or Bearer token is invalid.",
            },
            headers={"WWW-Authenticate": "Bearer"},
        )

    return provided_key

