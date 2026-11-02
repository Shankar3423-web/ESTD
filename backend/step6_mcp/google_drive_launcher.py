"""Module alias for Google Drive MCP launcher.

Supports:
    python -m backend.step6_mcp.google_drive_launcher --auth
    python -m backend.step6_mcp.google_drive_launcher
"""
from backend.step6_mcp.google.launcher import main

if __name__ == "__main__":
    main()
