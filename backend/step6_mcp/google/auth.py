"""Google OAuth 2.0 authentication and token management for Google Drive / Docs."""
import json
import os
from pathlib import Path
import time
from typing import Any, Dict, List, Optional
import urllib.parse

import httpx

from backend.common.logging.logger import logger
from backend.step6_mcp.config.mcp_settings import get_mcp_settings
from backend.step6_mcp.exceptions import MCPAuthenticationError

GOOGLE_AUTH_ENDPOINT = "https://accounts.google.com/o/oauth2/auth"
GOOGLE_TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"

REQUIRED_SCOPES: List[str] = [
    "https://www.googleapis.com/auth/drive.readonly",
    "https://www.googleapis.com/auth/drive.file",
]

DEFAULT_REDIRECT_URI = "https://antigravity.google/oauth-callback"


def load_client_credentials(oauth_path: Optional[Path] = None) -> Dict[str, str]:
    """Load Google OAuth client credentials from JSON file or environment variables."""
    settings = get_mcp_settings()
    path = oauth_path or settings.get_oauth_path()

    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            keys = data.get("installed") or data.get("web") or {}
            client_id = keys.get("client_id")
            client_secret = keys.get("client_secret")
            redirect_uris = keys.get("redirect_uris", [])
            if "https://antigravity.google/oauth-callback" in redirect_uris:
                redirect_uri = "https://antigravity.google/oauth-callback"
            elif redirect_uris:
                redirect_uri = redirect_uris[0]
            else:
                redirect_uri = DEFAULT_REDIRECT_URI

            if client_id and client_secret:
                return {
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "redirect_uri": redirect_uri,
                }
        except Exception as exc:
            logger.warning(f"Failed to parse OAuth client keys from {path}: {exc}")

    client_id = os.environ.get("GOOGLE_DRIVE_OAUTH_CLIENT_ID")
    client_secret = os.environ.get("GOOGLE_DRIVE_OAUTH_CLIENT_SECRET")
    if client_id and client_secret:
        return {
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": DEFAULT_REDIRECT_URI,
        }

    raise MCPAuthenticationError(
        "google_drive",
        f"OAuth client keys not found at '{path}'. Please provide client ID and secret.",
    )


def generate_authorization_url(redirect_uri: Optional[str] = None) -> str:
    """Generate the Google OAuth 2.0 authorization URL for human consent."""
    creds = load_client_credentials()
    effective_redirect_uri = redirect_uri or creds.get("redirect_uri") or DEFAULT_REDIRECT_URI

    params = {
        "client_id": creds["client_id"],
        "redirect_uri": effective_redirect_uri,
        "response_type": "code",
        "scope": " ".join(REQUIRED_SCOPES),
        "access_type": "offline",
        "prompt": "consent",
    }
    return f"{GOOGLE_AUTH_ENDPOINT}?{urllib.parse.urlencode(params)}"


def exchange_code_for_tokens(
    code: str,
    redirect_uri: Optional[str] = None,
    creds_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """Exchange authorization code for access and refresh tokens and save credentials."""
    creds = load_client_credentials()
    effective_redirect_uri = redirect_uri or creds.get("redirect_uri") or DEFAULT_REDIRECT_URI

    payload = {
        "code": code.strip(),
        "client_id": creds["client_id"],
        "client_secret": creds["client_secret"],
        "redirect_uri": effective_redirect_uri,
        "grant_type": "authorization_code",
    }

    try:
        with httpx.Client(timeout=15.0) as client:
            resp = client.post(GOOGLE_TOKEN_ENDPOINT, data=payload)
    except Exception as exc:
        raise MCPAuthenticationError("google_drive", f"Network failure contacting token endpoint: {exc}")

    if resp.status_code != 200:
        err_msg = resp.text
        # Avoid exposing client secret in logs
        safe_err = err_msg.replace(creds["client_secret"], "***")
        raise MCPAuthenticationError("google_drive", f"OAuth token exchange failed (HTTP {resp.status_code}): {safe_err}")

    token_data = resp.json()
    access_token = token_data.get("access_token")
    refresh_token = token_data.get("refresh_token")
    expires_in = token_data.get("expires_in", 3600)

    if not access_token:
        raise MCPAuthenticationError("google_drive", "Token endpoint returned no access_token.")

    settings = get_mcp_settings()
    target_path = creds_path or settings.get_credentials_path()
    target_path.parent.mkdir(parents=True, exist_ok=True)

    saved_creds = {
        "client_id": creds["client_id"],
        "client_secret": creds["client_secret"],
        "token": access_token,
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_uri": GOOGLE_TOKEN_ENDPOINT,
        "scopes": REQUIRED_SCOPES,
        "scope": " ".join(REQUIRED_SCOPES),
        "token_type": token_data.get("token_type", "Bearer"),
        "expires_at": int(time.time() + expires_in),
        "expiry_date": int(time.time() + expires_in) * 1000,
    }

    with open(target_path, "w", encoding="utf-8") as f:
        json.dump(saved_creds, f, indent=2)

    # Sync to root or backend credentials path if different
    alt_paths = [
        Path("c:/Users/nered/Desktop/ESTD/credentials/gdrive-server-credentials.json"),
        Path("c:/Users/nered/Desktop/ESTD/backend/credentials/gdrive-server-credentials.json"),
    ]
    for alt in alt_paths:
        if alt != target_path:
            try:
                alt.parent.mkdir(parents=True, exist_ok=True)
                with open(alt, "w", encoding="utf-8") as f:
                    json.dump(saved_creds, f, indent=2)
            except Exception as sync_exc:
                logger.warning(f"Failed syncing credentials to {alt}: {sync_exc}")

    logger.info(f"Google Drive MCP credentials successfully saved to {target_path}")
    return saved_creds


def refresh_access_token_if_needed(creds_path: Optional[Path] = None) -> str:
    """Return an active access token, refreshing it if near expiry."""
    settings = get_mcp_settings()
    path = creds_path or settings.get_credentials_path()

    if not path.exists():
        raise MCPAuthenticationError("google_drive", f"Credentials file not found at {path}")

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    access_token = data.get("access_token") or data.get("token")
    expires_at = data.get("expires_at", 0)
    refresh_token = data.get("refresh_token")

    # If token has more than 2 minutes left, return it
    if access_token and expires_at > (time.time() + 120):
        return access_token

    if not refresh_token:
        if access_token:
            return access_token
        raise MCPAuthenticationError("google_drive", "No refresh_token found in credentials to renew session.")

    client_id = data.get("client_id")
    client_secret = data.get("client_secret")
    if not client_id or not client_secret:
        client_info = load_client_credentials()
        client_id = client_info["client_id"]
        client_secret = client_info["client_secret"]

    payload = {
        "refresh_token": refresh_token,
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "refresh_token",
    }

    try:
        with httpx.Client(timeout=15.0) as client:
            resp = client.post(GOOGLE_TOKEN_ENDPOINT, data=payload)
    except Exception as exc:
        if access_token:
            return access_token
        raise MCPAuthenticationError("google_drive", f"Failed refreshing token: {exc}")

    if resp.status_code != 200:
        if access_token:
            return access_token
        raise MCPAuthenticationError("google_drive", f"Token refresh failed: {resp.text}")

    token_data = resp.json()
    new_token = token_data.get("access_token")
    expires_in = token_data.get("expires_in", 3600)

    data["token"] = new_token
    data["access_token"] = new_token
    data["expires_at"] = int(time.time() + expires_in)
    data["expiry_date"] = int(time.time() + expires_in) * 1000
    if "refresh_token" in token_data:
        data["refresh_token"] = token_data["refresh_token"]

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    alt_paths = [
        Path("c:/Users/nered/Desktop/ESTD/credentials/gdrive-server-credentials.json"),
        Path("c:/Users/nered/Desktop/ESTD/backend/credentials/gdrive-server-credentials.json"),
    ]
    for alt in alt_paths:
        if alt != path:
            try:
                alt.parent.mkdir(parents=True, exist_ok=True)
                with open(alt, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2)
            except Exception as sync_exc:
                logger.warning(f"Failed syncing refreshed credentials to {alt}: {sync_exc}")

    return new_token
