# ESTD Step 6 — MCP Integration / MCP Access Layer

## 1. Purpose of Step 6

The **ESTD MCP Access Layer** serves as the secure, isolated communication bridge between AI/MCP clients (such as Google Gemini, Antigravity IDE, Claude Desktop, Cursor) and the frozen ESTD production components:
1. **ESTD PostgreSQL Knowledge Source**: Read-only structured database access to news articles and categories on port `5433`.
2. **Google Drive / Google Docs**: File discovery, search, and document access to prepare for subsequent pipeline stages (Step 7 Content Generation and Step 8 Document Generation).

Steps 1 through 5 remain completely frozen production components. Step 6 introduces zero schema changes, duplicates no persistence logic, and provides strict read-only security enforcement.

---

## 2. Architecture

```text
                    ESTD PIPELINE

STEP 1: Source Collection (GNews, NewsData, RSS)
        ↓
STEP 2: Article Extraction
        ↓
STEP 3: Content Cleaning
        ↓
STEP 4: Duplicate Detection
        ↓
STEP 5: PostgreSQL Persistence (estd_knowledge :5433)
        │
        │ [Frozen Knowledge Base]
        ▼
══════════════════════════════════════════════════════════════════
               STEP 6 — MCP ACCESS LAYER
══════════════════════════════════════════════════════════════════
        │                                         │
        ▼                                         ▼
PostgreSQL MCP Server                    Google Drive MCP Server
(@modelcontextprotocol/server-postgres)  (@modelcontextprotocol/server-gdrive)
        │                                         │
        │ [Enforced Read-Only SQL]                │ [OAuth 2.0 Auth Boundary]
        ▼                                         ▼
ESTD PostgreSQL Database                 Google Drive & Docs
(Port 5433, estd_knowledge)              (Files, Docs as Markdown)
        │                                         │
        └───────────────────┬─────────────────────┘
                            ▼
                    Unified MCP Service
                  (backend.step6_mcp)
                            │
               ┌────────────┴────────────┐
               ▼                         ▼
      FastAPI Endpoints          AI / Gemini MCP Client
      (/api/mcp/*)               (via mcp_config.json)
══════════════════════════════════════════════════════════════════
                            │
                            ▼
               STEP 7: Content Generation (Future)
                            │
                            ▼
               STEP 8: Document Creation (Future)
```

---

## 3. PostgreSQL MCP Configuration

- **MCP Implementation**: `@modelcontextprotocol/server-postgres`
- **Transport**: JSON-RPC 2.0 over Stdio
- **Target Database**: `estd_knowledge` on `localhost:5433`
- **Executable Launcher**: `python -m backend.step6_mcp.postgres.launcher`
- **Credential Protection**: Database passwords and credentials are never stored in `mcp_config.json` or source control. The launcher loads connection parameters dynamically from `backend/.env` using the project's existing configuration system.

---

## 4. Google Drive / Docs MCP Configuration

- **MCP Implementation**: `@modelcontextprotocol/server-gdrive`
- **Transport**: JSON-RPC 2.0 over Stdio
- **Executable Launcher**: `python -m backend.step6_mcp.google.launcher`
- **Auth Trigger**: `python -m backend.step6_mcp.google.launcher --auth`
- **Credentials Directory**: `backend/credentials/` (gitignored)

---

## 5. Required Environment Variables

Add the following variables to `backend/.env` (refer to `backend/.env.example` for templates):

```bash
# Existing PostgreSQL Knowledge Source (Step 5)
POSTGRES_HOST=localhost
POSTGRES_PORT=5433
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
POSTGRES_DB=estd_knowledge
DATABASE_URL=postgresql://postgres:your_password@localhost:5433/estd_knowledge

# Step 6 MCP Settings
GDRIVE_OAUTH_PATH=credentials/gcp-oauth.keys.json
GDRIVE_CREDENTIALS_PATH=credentials/gdrive-server-credentials.json
MCP_TIMEOUT_SECONDS=20.0
MCP_READ_ONLY_ENFORCED=true
```

---

## 6. Authentication Process (Google OAuth 2.0)

When Google credentials have not been authorized, the health checker returns:
`REQUIRES_AUTHENTICATION` with clear instructions. It does not fake success.

### Step-by-Step Manual Authorization:
1. Open [Google Cloud Console](https://console.cloud.google.com/).
2. Create or select a project and enable the **Google Drive API**.
3. Under **APIs & Services > Credentials**, create an **OAuth 2.0 Client ID** with Application Type: **Desktop App**.
4. Download the client secret JSON file and place it at:
   `backend/credentials/gcp-oauth.keys.json`
5. Run the authentication command:
   ```bash
   .venv\Scripts\python -m backend.step6_mcp.google.launcher --auth
   ```
6. A browser window will open asking to grant read-only permissions to Google Drive (`https://www.googleapis.com/auth/drive.readonly`).
7. Complete authorization. The tokens will be stored in `backend/credentials/gdrive-server-credentials.json` (gitignored).

---

## 7. How to Start / Enable the MCP Integration

### Method A: External AI / Gemini / MCP Client (Antigravity IDE, Claude, Cursor)
The servers are registered in `~/.gemini/config/mcp_config.json` and `.agents/mcp_config.json`:

```json
{
  "mcpServers": {
    "estd-postgres": {
      "command": "c:\\Users\\nered\\Desktop\\ESTD\\backend\\.venv\\Scripts\\python.exe",
      "args": ["-m", "backend.step6_mcp.postgres.launcher"],
      "env": {
        "PYTHONPATH": "c:\\Users\\nered\\Desktop\\ESTD"
      }
    },
    "estd-gdrive": {
      "command": "c:\\Users\\nered\\Desktop\\ESTD\\backend\\.venv\\Scripts\\python.exe",
      "args": ["-m", "backend.step6_mcp.google.launcher"],
      "env": {
        "PYTHONPATH": "c:\\Users\\nered\\Desktop\\ESTD"
      }
    }
  }
}
```

### Method B: REST API Endpoints (via FastAPI Backend)
The backend exposes MCP status and query endpoints:
- `GET /api/mcp/health`
- `GET /api/mcp/tools`
- `POST /api/mcp/postgres/query`

---

## 8. How to Verify PostgreSQL MCP

### Option 1: Python CLI
```bash
.venv\Scripts\python -c "from backend.step6_mcp.postgres.health import PostgresMCPHealthChecker; print(PostgresMCPHealthChecker().check_health())"
```

### Option 2: HTTP Endpoint
```bash
curl http://localhost:8000/api/mcp/postgres/health
```

### Option 3: Safe SQL Query via MCP
```bash
curl -X POST http://localhost:8000/api/mcp/postgres/query \
  -H "Content-Type: application/json" \
  -d "{\"sql\": \"SELECT id, name, slug FROM categories LIMIT 5;\"}"
```

---

## 9. How to Verify Google MCP

```bash
.venv\Scripts\python -c "from backend.step6_mcp.google.health import GoogleDriveMCPHealthChecker; print(GoogleDriveMCPHealthChecker().check_health())"
```

Expected result when unauthenticated:
- `state`: `REQUIRES_AUTHENTICATION`
- `manual_action_required`: Actionable instructions for OAuth setup.

---

## 10. How to Verify MCP Tool Discovery

Run:
```bash
.venv\Scripts\python -c "from backend.step6_mcp.services.mcp_service import MCPService; print(MCPService().discover_tools())"
```

Output:
```python
{'postgres': [MCPToolSchema(name='query', description='Run a read-only SQL query', inputSchema=...)], 'google_drive': []}
```

---

## 11. AI / Gemini Access Verification

In the Antigravity IDE / Gemini client:
1. The global MCP configuration in `~/.gemini/config/mcp_config.json` automatically registers `estd-postgres` and `estd-gdrive`.
2. When the Language Server starts, it executes `python -m backend.step6_mcp.postgres.launcher`.
3. The AI client discovers the `query` tool and resources for `estd_knowledge`.
4. In chat, the model can query database statistics or articles via the tool.

---

## 12. Troubleshooting

1. **`npx` not found or permission error**:
   - Ensure Node.js (v18+) is installed and `npx` is available in system PATH.
2. **PostgreSQL connection refused**:
   - Ensure PostgreSQL is active on port `5433` and `estd_knowledge` database is running.
3. **`MCPSecurityError: Destructive or administrative SQL keyword is strictly forbidden`**:
   - Only `SELECT`, `WITH`, and `EXPLAIN` statements are permitted. Modifications (`DROP`, `DELETE`, `UPDATE`, `INSERT`) are intentionally blocked.
4. **Google Drive auth error**:
   - Verify `gcp-oauth.keys.json` is a Desktop App client credentials file, not a web application redirect URI file.

---

## 13. Security Considerations

- **Strict Read-Only Enforcement**: Queries are validated locally by `validate_sql_safety()` before transmission and executed under `BEGIN TRANSACTION READ ONLY` with automatic `ROLLBACK`.
- **Zero Credential Leakage**: Database passwords and auth tokens are masked (`:***@`) in logs, `__repr__`, error responses, and health payloads.
- **Git Protection**: `.env`, `*oauth*.json`, `*credentials*.json`, and `credentials/` are excluded by `.gitignore`.
- **Placeholder Example**: `.env.example` contains only template placeholders.

---

## 14. Current Environment Limitations

- **Google Drive Authentication**: Requires interactive user login in a browser to obtain OAuth refresh tokens. Until user credentials are provided, Google Drive operations safely report `REQUIRES_AUTHENTICATION`.
- **PostgreSQL Write Operations**: Write, update, delete, and DDL operations are forbidden by design in the MCP layer. Ingestion and persistence remain strictly owned by frozen Step 5.
