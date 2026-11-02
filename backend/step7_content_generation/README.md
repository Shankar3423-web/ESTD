# ESTD — Step 7: Gemini AI Content Generation Layer

## 1. Purpose of Step 7

The objective of Step 7 is to provide an isolated, fact-grounded AI synthesis layer that transforms articles stored in the ESTD PostgreSQL knowledge source into high-impact, professional journalistic news reports.

Step 7 does **not** collect news independently from the internet or scrape URLs. Instead, it accesses verified, cleaned, and deduplicated articles strictly through the existing Step 6 PostgreSQL MCP server, submits structured prompts to Google Gemini AI, and validates the output against a Pydantic schema before delivery.

---

## 2. Architecture

```text
                  ESTD PIPELINE

STEP 1: Source Collection (RSS, GNews, NewsData)          [FROZEN]
        ↓
STEP 2: Article Extraction                                [FROZEN]
        ↓
STEP 3: Content Cleaning                                  [FROZEN]
        ↓
STEP 4: Duplicate Detection                               [FROZEN]
        ↓
STEP 5: PostgreSQL Knowledge Source (`news_articles`)     [FROZEN]
        ↓
STEP 6: PostgreSQL MCP Access (`@modelcontextprotocol`)   [FROZEN]
        ↓
════════════════════════════════════════════════════════════════════════
STEP 7 — GEMINI AI CONTENT GENERATION LAYER
════════════════════════════════════════════════════════════════════════
        ↓
1. Article Retrieval via Step 6 MCP (`query_knowledge_source`)
        ↓
2. Article Eligibility & Duplicate Prevention Check
        ↓
3. Factual Safety Prompt Assembly (`build_news_generation_prompt`)
        ↓
4. Gemini AI Synthesis (`GeminiClient.generate_structured`)
        ↓
5. Strict Schema & Grounding Validation (`GenerationValidator`)
        ↓
6. Validated Structured News (`GeneratedNews`)
════════════════════════════════════════════════════════════════════════
        ↓
STEP 8: Google Docs / Google Drive Publishing             [FUTURE STEP]
```

---

## 3. Gemini Configuration

Step 7 uses centralized settings loaded via Pydantic Settings from `backend/.env`.

### Supported Configuration Keys

| Variable | Description | Default | Security / Validation |
| :--- | :--- | :--- | :--- |
| `GEMINI_API_KEY` | Official Google Gemini API key | *Required* | Stored as `SecretStr`; masked in logs & errors |
| `GEMINI_MODEL` | Supported Gemini model name | `gemini-2.5-flash` | Verified active via API |
| `GEMINI_TEMPERATURE` | Generation randomness | `0.2` | Constrained between `0.0` and `2.0` |
| `GEMINI_MAX_RETRIES` | Max retries for transient errors | `2` | Bounded backoff retry policy |
| `GEMINI_TIMEOUT_SECONDS` | HTTP/API timeout | `30.0` | Range `1.0` to `120.0` |
| `GEMINI_MAX_OUTPUT_TOKENS` | Max tokens for generated text | `4096` | Range `512` to `8192` |

> [!IMPORTANT]
> The API key is masked in all logs, exceptions, and API payloads via `GeminiSettings.mask_secret()`. Real secrets must never be committed to git or exposed to clients.

---

## 4. Selected Gemini Model

- **Model**: `gemini-2.5-flash`
- **SDK**: `google-genai` (official unified Google GenAI Python SDK, v2.28.0+)
- **Verification**: Verified active, responsive, and compatible with structured JSON schema outputs (`response_mime_type="application/json"`).

---

## 5. Gemini Connectivity Verification

Connectivity is verified without transmitting sensitive payloads or exposing secrets:

```bash
.venv\Scripts\python -c "import sys; sys.path.insert(0, '.'); sys.path.insert(0, '..'); from backend.step7_content_generation.client.gemini_client import GeminiClient; print(GeminiClient().test_connectivity())"
```

Output:
```json
{"status": "connected", "model": "gemini-2.5-flash", "latency_ms": 1187.92, "response_received": true}
```

---

## 6. MCP → Gemini Flow

1. **Client Request**: Caller invokes `POST /step7/generate` with `{"article_id": <int>}`.
2. **MCP Retrieval**: `MCPGenerationService` calls `MCPService.query_knowledge_source(sql)`:
   ```sql
   SELECT id, title, description, content, url, source_name, source_type, author, published_at, category 
   FROM news_articles 
   WHERE id = :article_id 
   LIMIT 1;
   ```
3. **Eligibility Verification**:
   - Article exists in database.
   - Title is non-empty.
   - Content has at least 50 characters of cleaned text.
   - Category is one of the 5 canonical ESTD categories (`VALID_CATEGORIES`).
   - Source URL is valid.
4. **Duplicate Protection**: An in-memory cache checks if the article was already processed in the current session. If so, the cached `GeneratedNews` is returned immediately without re-calling Gemini.
5. **Prompt Assembly**: `build_news_generation_prompt()` bundles facts, category constraint, publisher attribution, and strict anti-hallucination rules.
6. **Gemini Invocation**: `GeminiClient` generates structured JSON conforming to `GeneratedNews`.
7. **Validation**: `GenerationValidator` verifies structure, field constraints, category preservation, URL retention, and lexical grounding.
8. **Response**: Structured `GenerationResponse` returned.

---

## 7. Schemas

### Generated News Output (`GeneratedNews`)

```python
class GeneratedNews(BaseModel):
    title: str               # 5-300 characters, compelling headline
    subtitle: str | None     # Contextual secondary deck
    category: ESTDCategory   # Canonical ESTD category strictly matching input
    summary: str             # 20-1000 characters, executive summary
    content: str             # Min 100 characters, full article body
    source_name: str         # Publisher or outlet name
    source_url: str          # Exact original URL for full traceability
    generated_at: datetime   # UTC generation timestamp
```

### Generation Request (`ArticleGenerationRequest`)

```python
class ArticleGenerationRequest(BaseModel):
    article_id: int          # Positive integer ID from news_articles
    custom_instructions: str | None # Optional editorial guidance
```

### Generation Response Envelope (`GenerationResponse`)

```python
class GenerationResponse(BaseModel):
    success: bool
    article_id: int | None
    data: GeneratedNews | None
    error: str | None
    generation_time_ms: float
    model_used: str
```

---

## 8. Validation & Anti-Hallucination Controls

Every generated article must satisfy:
1. **Title Existence & Length**: >= 5 characters.
2. **Summary Existence & Length**: >= 20 characters.
3. **Content Existence & Length**: >= 100 characters.
4. **Category Adherence**: Must match one of the 5 official ESTD categories:
   - `Artificial Intelligence`
   - `Technology`
   - `Business`
   - `Education`
   - `Science`
5. **URL Format & Matching**: Source URL must be a valid HTTP/HTTPS URL and match the source record.
6. **Lexical Grounding Check**: Validates token overlap between source article and generated text to reject hallucinated responses completely disconnected from input facts.

---

## 9. Error Handling & Retry Policy

| Error Type | Status Code | Policy |
| :--- | :--- | :--- |
| `ArticleIneligibleError` | 400 Bad Request | Non-retryable. Immediate rejection. |
| `GeminiAuthenticationError` | 502 Bad Gateway | Non-retryable. Immediate fail-fast without leaking key. |
| `GeminiModelError` | 500 Internal Error | Non-retryable. Immediate fail-fast. |
| `GeminiRateLimitError` (429) | 429 Too Many Requests | Retryable up to 2 times with exponential backoff (`2^attempt` s). |
| `GeminiTimeoutError` | 504 Gateway Timeout | Retryable once before safe failure. |
| `GenerationValidationError` | 422 Unprocessable | Non-retryable. Rejects malformed AI outputs. |

---

## 10. API Endpoints

| Method | Path | Summary |
| :--- | :--- | :--- |
| `POST` | `/step7/generate` | Generate ESTD news from article in PostgreSQL via MCP |
| `POST` | `/step7/generate/direct` | Direct synthesis from raw article payload |
| `GET` | `/step7/eligible-articles` | List candidate articles in PostgreSQL via MCP |
| `GET` | `/step7/health` | Health check verifying Gemini config & ping connectivity |

---

## 11. Testing Commands

All tests use the virtual environment (`.venv`):

```bash
# 1. Run Step 7 Unit and Route Tests (32 tests)
.venv\Scripts\pytest step7_content_generation/tests tests/step7 -v

# 2. Run Master Live Verification (MCP + Gemini 5-category live generation)
.venv\Scripts\python verify_step7_full_pipeline.py

# 3. Run Full Project Regression Suite (380 tests)
.venv\Scripts\pytest -q
```

---

## 12. Known Limitations & Database Schema Policy

1. **Step 5 Schema Integrity**: The existing `news_articles` table does not contain an `is_generated` or `generated_at` column. In accordance with the non-negotiable freeze rule (Steps 1–6 remain unmodified), Step 7 does not alter the Step 5 database schema.
2. **Session Duplicate Prevention**: Duplicate prevention is enforced at the service level via an in-memory generation registry (`_generated_articles_cache`). If persistent generation status across server restarts is required in future releases, a dedicated migration can be considered during pipeline evolution.
3. **Windows Subprocess Encoding**: On Windows environments, articles containing unusual non-cp1252 byte sequences are filtered during eligibility checks to ensure smooth MCP subprocess JSON-RPC communication.

---

## 13. Step 8 Boundary

Step 7 strictly terminates at **Validated ESTD Generated Content** (`GeneratedNews`).

The following capabilities belong exclusively to Step 8 and are **NOT** implemented in Step 7:
- Google Docs document creation
- Google Docs formatting / styling
- Google Drive upload or folder management
- Google Workspace MCP tool invocation
