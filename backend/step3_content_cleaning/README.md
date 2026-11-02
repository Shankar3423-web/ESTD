# ESTD — Step 3: Content Cleaning & Normalization

## 1. Overview & Purpose

**Step 3: Content Cleaning & Normalization** is the deterministic preprocessing and sanitization stage of the ESTD news pipeline. It consumes raw extracted article data from **Step 2 (Article Scraping & Extraction)**, strips non-article webpage noise (advertisements, cookie banners, navigation elements, social sharing prompts, newsletter signups, footer boilerplate), normalizes Unicode and whitespace formatting, cleans individual paragraphs, deduplicates exact repeated extraction artifacts, and produces a validated, canonical `CleanedArticle` representation for downstream consumption.

```
Step 1: Source Collection (FROZEN)
        ↓
     NewsItem
        ↓
Step 2: Article Extraction (FROZEN)
        ↓
  ExtractedArticle
        ↓
Step 3: Content Cleaning & Normalization (IMPLEMENTED)
        ↓
   CleanedArticle
        ↓
Step 4: Duplicate Detection (NOT IMPLEMENTED - FUTURE STAGE)
```

---

## 2. Explicit Boundaries & Non-Goals

> [!IMPORTANT]
> **Step 3 does NOT perform duplicate detection, semantic similarity, or AI rewriting.**

- **NO Article-Level Duplicate Detection**: Duplicate article matching across sources belongs strictly to **Step 4**.
- **NO Semantic Similarity / Cosine Similarity**: No cross-article vector comparisons or nearest neighbor searches.
- **NO Embeddings / Vector Databases**: No vector stores, ChromaDB, Pinecone, or FAISS.
- **NO LLMs / AI Services**: No OpenAI, Gemini, Anthropic, RAG, or AI summarization/rewriting.
- **NO Meaning Modification**: Step 3 cleans formatting and strips noise; it never paraphrases, summarizes, or alters the factual meaning of the news article.
- **NO Category Reclassification**: The 5 ESTD categories (`Artificial Intelligence`, `Technology`, `Business`, `Education`, `Science`) are strictly preserved.

---

## 3. Architecture & Directory Structure

All Step 3 implementation resides under `backend/step3_content_cleaning/`:

```
backend/step3_content_cleaning/
├── __init__.py                 # Package exports (CleanedArticle, CleaningStatus, ContentCleaningService)
├── config.py                   # Explicit, configurable thresholds & toggles (CleaningConfig)
├── apis/
│   ├── __init__.py
│   └── cleaning_routes.py      # FastAPI endpoints (/clean, /clean-batch)
├── cleaners/
│   ├── __init__.py
│   ├── html_cleaner.py         # BeautifulSoup HTML stripper, tag-to-newline mapping & entity decoder
│   ├── boilerplate_cleaner.py  # Conservative regex & pattern filters for ads, cookies, footers
│   └── paragraph_cleaner.py    # Paragraph hygiene & conservative repeated-paragraph deduplication
├── normalizers/
│   ├── __init__.py
│   ├── unicode_normalizer.py   # NFC composition, smart quotes, dashes, non-breaking space normalization
│   ├── whitespace_normalizer.py# Tabs, repeated spaces, and newline spacing normalization
│   └── text_normalizer.py      # Composite normalizer orchestrator
├── models/
│   ├── __init__.py
│   ├── cleaning_enums.py       # CleaningStatus (SUCCESS, CLEANING_FAILED)
│   └── cleaned_article.py      # Canonical CleanedArticle model preserving Step 1 & 2 provenance
├── schemas/
│   ├── __init__.py
│   └── cleaning_schemas.py     # Request/Response schemas (CleaningRequest, SingleCleaningResponse, etc.)
├── services/
│   ├── __init__.py
│   └── content_cleaning_service.py # Core orchestrator of the deterministic pipeline
├── exceptions/
│   ├── __init__.py
│   └── cleaning_exceptions.py  # Domain-specific exceptions inheriting from ESTDException
└── README.md                   # Comprehensive technical documentation & testing guide
```

---

## 4. Pipeline Execution Flow

The content cleaning service executes in a strictly deterministic sequence:

```
                  ExtractedArticle (from Step 2)
                                ↓
1. Input Validation: Check non-null, valid category, content presence
                                ↓
2. HTML / Text Cleanup: Strip HTML tags, scripts, styles, convert block tags to newlines
                                ↓
3. Boilerplate Removal: Filter out ads, cookie notices, newsletters, social links
                                ↓
4. Unicode Normalization: NFC composition, smart quotes to ASCII, standard dashes, nbsp
                                ↓
5. Whitespace Normalization: Collapse horizontal spaces, tabs, cap blank lines (max 2)
                                ↓
6. Paragraph Cleanup: Strip decorative lines, empty paragraphs, isolate list items
                                ↓
7. Conservative Repeated-Paragraph Removal: Deduplicate verbatim repeated extraction artifacts
                                ↓
8. Output Validation: Verify minimum length (>=25 chars), word count (>=5), valid metadata
                                ↓
                         CleanedArticle
```

---

## 5. Input and Output Contracts

### Input Contract: `ExtractedArticle` (Step 2)
Step 3 consumes the exact `ExtractedArticle` model produced by Step 2:
- `title` (str, required)
- `description` (Optional[str])
- `url` (str, required)
- `source_name` (Optional[str])
- `source_type` (str, required, e.g. "gnews", "newsdata", "rss")
- `author` (Optional[str])
- `published_at` (Optional[str], ISO 8601 UTC)
- `category` (str, required — must be one of the 5 valid categories)
- `image_url` (Optional[str])
- `collected_at` (str, required)
- `canonical_url` (Optional[str])
- `extraction_status` (ExtractionStatus, required)
- `extraction_method` (Optional[ExtractionMethod])
- `extracted_at` (str)
- `content` (Optional[str], full extracted body text)

### Output Contract: `CleanedArticle` (Step 3)
Step 3 outputs a `CleanedArticle` with 100% metadata provenance preserved:

| Field | Type | Description |
|---|---|---|
| `title` | `str` | Headline from Step 1 / Step 2 (preserved) |
| `description` | `Optional[str]` | Summary snippet from Step 1 (preserved) |
| `url` | `str` | Original article URL (preserved) |
| `source_name` | `Optional[str]` | Publisher name (preserved) |
| `source_type` | `str` | Aggregator provider identifier (preserved) |
| `author` | `Optional[str]` | Article author (preserved) |
| `published_at` | `Optional[str]` | Publication timestamp (preserved) |
| `category` | `str` | Validated ESTD category (preserved) |
| `image_url` | `Optional[str]` | Thumbnail or feature image URL (preserved) |
| `collected_at` | `str` | Ingestion timestamp from Step 1 (preserved) |
| `canonical_url` | `Optional[str]` | Canonical URL discovered by Step 2 (preserved) |
| `extraction_status`| `Optional[str]` | Step 2 extraction status (preserved) |
| `extraction_method`| `Optional[str]` | Step 2 extraction method (preserved) |
| `extracted_at` | `Optional[str]` | Step 2 extraction timestamp (preserved) |
| **`original_content`** | `Optional[str]` | **Raw uncleaned content from Step 2 (preserved for auditing & debugging)** |
| **`cleaned_content`** | `Optional[str]` | **Sanitized, normalized text body produced by Step 3** |
| **`content`** | `Optional[str]` | **Primary content alias pointing to `cleaned_content` for downstream stages** |
| **`cleaning_status`** | `CleaningStatus` | **Outcome status: `SUCCESS` or `CLEANING_FAILED`** |
| **`cleaned_at`** | `str` | **ISO 8601 UTC timestamp of Step 3 execution** |
| **`original_content_length`** | `int` | **Character count of original content** |
| **`cleaned_content_length`** | `int` | **Character count of cleaned content** |
| **`error_message`** | `Optional[str]` | **Descriptive failure reason if cleaning failed; None on success** |

---

## 6. Supported Cleaning & Normalization Rules

1. **HTML Removal (`HTMLCleaner`)**:
   - Parses with BeautifulSoup (`html.parser`).
   - Discards non-content trees: `<script>`, `<style>`, `<noscript>`, `<iframe>`, `<svg>`, `<canvas>`, `<form>`, `<button>`, `<nav>`, `<header>`, `<footer>`, `<aside>`, etc.
   - Converts block tags (`<p>`, `<div>`, `<h1>`-`<h6>`, `<li>`, `<blockquote>`, `<br>`, etc.) to newlines to preserve paragraph boundaries.
   - Decomposes tags with ad/cookie classes (`.ad-banner`, `.ad-slot`, `.advertisement`, `.cookie-notice`, `.social-share`, `.share-box`).
   - Safely decodes HTML entities (`&amp;` → `&`, `&quot;` → `"`, `&#39;` → `'`, `&lt;` → `<`, `&gt;` → `>`).
   - Handles malformed HTML without crashing.

2. **Conservative Boilerplate Removal (`BoilerplateCleaner`)**:
   - Advertisements: `ADVERTISEMENT`, `Sponsored Content`, `Promoted Stories`, `[Advertisement]`.
   - Cookie banners: `We use cookies to improve your experience...`, `Accept all cookies`, `Manage cookie preferences`.
   - Social sharing prompts: `Share this article on Twitter`, `Share on LinkedIn`, `Follow us on X`.
   - Newsletter prompts: `Sign up for our newsletter`, `Subscribe to our daily updates`, `Get the latest news in your inbox`.
   - "Read more" links: `Read more: ...`, `Related stories: ...`, `Also read: ...`.
   - Navigation fragments: `Home > Tech > AI`, `Skip to main content`, `Back to top`.
   - Copyright / Footer boilerplate: `All rights reserved`, `Copyright © 2026...`.
   - Code fragments: `googletag.*`, `window._taboola*`.
   - *Conservative principle*: Multi-sentence news paragraphs discussing cookies or advertising in an editorial context are strictly preserved.

3. **Unicode Normalization (`UnicodeNormalizer`)**:
   - NFC canonical composition via `unicodedata.normalize('NFC', text)`.
   - Curly quotes & smart apostrophes (`“`, `”`, `„`, `«`, `»` → `"`; `‘`, `’`, `‚`, `‛`, `′`, `` ` `` → `'`).
   - Typographic dashes (`—` em dash, `–` en dash, `―` horizontal bar, `−` minus → standard `-`).
   - Exotic & non-breaking spaces (`\u00a0`, `\u2000`-`\u200a`, `\u202f`, `\u3000` → standard ASCII space ` `).
   - Zero-width & control character removal (`\u200b`, `\ufeff`, `\u00ad`).
   - Standardizes ellipsis (`…` → `...`).
   - Preserves all international characters (accents, umlauts, Cyrillic, Greek, CJK, etc.).

4. **Whitespace Normalization (`WhitespaceNormalizer`)**:
   - Replaces `\r\n` and `\r` with `\n`.
   - Converts tabs to spaces.
   - Collapses multiple horizontal spaces into a single space.
   - Trims whitespace from the beginning and end of each line.
   - Caps consecutive blank lines to standard double newlines (`\n\n`), preventing collapsed single giant paragraphs or runaway blank line sequences.

5. **Paragraph Cleanup & Deduplication (`ParagraphCleaner`)**:
   - Removes empty or whitespace-only paragraphs.
   - Removes purely decorative lines (`---`, `***`, `===`, `###`, `•••`).
   - Removes exact repeated-paragraph extraction artifacts (`Paragraph A`, `Paragraph B`, `Paragraph A` → `Paragraph A`, `Paragraph B`).
   - Preserves headings, numbered lists, bullet points, and original ordering.

---

## 7. API Endpoints

### Single Article Cleaning
- **Method**: `POST`
- **Path**: `/api/v1/content-cleaning/clean`
- **Request Body**: Accepts either direct `ExtractedArticle` or wrapped `{"article": ExtractedArticle}`
- **Response**: `SingleCleaningResponse` (`{ "status": "success"|"failed", "data": CleanedArticle }`)

### Batch Article Cleaning
- **Method**: `POST`
- **Path**: `/api/v1/content-cleaning/clean-batch`
- **Request Body**: Accepts either `List[ExtractedArticle]` or `{"articles": List[ExtractedArticle]}`
- **Response**: `BatchCleaningResponse` (`{ "status": "success", "count": int, "items": List[CleanedArticle] }`)

---

## 8. Manual Postman Test Cases

To verify Step 3 via Postman or HTTP client, start the backend server:

```powershell
.venv\Scripts\activate
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

### Health Check First
- **Method**: `GET`
- **URL**: `http://127.0.0.1:8000/health`
- **Expected Status**: `200 OK`
- **Expected Body**: `{"status": "ok"}`

---

### TEST 1 — Valid Article Cleaning
- **Method**: `POST`
- **URL**: `http://127.0.0.1:8000/api/v1/content-cleaning/clean`
- **Headers**: `Content-Type: application/json`
- **Body**:
```json
{
  "title": "Quantum Computing Laboratory Achieves Sub-Kelvin Benchmark",
  "description": "Researchers maintain quantum coherence across multi-qubit processor.",
  "url": "https://science.example.com/quantum/sub-kelvin",
  "source_name": "Science Review",
  "source_type": "rss",
  "author": "Dr. Aris Thorne",
  "published_at": "2026-09-30T10:00:00Z",
  "category": "Science",
  "collected_at": "2026-09-30T10:15:00Z",
  "extraction_status": "EXTRACTED",
  "content": "Physicists at the High Energy Consortium have demonstrated quantum telemetry over a forty-kilometer subterranean optical fiber network.\n\nThe technique maintains coherence across entangled photon pairs despite thermal fluctuations.\n\nCommercial prototype modules are scheduled for field endurance testing throughout the coming year."
}
```
- **Expected HTTP Status**: `200 OK`
- **Expected Response**:
```json
{
  "status": "success",
  "data": {
    "title": "Quantum Computing Laboratory Achieves Sub-Kelvin Benchmark",
    "category": "Science",
    "cleaning_status": "SUCCESS",
    "cleaned_content": "Physicists at the High Energy Consortium have demonstrated quantum telemetry over a forty-kilometer subterranean optical fiber network.\n\nThe technique maintains coherence across entangled photon pairs despite thermal fluctuations.\n\nCommercial prototype modules are scheduled for field endurance testing throughout the coming year.",
    "original_content_length": 330,
    "cleaned_content_length": 330,
    "error_message": null
  }
}
```

---

### TEST 2 — HTML Article Cleaning
- **Method**: `POST`
- **URL**: `http://127.0.0.1:8000/api/v1/content-cleaning/clean`
- **Headers**: `Content-Type: application/json`
- **Body**:
```json
{
  "title": "Autonomous Drone Navigation in GPS-Denied Environments",
  "url": "https://tech.example.com/drones/gps-denied",
  "source_type": "gnews",
  "category": "Technology",
  "collected_at": "2026-09-30T10:00:00Z",
  "extraction_status": "EXTRACTED",
  "content": "<p>Autonomous aerial robotics systems often encounter severe degradation when operating in subterranean caverns or dense urban canyons where satellite positioning signals are obstructed.</p><div class='ad-banner'>Advertisement: Discover Best Drones</div><p>A novel vision-inertial odometry pipeline utilizing neuromorphic event cameras has demonstrated centimeter-level localization accuracy under zero-illumination conditions.</p>"
}
```
- **Expected HTTP Status**: `200 OK`
- **Expected Response**: `status: "success"`, `cleaning_status: "SUCCESS"`, HTML tags (`<p>`, `<div>`) and advertisement stripped from `cleaned_content`.

---

### TEST 3 — Article with Boilerplate
- **Method**: `POST`
- **URL**: `http://127.0.0.1:8000/api/v1/content-cleaning/clean`
- **Headers**: `Content-Type: application/json`
- **Body**:
```json
{
  "title": "Central Bank Announces Digital Currency Pilot",
  "url": "https://finance.example.com/cbdc-pilot",
  "source_type": "newsdata",
  "category": "Business",
  "collected_at": "2026-09-30T10:00:00Z",
  "extraction_status": "EXTRACTED",
  "content": "We use cookies to improve your experience. Accept all cookies.\n\nADVERTISEMENT\n\nThe monetary authority unveiled technical specifications for its sovereign retail digital currency pilot today. Interoperability with existing commercial banking infrastructure was highlighted.\n\nSign up for our daily newsletter to receive financial alerts directly in your inbox.\n\nShare this article on Twitter | Share on LinkedIn\n\nAll rights reserved. Copyright 2026 Global Finance Media."
}
```
- **Expected HTTP Status**: `200 OK`
- **Expected Response**: `status: "success"`, `cleaning_status: "SUCCESS"`, cookies, ads, newsletter, social links, and copyright footer removed. Valid monetary authority text preserved.

---

### TEST 4 — Existing Clean Article
- **Method**: `POST`
- **URL**: `http://127.0.0.1:8000/api/v1/content-cleaning/clean`
- **Headers**: `Content-Type: application/json`
- **Body**:
```json
{
  "title": "Universities Adopt Adaptive AI Tutors in STEM Curricula",
  "url": "https://education.example.com/ai-tutors",
  "source_type": "rss",
  "category": "Education",
  "collected_at": "2026-09-30T10:00:00Z",
  "extraction_status": "CONTENT_ALREADY_AVAILABLE",
  "content": "Higher education institutions are increasingly incorporating adaptive artificial intelligence tutors into foundational mathematics courses. Preliminary longitudinal data demonstrates a twelve percent increase in retention rates among first-year engineering cohorts."
}
```
- **Expected HTTP Status**: `200 OK`
- **Expected Response**: `status: "success"`, `cleaning_status: "SUCCESS"`, content remains essentially unchanged.

---

### TEST 5 — Empty Content Handling
- **Method**: `POST`
- **URL**: `http://127.0.0.1:8000/api/v1/content-cleaning/clean`
- **Headers**: `Content-Type: application/json`
- **Body**:
```json
{
  "title": "Article Missing Extracted Content",
  "url": "https://example.com/no-content-story",
  "source_type": "rss",
  "category": "Technology",
  "collected_at": "2026-09-30T10:00:00Z",
  "extraction_status": "EXTRACTION_FAILED",
  "content": null
}
```
- **Expected HTTP Status**: `200 OK` (Controlled Failure Response)
- **Expected Response**:
```json
{
  "status": "failed",
  "data": {
    "title": "Article Missing Extracted Content",
    "cleaning_status": "CLEANING_FAILED",
    "cleaned_content": null,
    "error_message": "Article content is empty or contains no readable text."
  }
}
```

---

### TEST 6 — Invalid Request (Schema Validation)
- **Method**: `POST`
- **URL**: `http://127.0.0.1:8000/api/v1/content-cleaning/clean`
- **Headers**: `Content-Type: application/json`
- **Body**:
```json
{
  "category": "UnsupportedCategory",
  "content": "Some text"
}
```
- **Expected HTTP Status**: `422 Unprocessable Entity`
- **Expected Response**:
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Validation error for 'article': Field required"
  }
}
```

---

### TEST 7 — Real Step 2 Output
- **Method**: `POST`
- **URL**: `http://127.0.0.1:8000/api/v1/content-cleaning/clean`
- **Headers**: `Content-Type: application/json`
- **Body**: Send the direct response payload from Step 2 `/api/v1/article-extraction/extract`.
- **Expected HTTP Status**: `200 OK`
- **Expected Response**: `status: "success"`, `cleaning_status: "SUCCESS"`, `original_content` preserved, `cleaned_content` sanitized.

---

## 9. Automated Testing & Verification

All automated tests can be run using the following commands:

```powershell
# 1. Activate Virtual Environment
.venv\Scripts\activate

# 2. Run Step 3 Unit & Endpoint Tests
pytest tests/step3 -v

# 3. Run Step 1 -> Step 2 -> Step 3 Pipeline Verification Script
python tests/verify_step1_to_step3_pipeline.py

# 4. Run Automated 7-Case Postman Verification Script
python tests/step3/manual_postman_verification.py

# 5. Run Complete Regression Test Suite (Step 1, Step 2, Step 3)
pytest
```
