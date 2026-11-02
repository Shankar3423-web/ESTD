# ESTD — Step 5: Knowledge Source / PostgreSQL Persistence

## 1. Overview & Objective

Step 5 represents the persistent **Knowledge Source** of the ESTD (news/content intelligence pipeline).
It receives **UNIQUE**, cleaned, validated news articles produced by previous stages (Steps 1–4) and permanently persists them into PostgreSQL 17 as the canonical ESTD knowledge source for downstream retrieval and MCP access.

```
Step 1: Source Collection (GNews, NewsData.io, RSS)
   ↓
Step 2: Article Extraction
   ↓
Step 3: Content Cleaning / Normalization
   ↓
Step 4: Duplicate Detection (Exact Hash, URL Normalization, TF-IDF Cosine Similarity)
   ↓ [UNIQUE ARTICLES ONLY]
Step 5: KNOWLEDGE SOURCE / POSTGRESQL PERSISTENCE (estd_knowledge)
   ↓
Step 6: MCP / Knowledge Access (Future)
```

---

## 2. Database Configuration

The ESTD Knowledge Source runs on PostgreSQL 17:

| Parameter | Configuration | Environment Variable |
|---|---|---|
| **Host** | `localhost` | `POSTGRES_HOST` |
| **Port** | `5433` | `POSTGRES_PORT` |
| **User** | `postgres` | `POSTGRES_USER` |
| **Password** | Configured in `.env` | `POSTGRES_PASSWORD` |
| **Database** | `estd_knowledge` | `POSTGRES_DB` |
| **Connection URL** | `postgresql://postgres:root@localhost:5433/estd_knowledge` | `DATABASE_URL` |

> [!IMPORTANT]
> Passwords and connection credentials are NEVER hardcoded into source code. All connection settings are loaded dynamically via `backend/common/config/settings.py` from `.env`. All logging automatically redacts passwords.

---

## 3. Database Architecture & Schema

### A. Reference Table: `categories`
Stores the exact 5 canonical ESTD categories seeded idempotently:
1. `Artificial Intelligence` (slug: `artificial-intelligence`)
2. `Technology` (slug: `technology`)
3. `Business` (slug: `business`)
4. `Education` (slug: `education`)
5. `Science` (slug: `science`)

```sql
CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    slug VARCHAR(100) NOT NULL UNIQUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL
);
```

### B. Core Knowledge Table: `news_articles`
Stores unique articles adhering strictly to the pipeline data contract:

```sql
CREATE TABLE news_articles (
    id BIGSERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    content TEXT NOT NULL,
    url TEXT NOT NULL,
    normalized_url VARCHAR(1024) NOT NULL UNIQUE,
    content_hash VARCHAR(64) NOT NULL UNIQUE,
    source_name VARCHAR(255),
    source_type VARCHAR(100) NOT NULL,
    author VARCHAR(255),
    published_at TIMESTAMP WITH TIME ZONE,
    category VARCHAR(100) NOT NULL,
    category_id INTEGER NOT NULL REFERENCES categories(id) ON DELETE RESTRICT,
    image_url TEXT,
    collected_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    CONSTRAINT ck_news_articles_title_not_empty CHECK (length(trim(title)) > 0),
    CONSTRAINT ck_news_articles_url_not_empty CHECK (length(trim(url)) > 0),
    CONSTRAINT ck_news_articles_content_not_empty CHECK (length(trim(content)) > 0),
    CONSTRAINT ck_news_articles_valid_category CHECK (
        category IN ('Artificial Intelligence', 'Technology', 'Business', 'Education', 'Science')
    )
);
```

### C. Database Integrity & Duplicate Protection
1. **Normalized URL Uniqueness (`uq_news_articles_normalized_url`)**: Prevents duplicate stories from the same canonical URL.
2. **Content Hash Uniqueness (`uq_news_articles_content_hash`)**: Prevents duplicate stories from different sources with identical normalized text.
3. **Category Foreign Key (`fk_news_articles_category_id`)**: Enforces relational consistency with the `categories` reference table.
4. **Category Check Constraint (`ck_news_articles_valid_category`)**: Database-level check constraint preventing any non-canonical category (e.g. Sports, Politics).

---

## 4. Database Setup & Migrations

### Running Migrations via Alembic
```bash
cd backend
.\.venv\Scripts\python.exe -m alembic upgrade head
```

Or programmatically in Python:
```python
from backend.database.migrations.runner import run_migrations
run_migrations("head")
```

### Database Initialization & Verification
```python
from backend.database.initializer import setup_knowledge_database
setup_knowledge_database()
```

---

## 5. API Endpoints Reference

Base URL: `http://127.0.0.1:8000/api/v1/knowledge`

| Method | Endpoint | Description | Status Code |
|---|---|---|---|
| `GET` | `/health` | Verify database connection and report server details | `200 OK` |
| `GET` | `/categories` | List the 5 canonical reference categories | `200 OK` |
| `POST` | `/articles` | Persist a unique article or Step 4 `DuplicateCheckResult` | `201 Created` / `409 Conflict` |
| `GET` | `/articles/{id}` | Retrieve article by its primary key ID | `200 OK` / `404 Not Found` |
| `GET` | `/articles` | Query paginated articles with category, source, date filtering | `200 OK` / `400 Bad Request` |
| `DELETE` | `/articles/{id}` | Delete an article from knowledge source | `200 OK` / `404 Not Found` |

---

## 6. Postman Testing Guide

### TEST 1: Database Health Check
- **Method:** `GET`
- **URL:** `http://127.0.0.1:8000/api/v1/knowledge/health`
- **Expected Response (200 OK):**
```json
{
  "status": "healthy",
  "database": "connected",
  "database_name": "estd_knowledge",
  "server_version": "PostgreSQL 17.5"
}
```

---

### TEST 2: Create Valid Article
- **Method:** `POST`
- **URL:** `http://127.0.0.1:8000/api/v1/knowledge/articles`
- **Headers:** `Content-Type: application/json`
- **Body:**
```json
{
  "title": "Quantum Computing Lab Unveils 1000-Qubit Processor",
  "description": "Commercial availability projected for quantum simulation.",
  "content": "Researchers have successfully operated a 1000-qubit quantum processor with high gate fidelity and error suppression.",
  "url": "https://example.com/postman-quantum-1000",
  "source_name": "Tech Times",
  "source_type": "rss",
  "author": "Dr. Quantum",
  "published_at": "2026-10-05T08:00:00Z",
  "category": "Technology"
}
```
- **Expected Response (201 Created):**
```json
{
  "status": "success",
  "data": {
    "id": 1,
    "title": "Quantum Computing Lab Unveils 1000-Qubit Processor",
    "category": "Technology",
    "normalized_url": "https://example.com/postman-quantum-1000",
    "content_hash": "6d1ae81d5109fec71350a4e174f4e833214f2b9c44f6b2d93229bc9a45821cc2"
  }
}
```

---

### TEST 3: Retrieve Article by ID
- **Method:** `GET`
- **URL:** `http://127.0.0.1:8000/api/v1/knowledge/articles/1`
- **Expected Response (200 OK):**
```json
{
  "status": "success",
  "data": {
    "id": 1,
    "title": "Quantum Computing Lab Unveils 1000-Qubit Processor",
    "category": "Technology"
  }
}
```

---

### TEST 4: List Articles
- **Method:** `GET`
- **URL:** `http://127.0.0.1:8000/api/v1/knowledge/articles`
- **Expected Response (200 OK):**
```json
{
  "status": "success",
  "data": {
    "items": [...],
    "pagination": {
      "page": 1,
      "page_size": 10,
      "total_items": 1,
      "total_pages": 1,
      "has_next": false,
      "has_prev": false
    }
  }
}
```

---

### TEST 5: Filter Category: Science
- **Method:** `GET`
- **URL:** `http://127.0.0.1:8000/api/v1/knowledge/articles?category=Science`
- **Expected Response (200 OK):**
Returns only articles with `category == "Science"`.

---

### TEST 6: Filter Category: Technology
- **Method:** `GET`
- **URL:** `http://127.0.0.1:8000/api/v1/knowledge/articles?category=Technology`
- **Expected Response (200 OK):**
Returns only articles with `category == "Technology"`.

---

### TEST 7: Invalid Category Validation Error
- **Method:** `GET`
- **URL:** `http://127.0.0.1:8000/api/v1/knowledge/articles?category=Sports`
- **Expected Response (400 Bad Request):**
```json
{
  "error": {
    "code": "INVALID_CATEGORY",
    "message": "Category 'Sports' is not supported."
  }
}
```

---

### TEST 8: Duplicate Article Rejection
- **Method:** `POST`
- **URL:** `http://127.0.0.1:8000/api/v1/knowledge/articles`
- **Body:** (Submit the exact same URL/content from TEST 2)
- **Expected Response (409 Conflict):**
```json
{
  "error": {
    "code": "DUPLICATE_ARTICLE",
    "message": "Cannot persist duplicate article. Duplicate detected by normalized_url: 'https://example.com/postman-quantum-1000'"
  }
}
```

---

### TEST 9: Pagination
- **Method:** `GET`
- **URL:** `http://127.0.0.1:8000/api/v1/knowledge/articles?page=1&page_size=1`
- **Expected Response (200 OK):**
Returns exactly 1 item in `items`, with `page: 1`, `page_size: 1`, `has_next: true`.

---

### TEST 10: Five Category Coverage
- **Method:** `GET`
- **URL:** `http://127.0.0.1:8000/api/v1/knowledge/categories`
- **Expected Response (200 OK):**
```json
{
  "status": "success",
  "total": 5,
  "items": [
    {"id": 1, "name": "Artificial Intelligence", "slug": "artificial-intelligence"},
    {"id": 2, "name": "Technology", "slug": "technology"},
    {"id": 3, "name": "Business", "slug": "business"},
    {"id": 4, "name": "Education", "slug": "education"},
    {"id": 5, "name": "Science", "slug": "science"}
  ]
}
```

---

## 7. Manual Verification in pgAdmin

Open pgAdmin 4 or connect via any PostgreSQL client to:
- **Host:** `localhost`
- **Port:** `5433`
- **Database:** `estd_knowledge`
- **Username:** `postgres`

### Tree Navigation:
`PostgreSQL 17` → `Databases` → `estd_knowledge` → `Schemas` → `public` → `Tables`

Expected Tables:
- `alembic_version`
- `categories`
- `news_articles`
- `estd_duplicate_index`

### Verification SQL Queries:
```sql
-- 1. Verify 5 canonical categories
SELECT id, name, slug, created_at 
FROM categories 
ORDER BY id;

-- 2. Verify stored articles count by category
SELECT category, count(*) as article_count 
FROM news_articles 
GROUP BY category;

-- 3. Verify unique constraints on news_articles
SELECT conname, contype 
FROM pg_constraint 
WHERE conrelid = 'news_articles'::regclass;

-- 4. Query recent articles
SELECT id, title, category, source_name, published_at, created_at 
FROM news_articles 
ORDER BY created_at DESC 
LIMIT 10;
```
