# ESTD — Step 2: Article Scraping & Content Extraction

## 1. Purpose
Step 2 is responsible for receiving normalized `NewsItem` objects produced by Step 1 (Source Collection), determining if substantive article content is already present, and—only when required—fetching the original article webpage over HTTP and extracting readable article content and metadata into an `ExtractedArticle` representation.

---

## 2. Pipeline Flow
```text
STEP 1 (Source Collection)
           │
           ▼
        NewsItem
           │
           ▼
STEP 2 (Article Scraping & Content Extraction)
           │
   [Sufficiency Check]
           │
    ┌──────┴──────┐
   YES            NO
    │              │
    │         [Safe HTTP Fetch] (SSRF check + timeout)
    │              │
    │         [HTML Extraction] (JSON-LD + Semantic tags + Heuristics)
    │              │
    └──────┬───────┘
           ▼
    ExtractedArticle
           │
           ▼
STEP 3 (Content Cleaning & Normalization — Future)
```

---

## 3. Decision Logic (Content Sufficiency)
The system prevents redundant external network requests by evaluating whether the incoming item already contains sufficient article prose:

- **Metadata Snippet**: Short description (< 250 characters or < 40 words) or items containing truncation markers (`[+\d+ chars]`, `... [Read more]`, `Continue reading`). These require an external web scrape.
- **Substantive Content**: Sustained text (>= 250 characters and >= 40 words without truncation flags). The existing text is utilized directly, avoiding network overhead.
- **Configurable**: Configured via `EXTRACTION_MIN_CONTENT_CHARS` and `EXTRACTION_MIN_CONTENT_WORDS`.

---

## 4. Article Fetching Layer
When external retrieval is necessary:
- **HTTP Client**: Asynchronous requests powered by `httpx.AsyncClient`.
- **Timeouts**: Strict timeout (default 10.0s) prevents hanging requests.
- **Redirects**: Follows redirects safely up to a configurable maximum (default 5).
- **Security & SSRF Protection**: Validates HTTP/HTTPS schemes; rejects private IP ranges (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`, `127.0.0.1`, `169.254.169.254`, `::1`, and `.local`/`.internal` domains).
- **Respectful Headers**: Standard identification `ESTD-ArticleExtractor/1.0 (+https://estd.ai/bot)`.
- **Payload Bounds**: Enforces maximum HTML size (default 5 MB) and validates HTML Content-Types.

---

## 5. Article Extraction Strategy
Extraction parses HTML using `BeautifulSoup` (`html.parser`) across multiple fallback tiers:
1. **Schema.org JSON-LD**: Prioritizes `NewsArticle` / `Article` structured data if `articleBody` is available.
2. **Noise Removal**: Decomposes `<script>`, `<style>`, `<nav>`, `<header>`, `<footer>`, `<aside>`, `<form>`, and elements with noise classes (ads, sidebars, comments, popups, cookie notices).
3. **Semantic Tags**: Targets `<article>`, `<main>`, and `[role="main"]` containers.
4. **Candidate Heuristics**: Evaluates `<div>` / `<section>` tags with classes/ids matching article containers (`story-content`, `article-body`, `entry-content`, etc.), scoring by paragraph count, text density, and low link density.
5. **Metadata Extraction**: Gathers canonical URL (`link[rel=canonical]`, `og:url`), author (`meta[name=author]`, `article:author`, JSON-LD), published timestamp (normalized to ISO 8601 UTC), lead image (`og:image`, `twitter:image`), and headline (`og:title`, `<title>`, `<h1>`).

---

## 6. Output Contract (`ExtractedArticle`)
Preserves all Step 1 metadata while augmenting with extraction outcomes:

| Field | Type | Description |
|---|---|---|
| `title` | `str` | Article headline (extracted or Step 1 original) |
| `description` | `Optional[str]` | Original Step 1 synopsis/snippet |
| `url` | `str` | Original article URL from Step 1 |
| `canonical_url` | `Optional[str]` | Canonical URL discovered during extraction |
| `source_name` | `Optional[str]` | Publisher or site name |
| `source_type` | `str` | Provider identifier (`gnews`, `newsdata`, `rss`) |
| `author` | `Optional[str]` | Article author if identified |
| `published_at` | `Optional[str]` | ISO 8601 UTC timestamp of publication |
| `category` | `str` | One of the 5 official ESTD categories |
| `image_url` | `Optional[str]` | Primary lead image URL |
| `collected_at` | `str` | ISO 8601 UTC timestamp when Step 1 collected the item |
| `content` | `Optional[str]` | Extracted full article body text |
| `extraction_status` | `ExtractionStatus` | `CONTENT_ALREADY_AVAILABLE`, `EXTRACTED`, `EXTRACTION_FAILED` |
| `extraction_method` | `Optional[ExtractionMethod]` | `existing_source_content` or `article_web_extraction` |
| `extracted_at` | `str` | ISO 8601 UTC timestamp of Step 2 processing |
| `error_message` | `Optional[str]` | Diagnostic error message if extraction failed |

---

## 7. Failure Handling & Isolation
External network and webpage failures never crash the application or abort pipeline execution:
- **Timeouts / DNS / Connection drops**: Caught and mapped to `EXTRACTION_FAILED` with informative `error_message`.
- **HTTP 4xx / 5xx**: Server errors mapped to `EXTRACTION_FAILED`.
- **Paywalls / Empty / Unextractable pages**: Handled gracefully as `EXTRACTION_FAILED` without fabricating content.
- **Batch Isolation**: Per-article isolation in `extract_batch` ensures failure in one article does not affect others.

---

## 8. API Endpoints
- `POST /api/v1/article-extraction/extract`: Extracts a single `NewsItem`.
- `POST /api/v1/article-extraction/extract-batch`: Extracts a batch of `NewsItems`.

---

## 9. Step 2 → Step 3 Boundary
- **Step 2 Responsibility**: Fetch webpage and extract article body and metadata.
- **Step 3 Responsibility**: Content cleaning, advertisement snippet scrubbing, Markdown normalization, and deduplication.
- Step 2 strictly refrains from semantic text normalization, duplicate detection, or database persistence.
