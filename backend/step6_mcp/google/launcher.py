"""Executable launcher for Google Drive / Docs MCP Server.

Supports running as an MCP stdio server or launching the interactive OAuth flow:
    python -m backend.step6_mcp.google.launcher         # Run MCP server
    python -m backend.step6_mcp.google.launcher --auth  # Launch OAuth browser auth
"""
import os
from pathlib import Path
import subprocess
import sys
import webbrowser

# Ensure backend and project root are in sys.path
_BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
_PROJECT_ROOT = _BACKEND_DIR.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from backend.step6_mcp.config.mcp_settings import get_mcp_settings
from backend.step6_mcp.google.auth import (
    exchange_code_for_tokens,
    generate_authorization_url,
)


def main() -> None:
    settings = get_mcp_settings()
    oauth_path = settings.get_oauth_path()
    creds_path = settings.get_credentials_path()

    # Ensure parent credentials directory exists
    creds_path.parent.mkdir(parents=True, exist_ok=True)

    npx_binary = "npx.cmd" if sys.platform == "win32" else "npx"

    env = os.environ.copy()
    env["GDRIVE_OAUTH_PATH"] = str(oauth_path)
    env["GDRIVE_CREDENTIALS_PATH"] = str(creds_path)

    if "--auth" in sys.argv or (len(sys.argv) > 1 and sys.argv[1] == "auth"):
        print(f"Launching Google OAuth authorization flow...")
        print(f"OAuth Client Keys: {oauth_path}")
        print(f"Target Credentials File: {creds_path}")

        if not oauth_path.exists():
            print(f"ERROR: OAuth client keys file not found at: {oauth_path}")
            print("Please ensure credentials/gcp-oauth.keys.json exists.")
            sys.exit(1)

        # Check if code is passed as argument: --code <code> or --code=<code>
        auth_code = None
        for i, arg in enumerate(sys.argv):
            if arg == "--code" and i + 1 < len(sys.argv):
                auth_code = sys.argv[i + 1]
                break
            elif arg.startswith("--code="):
                auth_code = arg.split("=", 1)[1]
                break

        auth_url = generate_authorization_url()

        if auth_code:
            print(f"Exchanging provided authorization code...")
            try:
                exchange_code_for_tokens(auth_code, creds_path=creds_path)
                print(f"SUCCESS: Authorized credentials saved to: {creds_path}")
                sys.exit(0)
            except Exception as exc:
                print(f"ERROR exchanging code: {exc}")
                sys.exit(1)

        print("\n" + "=" * 70)
        print("GOOGLE OAUTH AUTHORIZATION REQUIRED")
        print("=" * 70)
        print("Please authorize with account: shankar13052005@gmail.com")
        print("Authorization URL:")
        print(auth_url)
        print("=" * 70 + "\n")

        try:
            webbrowser.open(auth_url)
        except Exception:
            pass

        # If interactive terminal, prompt for the code
        if sys.stdin.isatty():
            try:
                entered_code = input("Enter the authorization code from the redirect page: ").strip()
                if entered_code:
                    exchange_code_for_tokens(entered_code, creds_path=creds_path)
                    print(f"SUCCESS: Authorized credentials saved to: {creds_path}")
                    sys.exit(0)
            except (KeyboardInterrupt, EOFError):
                print("\nAuthorization cancelled.")
                sys.exit(1)
        else:
            print("To complete authorization, run:")
            print(f"python -m backend.step6_mcp.google.launcher --auth --code <YOUR_AUTH_CODE>")
            sys.exit(0)

    # Standard stdio server mode
    if not creds_path.exists():
        sys.stderr.write(
            f"Google Drive MCP credentials not found at: {creds_path}\n"
            f"Please run 'python -m backend.step6_mcp.google.launcher --auth' first to authenticate.\n"
        )
        sys.exit(1)

    cmd = [npx_binary, "-y", "@modelcontextprotocol/server-gdrive"]
    try:
        sys.exit(subprocess.call(cmd, env=env))
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == "__main__":
    main()
