# ESTD — Desktop News Intelligence Web Application

> **“News that fits in one breath. Videos that finish the story.”**

ESTD is an editorial, video-first, dark-mode desktop news intelligence application designed to eliminate cognitive overload and platform fragmentation. It synthesizes complex stories into concise, conversational headlines, single-paragraph executive briefs, verifiable impact metrics, multi-perspective video rails, 4-beat development timelines, and cultural sentiment pulses.

---

## 1. Product & Architecture Overview

The frontend connects directly and securely to the ESTD FastAPI backend (`http://localhost:8000`) and PostgreSQL knowledge source (port `5433`).

```
                    ┌────────────────────────────────────────────────────────┐
                    │               ESTD Frontend Web App                    │
                    │   React 18 + Vite 6 + React Router 7 + Lucide Icons    │
                    └───────────┬────────────────────────────────┬───────────┘
                                │                                │
                        REST API Requests             Live Pipeline Polling
                                │                                │
                                ▼                                ▼
                    ┌────────────────────────────────────────────────────────┐
                    │               ESTD FastAPI Backend (8000)              │
                    │      Steps 1–8 News Intelligence Pipeline Orchestrator  │
                    └───────────┬────────────────────────────────┬───────────┘
                                │                                │
                                ▼                                ▼
                    ┌───────────────────────┐        ┌───────────────────────┐
                    │ PostgreSQL Database   │        │ Google Drive / Docs   │
                    │ 5 Categories, 37 Subs │        │ ESTD CONTENT Folder   │
                    └───────────────────────┘        └───────────────────────┘
```

- **Zero Direct Database/MCP Access in Browser**: The browser never connects directly to PostgreSQL, Gemini, GNews, or Google Drive. All communication flows through authorized FastAPI backend endpoints.
- **Strict Idempotency**: Normal page rendering never triggers redundant Gemini generation or duplicate Google Document creation.

---

## 2. Canonical Category Taxonomy

The application strictly implements the 5 canonical top-level categories and all 37 subcategories:

| Category | Accent Color | Token | Subcategories Count | Canonical Code |
| :--- | :--- | :--- | :--- | :--- |
| **Tech** | Cyan `#00E5FF` | `--cat-cyan` | 7 subcategories | `TECH` |
| **Entertainment** | Magenta `#FF20B8` | `--cat-magenta` | 8 subcategories | `ENT` |
| **Business & Finance** | Violet `#A855F7` | `--cat-violet` | 6 subcategories | `BIZ_FIN` |
| **Developments** | Amber `#FFB020` | `--cat-amber` | 7 subcategories | `DEV` |
| **Sports** | Lime `#B8FF3B` | `--cat-lime` | 9 subcategories | `SPORTS` |

---

## 3. The 6-Element Story Object

Every story is anchored in the canonical 6-part editorial standard:
1. **Conversational Headline**: Capped at ~12 words, spoken-language cadence.
2. **One-Paragraph Intelligence Brief**: Single paragraph explaining what happened, context, and why it matters.
3. **Verifiable Impact Metrics**: Source-grounded financial figures, percentages, and volume numbers.
4. **Video Perspectives Rail**: Multi-angle coverage (Official Announcement, Expert Explainer, Field Reaction).
5. **Context in Four Beats**: 4-milestone development timeline.
6. **Cultural Pulse**: Social sentiment and industry implications.

---

## 4. Route Map

| Path | Component | Description |
| :--- | :--- | :--- |
| `/` | `HomePage` | Bento layout with Hero Story, Supporting Cards, Video Rail, Latest Briefs, Topic Hubs |
| `/category/:categorySlug` | `CategoryPage` | Reusable category template with subcategory chips, featured card, and briefs |
| `/category/:categorySlug/:subcategorySlug` | `CategoryPage` | Direct subcategory intelligence view (e.g. `/category/tech/artificial-intelligence`) |
| `/story/:storyId` | `StoryObject` | Full canonical 6-element Story Object view with Audio Listen, Drive Doc, and Share |
| `/watch/:storyId` | `WatchPage` | Video-first perspective player with multi-angle perspective switcher |
| `/hub` | `TopicHubPage` | Topic & Entity hubs directory |
| `/hub/:entitySlug` | `TopicHubPage` | Dedicated entity hub (e.g. OpenAI, boAt, Formula 1) with timeline and related briefs |
| `/live` | `LivePage` | Real-time intelligence feed with operational freshness indicators |
| `/saved` | `SavedPage` | Locally persisted bookmarks with un-save action and empty state |
| `/you` | `YouPage` | User preferences, followed categories, speech rate, and system diagnostics |
| `/search` | `SearchPage` | Ask ESTD search interface querying real backend articles and subcategories |

---

## 5. Design Tokens

Defined centrally in `src/index.css`:
- **Ink Background**: `#07080B`
- **Surface**: `#0D0F17`
- **Card Background**: `#12141C` (Hover: `#191D2A`)
- **Borders**: `rgba(255, 255, 255, 0.08)` (Hover: `0.16`, Focus: `0.28`)
- **Category Accents**:
  - Entertainment: `#FF20B8`
  - Sports: `#B8FF3B`
  - Tech: `#00E5FF`
  - Developments: `#FFB020`
  - Business & Finance: `#A855F7`
- **Typography Scale**: Satoshi / Inter fallback with high legibility on dark surfaces.

---

## 6. Development & Build Commands

```bash
# 1. Start the FastAPI backend
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload

# 2. Start the Vite React frontend
cd frontend
npm run dev

# 3. Production build check
npm run build
```

---

## 7. Verification Results

- **Vite Production Build**: `✓ built in 36.62s` with 0 errors.
- **Backend API Connectivity**: `GET /health` (`status: ok`), `GET /pipeline/articles`, `GET /api/v1/knowledge/categories`, `GET /api/v1/knowledge/subcategories` fully operational.
- **Browser Subagent Testing**: Executed across all 10 checklist items (Home, Sports filter, Tech category, AI subcategory, Story Object 6 elements, Watch perspective switcher, Pipeline Inspector modal, Search for boAt, Saved, You). All interactions confirmed functional and responsive.
