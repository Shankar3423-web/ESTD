# Step 4 — Duplicate Detection & Deduplication Engine

## 1. Purpose of Step 4

In the **ESTD (Enterprise Source-to-Document)** pipeline, Step 4 receives cleaned and normalized news articles produced by **Step 3 (Content Cleaning & Normalization)** and determines whether each article is `UNIQUE` or a `DUPLICATE`.

To ensure maximum integrity, deterministic reproducibility, low latency, and zero per-token cost, Step 4 operates **entirely without external AI, OpenAI, Gemini, generative AI, or external vector APIs**. All matching is performed locally using mathematical and algorithmic techniques:
1. Canonical URL normalization and exact match.
2. Cryptographic SHA-256 exact content fingerprinting.
3. Local unigram TF-IDF vectorization and Cosine Similarity calculation.
4. Cross-batch and persistent historical deduplication against PostgreSQL.

```text
STEP 3
Cleaned / Normalized Article
        ↓
STEP 4
Duplicate Detection
        ↓
 ┌───────────────┐
 │ URL Matching  │ ──► Matched? ──► DUPLICATE (URL_MATCH)
 └───────┬───────┘
         │ No
         ▼
 ┌─────────────────────┐
 │ Exact Content Hash  │ ──► Matched? ──► DUPLICATE (EXACT_CONTENT)
 │      SHA-256        │
 └──────────┬──────────┘
            │ No
            ▼
 ┌─────────────────────┐
 │ TF-IDF              │
 │ +                   │ ──► Score >= Threshold? ──► DUPLICATE (SIMILARITY)
 │ Cosine Similarity   │
 └──────────┬──────────┘
            │ No
            ▼
 ┌─────────────────────┐
 │ Duplicate Decision  │ ──► UNIQUE ──► Persist Index ──► STEP 5
 └─────────────────────┘
```

---

## 2. Input Contract

Step 4 accepts the canonical `CleanedArticle` model produced by Step 3 (`backend.step3_content_cleaning.models.cleaned_article.CleanedArticle`) or wrapped inside `DuplicateCheckRequest`.

### Key Input Fields Preserved:
- `title` (str, required): Article headline.
- `url` (str, required): Original publication URL from Step 1.
- `canonical_url` (str, optional): Canonical link extracted in Step 2.
- `cleaned_content` (str, optional): Cleaned text body produced by Step 3.
- `content` (str, optional): Downstream body text field from Step 3.
- `description` (str, optional): Synopsis / description from Step 1.
- `category` (str, required): One of the 5 official ESTD categories (`Technology`, `Artificial Intelligence`, `Science`, `Business`, `General`).
- `source_name` (str, optional): Name of publisher/feed.
- `source_type` (str, required): Source identifier (`gnews`, `newsdata`, `rss`).
- `author` (str, optional): Author name if identified.
- `published_at` (str, optional): ISO 8601 publication timestamp.
- `collected_at` (str, required): ISO 8601 collection timestamp.
- `cleaning_status` (CleaningStatus, required): `SUCCESS` or `CLEANING_FAILED`.

---

## 3. Output Contract

Step 4 outputs a `DuplicateCheckResult` model containing the original `CleanedArticle` and a strongly-typed `DuplicateDecision`:

```json
{
  "status": "duplicate",
  "data": {
    "status": "duplicate",
    "decision": {
      "status": "DUPLICATE",
      "is_duplicate": true,
      "duplicate_reason": "SIMILARITY",
      "detection_scope": "HISTORICAL",
      "matched_article_id": "42",
      "matched_article_title": "OpenAI releases new reasoning model",
      "matched_article_url": "https://techcrunch.com/2026/10/01/openai-model",
      "similarity_score": 0.9395,
      "confidence": 0.9395,
      "normalized_url": "https://venturebeat.com/2026/10/01/openai-ai-dev-reasoning",
      "content_hash": "2816999bbf287c674251bbf391e4ab6b7a544521f7bbffdf4e45ab02465ab2ba",
      "evaluated_at": "2026-10-01T15:00:00Z"
    },
    "article": { ... }
  }
}
```

For unique articles:
```json
{
  "status": "unique",
  "data": {
    "status": "unique",
    "decision": {
      "status": "UNIQUE",
      "is_duplicate": false,
      "duplicate_reason": null,
      "detection_scope": null,
      "matched_article_id": null,
      "matched_article_title": null,
      "matched_article_url": null,
      "similarity_score": 0.0,
      "confidence": 1.0,
      "normalized_url": "https://space.com/2026/10/01/habitable-exoplanet",
      "content_hash": "296be0798dcb052efd553fb729a765c71e73357d9bc9d46ac2e3f227c96939a9",
      "evaluated_at": "2026-10-01T15:00:00Z"
    },
    "article": { ... }
  }
}
```

---

## 4. Detection Pipeline & Priority

Evaluation adheres strictly to cost-ordered priority:
1. **Stage 1 — URL Match** (O(1) in-memory lookup / indexed DB query):
   - Fast, deterministic.
   - If matched, processing stops immediately; expensive NLP is bypassed.
2. **Stage 2 — SHA-256 Exact Content Fingerprint** (O(L) hash computation + indexed DB query):
   - Catches cross-publisher wire syndication and republishing where URLs differ but text is identical.
   - If matched, processing stops immediately; TF-IDF is bypassed.
3. **Stage 3 — TF-IDF & Cosine Similarity** (O(V * C) vector comparison):
   - Evaluates paraphrased, updated, or re-headlined articles against candidate articles in the current batch and recent historical index.
   - If `similarity_score >= SIMILARITY_THRESHOLD`, classified as `DUPLICATE` with reason `SIMILARITY`.
4. **Final Decision**:
   - If no stage triggers, the article is declared `UNIQUE` and indexed for future comparisons.

---

## 5. URL Normalization

Implemented in `normalizers/url_normalizer.py`:
- **Scheme**: Standardized to lowercase (`https`).
- **Host**: Lowercased, stripped of leading `www.` aliases (`www.theverge.com` -> `theverge.com`).
- **Ports**: Default ports (`:80` for http, `:443` for https) removed.
- **Paths**: Consecutive slashes collapsed (`//` -> `/`), trailing slashes removed (except root `/`).
- **Fragments**: Completely stripped (`#article-comments` -> removed).
- **Tracking Parameters Stripped**:
  `utm_source`, `utm_medium`, `utm_campaign`, `utm_term`, `utm_content`, `utm_id`, `fbclid`, `gclid`, `msclkid`, `mc_eid`, `yclid`, `_ga`, `_gl`, `ref`, `ref_src`, `ref_url`, `trk`, `spm`, `igshid`.
- **Identity Parameters Preserved**: Legitimate content query parameters (e.g. `id=98765`, `page=2`) are strictly preserved and sorted alphabetically so parameter ordering does not affect canonical matching.

---

## 6. SHA-256 Exact Content Fingerprinting

Implemented in `normalizers/text_normalizer.py` and `detectors/exact_content_detector.py`:
- Text is canonicalized using Unicode NFC normalization.
- Converted to lowercase.
- All whitespace sequences (`\r`, `\n`, `\t`, multiple spaces) collapsed to single space.
- Surrounding whitespace stripped.
- SHA-256 digest computed via `hashlib.sha256(canonical_text.encode('utf-8')).hexdigest()`.

---

## 7. TF-IDF & Cosine Similarity

Implemented in `detectors/similarity_detector.py` and `services/similarity_service.py`:
- **Engine**: Local deterministic `scikit-learn` `TfidfVectorizer`.
- **Parameters**:
  - `ngram_range`: (1, 1) unigrams.
  - `stop_words`: `"english"`.
  - `max_features`: 5000.
  - `strip_accents`: `"unicode"`.
- **Similarity Metric**: `sklearn.metrics.pairwise.cosine_similarity`.
- **Threshold**: Configurable via `SIMILARITY_THRESHOLD` (default: `0.82`).

---

## 8. Related ≠ Duplicate

Cosine similarity measures vocabulary overlap, not semantic equivalence. Two independent articles covering the same topic (e.g. "Apple launches new iPhone today" vs "Apple announces another iPhone model for next year") share high keyword overlap (`Apple`, `iPhone`, `model`, `announces`) but represent distinct news events.

ESTD enforces a conservative threshold (`0.82`) combined with exact candidate retrieval to prevent false positive deduplication of independent news stories.

---

## 9. Current-Batch Deduplication

Implemented in `index/duplicate_index.py`:
- Deduplication evaluates each article sequentially within the submitted batch.
- Each evaluated article is immediately registered into the in-memory batch index (`_batch_by_url`, `_batch_by_hash`, `_batch_unique_items`).
- Subsequent articles in the batch are compared against previously processed items in memory **before any database transaction is finalized**.
- In an input batch `[A, B, C, D]` where `A == B` and `C == D`, the engine guarantees:
  - `A -> UNIQUE`
  - `B -> DUPLICATE`
  - `C -> UNIQUE`
  - `D -> DUPLICATE`

---

## 10. Historical Deduplication & Database Behavior

Step 4 utilizes the existing PostgreSQL database infrastructure in `backend/database/`:
- **Model**: `DuplicateIndexRecord` mapped to table `estd_duplicate_index`.
- **Indexed Columns**: `normalized_url`, `content_hash`, `category`, `created_at`.
- **Candidate Retrieval**: Fetches recent unique articles within the same category to constrain TF-IDF comparisons to relevant candidates, preventing unbounded database growth from degrading comparison speed.
- **Traceability**: All duplicate decisions record the matched record ID, matched title, matched URL, detection method, and similarity score.

---

## 11. API Endpoints

### 1. `POST /api/v1/duplicate-detection/check`
Evaluates a single article.
- **Request Body**:
```json
{
  "article": {
    "title": "OpenAI announces reasoning model",
    "url": "https://techcrunch.com/2026/10/01/openai-model",
    "source_type": "gnews",
    "category": "Artificial Intelligence",
    "collected_at": "2026-10-01T10:15:00Z",
    "cleaned_content": "Full article body...",
    "cleaning_status": "SUCCESS"
  }
}
```
- **Response**: `200 OK` with `SingleDuplicateResponse`.

### 2. `POST /api/v1/duplicate-detection/check-batch`
Evaluates a batch of articles with cross-batch and historical matching.
- **Request Body**:
```json
{
  "articles": [ ... ]
}
```
- **Response**: `200 OK` with `BatchDuplicateResponse` containing `total_count`, `unique_count`, `duplicate_count`, and ordered list of results.

### 3. `GET /api/v1/duplicate-detection/stats`
Returns historical index statistics (`total_indexed`, `unique_articles`, `duplicate_records`).

---

## 12. Running Tests

Execute the automated test suite using the virtual environment:

```powershell
# Run all Step 4 tests
.\.venv\Scripts\pytest.exe -v tests/step4

# Run live Postman simulation verification
.\.venv\Scripts\python.exe tests/step4/manual_postman_verification.py

# Run complete ESTD regression suite (Steps 1–4)
.\.venv\Scripts\pytest.exe -v
```

---

## 13. Integration with Step 5

Step 4 acts as the final gatekeeper before the **ESTD Knowledge Source (Step 5)**:
- Articles classified as `UNIQUE` proceed to Step 5 for persistent knowledge storage.
- Articles classified as `DUPLICATE` are blocked from polluting downstream knowledge storage while retaining complete auditability in the duplicate index.
