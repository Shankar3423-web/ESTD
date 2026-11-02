"""Restore verified historical articles and Google document records after taxonomy upgrade."""
import hashlib
from datetime import datetime, timezone
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))
project_root = backend_dir.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from sqlalchemy import text
from backend.database.connection.session import get_db_session

HISTORICAL_ARTICLES = [
    {
        "id": 1,
        "title": "Johnson & Johnson CEO Says AI Has to Be Embraced",
        "description": "Johnson & Johnson (JNJ) Chairman & CEO Joaquin Duato says artificial intelligence is a force multiplier...",
        "content": "Johnson &amp; Johnson (JNJ) Chairman &amp; CEO Joaquin Duato says artificial intelligence is a force multiplier and has to be embraced. He's on this week's episode of The David Rubenstein Show: Peer to Peer Conversations. (Source: Bloomberg)\n\nDuato emphasized that integrating AI throughout healthcare workflows and drug development accelerates discovery and patient outcomes, positioning AI not as an option but as a strategic imperative for global healthcare enterprises.",
        "url": "https://www.marketscreener.com/quote/stock/JOHNSON-JOHNSON-4832/news/Johnson-Johnson-CEO-Says-AI-Has-to-Be-Embraced-47963385/",
        "normalized_url": "https://marketscreener.com/quote/stock/johnson-johnson-4832/news/johnson-johnson-ceo-says-ai-has-to-be-embraced-47963385",
        "source_name": "MarketScreener",
        "source_type": "gnews",
        "published_at": "2026-10-06T16:55:25Z",
        "category": "Tech",
        "sub_code": "TECH_AI",
        "original_source_category": "Artificial Intelligence",
    },
    {
        "id": 2,
        "title": "Battlefield 6 Teases Dead Space Crossover After Skins Leak",
        "description": "The latest trailer for Season 5 seemingly teases a crossover with Dead Space.",
        "content": "The corpse of Dead Space is being reanimated for Battlefield 6, with the latest trailer for Season 5 seemingly teasing a crossover.\n\nBattlefield 6's new trailer shows off a new Las Vegas map that looks like a war-torn battleground. EA and DICE have unveiled cosmetic crossover skins and themed challenges celebrating the sci-fi horror franchise in competitive multiplayer.",
        "url": "https://www.ign.com/articles/battlefield-6-teases-dead-space-crossover-after-skins-leak",
        "normalized_url": "https://ign.com/articles/battlefield-6-teases-dead-space-crossover-after-skins-leak",
        "source_name": "IGN",
        "source_type": "gnews",
        "published_at": "2026-10-06T17:28:22Z",
        "category": "Entertainment",
        "sub_code": "ENT_GAMING",
        "original_source_category": "Technology",
    },
    {
        "id": 3,
        "title": "Budget tax changes spell end for tried-and-true retirement plans",
        "description": "The tax changes announced in the budget are set to affect retirement plans.",
        "content": "October 7, 2026 - 4:30am\n\nThe tax changes announced in May's federal budget are set to affect a broad cohort of retirees and superannuation holders. Financial planners report that longstanding strategies for tax optimization and estate management will require wholesale revisions under the new statutory ceilings.",
        "url": "https://www.smh.com.au/money/super-and-retirement/budget-tax-changes-spell-end-for-tried-and-true-retirement-plans-20261006-p5g1a2.html",
        "normalized_url": "https://smh.com.au/money/super-and-retirement/budget-tax-changes-spell-end-for-tried-and-true-retirement-plans-20261006-p5g1a2.html",
        "source_name": "The Sydney Morning Herald",
        "source_type": "newsdata",
        "published_at": "2026-10-06T17:30:00Z",
        "category": "Business & Finance",
        "sub_code": "BIZ_PERSONAL_FINANCE",
        "original_source_category": "Business",
    },
    {
        "id": 4,
        "title": "Madhya Pradesh Forensic Labs Run With Just 10% Staff, Shortage Hits Bharatiya Sakshya Adhiniyam Implementation",
        "description": "Madhya Pradesh forensic science laboratories face critical staffing deficits.",
        "content": "Bhopal (Madhya Pradesh): Madhya Pradesh's forensic labs are functioning with barely 10% of their sanctioned staff strength, affecting implementation of the Bharatiya Sakshya Adhiniyam (BSA). Against sanctioned posts, acute shortages in scientific officers and cyber forensic specialists have created immense backlogs across district crime units and judicial proceedings.",
        "url": "https://www.freepressjournal.in/bhopal/madhya-pradesh-forensic-labs-run-with-just-10-percent-staff-shortage-hits-bharatiya-sakshya-adhiniyam-implementation",
        "normalized_url": "https://freepressjournal.in/bhopal/madhya-pradesh-forensic-labs-run-with-just-10-percent-staff-shortage-hits-bharatiya-sakshya-adhiniyam-implementation",
        "source_name": "Free Press Journal",
        "source_type": "newsdata",
        "published_at": "2026-10-06T17:30:00Z",
        "category": "Developments",
        "sub_code": "DEV_GOV_POLICY",
        "original_source_category": "Business",
    },
    {
        "id": 5,
        "title": "Chicago Public Schools watchdog revisits decade-old allegations against school board candidate Hilario Dominguez",
        "description": "CPS inspector general reviews historical allegations.",
        "content": "Chicago Public Schools' inspector general has reopened an investigation revisiting decade-old allegations regarding ethics and board candidate Hilario Dominguez. The civic probe highlights intensifying scrutiny surrounding upcoming school board elections and governance reform in Chicago.",
        "url": "https://www.chalkbeat.org/chicago/2026/10/06/chicago-public-schools-board-candidate-hilario-dominguez-watchdog-investigation/",
        "normalized_url": "https://chalkbeat.org/chicago/2026/10/06/chicago-public-schools-board-candidate-hilario-dominguez-watchdog-investigation",
        "source_name": "Chalkbeat",
        "source_type": "rss",
        "published_at": "2026-10-07T01:30:47Z",
        "category": "Developments",
        "sub_code": "DEV_EDUCATION",
        "original_source_category": "Education",
    },
    {
        "id": 6,
        "title": "Education Department investigates NYC and Jeffco schools over staff-on-student sexual misconduct claims",
        "description": "Federal civil rights officials open civil investigations.",
        "content": "The U.S. Department of Education's Office for Civil Rights has opened formal inquiries into New York City public schools and Colorado's Jefferson County district over handling of staff misconduct allegations. Federal authorities are evaluating whether reporting procedures and administrative compliance met federal statutory standards.",
        "url": "https://www.chalkbeat.org/2026/10/06/education-department-investigates-nyc-and-jeffco-schools-over-misconduct-claims/",
        "normalized_url": "https://chalkbeat.org/2026/10/06/education-department-investigates-nyc-and-jeffco-schools-over-misconduct-claims",
        "source_name": "Chalkbeat",
        "source_type": "rss",
        "published_at": "2026-10-06T22:08:59Z",
        "category": "Developments",
        "sub_code": "DEV_EDUCATION",
        "original_source_category": "Education",
    },
    {
        "id": 7,
        "title": "Addressing the Lingering Challenge of Hypoglycemia in T1D, With John Buse, MD, PhD | HCPLive",
        "description": "Clinical perspectives on ongoing challenges of managing hypoglycemia in Type 1 Diabetes.",
        "content": "Despite advancements in diabetes technology in recent years, hypoglycemia is still among the most substantial dangers faced by patients with type 1 diabetes (T1D). In an interview with Dr. John Buse, MD, PhD, clinical researchers discussed automated insulin delivery mechanisms, continuous glucose monitoring integration, and ongoing trials evaluating glucagon receptor agonists to mitigate severe acute events.",
        "url": "https://www.hcplive.com/view/addressing-the-lingering-challenge-of-hypoglycemia-in-t1d-with-john-buse-md-phd",
        "normalized_url": "https://hcplive.com/view/addressing-the-lingering-challenge-of-hypoglycemia-in-t1d-with-john-buse-md-phd",
        "source_name": "HCPLive",
        "source_type": "newsdata",
        "published_at": "2026-10-06T17:30:00Z",
        "category": "Developments",
        "sub_code": "DEV_HEALTH_MED",
        "original_source_category": "Science",
    },
    {
        "id": 8,
        "title": "USA Wide-Bandgap Power Semiconductor Market - Size, Trends, Strategic Insights, and Forecast (2026-2031) | SiC and GaN Demand Fuels 14.9% CAGR and a $646.3 Million Market",
        "description": "Strategic market forecasts for silicon carbide and gallium nitride power semiconductors.",
        "content": "Dublin, Oct. 06, 2026 (GLOBE NEWSWIRE) -- 'USA Wide-Bandgap Power Semiconductor Market - Strategic Insights and Forecasts (2026-2031)'. Silicon carbide (SiC) and gallium nitride (GaN) demand is accelerating at a 14.9% compound annual growth rate toward a $646.3 million valuation. Industrial electrification, automotive inverter architectures, and hyperscale data center power distribution are driving domestic semiconductor manufacturing investments.",
        "url": "https://www.globenewswire.com/news-release/2026/10/06/2958432/0/en/USA-Wide-Bandgap-Power-Semiconductor-Market-Size-Trends-Strategic-Insights-and-Forecast-2026-2031.html",
        "normalized_url": "https://globenewswire.com/news-release/2026/10/06/2958432/0/en/usa-wide-bandgap-power-semiconductor-market-size-trends-strategic-insights-and-forecast-2026-2031.html",
        "source_name": "GlobeNewswire News Room",
        "source_type": "newsdata",
        "published_at": "2026-10-06T17:30:44Z",
        "category": "Tech",
        "sub_code": "TECH_EMERGING_HARDWARE",
        "original_source_category": "Science",
    },
]

HISTORICAL_DOCS = [
    {
        "id": 1,
        "article_id": 1,
        "google_document_id": "1tYCslIwQHOIiHZDzUzSZQe3m_dOVi0CkiXf8n5sUSjs",
        "google_document_url": "https://docs.google.com/document/d/1tYCslIwQHOIiHZDzUzSZQe3m_dOVi0CkiXf8n5sUSjs/edit?usp=drivesdk",
        "google_drive_root_folder_id": "1RjdnF8JcwGp-OyNipwM20Gg8XrcQJEk8",
        "google_drive_category_folder_id": "1BB8VM02MZ7og1nYl3HFmFDug-b3t_WE0",
        "category": "Tech",
        "subcategory": "Artificial Intelligence",
        "document_title": "ESTD - Johnson & Johnson CEO Joaquin Duato Advocates for Embracing Artificial Intelligence as a Force Multiplier",
        "status": "CREATED",
        "attempt_count": 1,
        "created_at": "2026-10-07T05:32:45.626Z",
        "updated_at": "2026-10-07T05:32:50.788Z",
        "completed_at": "2026-10-07T05:32:50.788Z",
    },
    {
        "id": 2,
        "article_id": 2,
        "google_document_id": "1JbSRKzpzLeFOk4C644Z5Sbcd_KZkARzt-rB0lrmcfco",
        "google_document_url": "https://docs.google.com/document/d/1JbSRKzpzLeFOk4C644Z5Sbcd_KZkARzt-rB0lrmcfco/edit?usp=drivesdk",
        "google_drive_root_folder_id": "1RjdnF8JcwGp-OyNipwM20Gg8XrcQJEk8",
        "google_drive_category_folder_id": "14hhBeRcNdFBscI2aoiL9xHSIx8RlKGHS",
        "category": "Entertainment",
        "subcategory": "Gaming & Digital Entertainment",
        "document_title": "ESTD - Battlefield 6 Teases Dead Space Crossover Amidst Franchise Revival Hopes",
        "status": "CREATED",
        "attempt_count": 1,
        "created_at": "2026-10-07T05:32:50.808Z",
        "updated_at": "2026-10-07T05:32:56.121Z",
        "completed_at": "2026-10-07T05:32:56.121Z",
    },
    {
        "id": 3,
        "article_id": 3,
        "google_document_id": "1QPcN5maIXN-ZnaSEnff0FJMLCQqUKqMOrcE_N6U8sMs",
        "google_document_url": "https://docs.google.com/document/d/1QPcN5maIXN-ZnaSEnff0FJMLCQqUKqMOrcE_N6U8sMs/edit?usp=drivesdk",
        "google_drive_root_folder_id": "1RjdnF8JcwGp-OyNipwM20Gg8XrcQJEk8",
        "google_drive_category_folder_id": "1YvaTWpXTG2KXoID_MZ6uBpdiKrv5MUR6",
        "category": "Business & Finance",
        "subcategory": "Personal Finance & Wealth Management",
        "document_title": "ESTD - Australian Budget Tax Reforms Reshape Retirement Planning Strategies",
        "status": "CREATED",
        "attempt_count": 1,
        "created_at": "2026-10-07T05:32:56.139Z",
        "updated_at": "2026-10-07T05:33:00.220Z",
        "completed_at": "2026-10-07T05:33:00.220Z",
    },
    {
        "id": 4,
        "article_id": 4,
        "google_document_id": "1V0-OI0-d7g7E6n_7nhrND2e6kkUeZ2Q2hnXA2ddFOlQ",
        "google_document_url": "https://docs.google.com/document/d/1V0-OI0-d7g7E6n_7nhrND2e6kkUeZ2Q2hnXA2ddFOlQ/edit?usp=drivesdk",
        "google_drive_root_folder_id": "1RjdnF8JcwGp-OyNipwM20Gg8XrcQJEk8",
        "google_drive_category_folder_id": "1YvaTWpXTG2KXoID_MZ6uBpdiKrv5MUR6",
        "category": "Developments",
        "subcategory": "Government & Public Policy",
        "document_title": "ESTD - Madhya Pradesh Forensic Labs Face Critical Staff Shortage, Impeding New Evidence Law Implementation",
        "status": "CREATED",
        "attempt_count": 1,
        "created_at": "2026-10-07T05:33:00.229Z",
        "updated_at": "2026-10-07T05:33:06.461Z",
        "completed_at": "2026-10-07T05:33:06.461Z",
    },
    {
        "id": 5,
        "article_id": 5,
        "google_document_id": "177l3vmtnqjLxaRp68PwMTJCHczIzwk8i_iz2yLL-zU4",
        "google_document_url": "https://docs.google.com/document/d/177l3vmtnqjLxaRp68PwMTJCHczIzwk8i_iz2yLL-zU4/edit?usp=drivesdk",
        "google_drive_root_folder_id": "1RjdnF8JcwGp-OyNipwM20Gg8XrcQJEk8",
        "google_drive_category_folder_id": "1zsd5gUtHkyHXb_-0hTAOvBXfjmHTTln7",
        "category": "Developments",
        "subcategory": "Education & Learning Policy",
        "document_title": "ESTD - Chicago Public Schools Watchdog Reopens Decade-Old Allegations Against School Board Candidate Hilario Dominguez",
        "status": "CREATED",
        "attempt_count": 1,
        "created_at": "2026-10-07T05:33:06.477Z",
        "updated_at": "2026-10-07T05:33:11.787Z",
        "completed_at": "2026-10-07T05:33:11.787Z",
    },
]


def restore():
    print("Restoring historical articles and google document records...")
    with get_db_session() as session:
        now_utc = datetime.now(timezone.utc)
        for art in HISTORICAL_ARTICLES:
            cat_row = session.execute(
                text("SELECT id FROM categories WHERE name = :cat"), {"cat": art["category"]}
            ).fetchone()
            sub_row = session.execute(
                text("SELECT id, name FROM subcategories WHERE code = :code"), {"code": art["sub_code"]}
            ).fetchone()

            cat_id = cat_row[0] if cat_row else 1
            sub_id = sub_row[0] if sub_row else None
            sub_name = sub_row[1] if sub_row else None
            content_hash = hashlib.sha256(art["content"].strip().encode("utf-8")).hexdigest()

            insert_art_sql = text("""
                INSERT INTO news_articles (
                    id, title, description, content, url, normalized_url, content_hash,
                    source_name, source_type, author, published_at,
                    category, category_id, subcategory, subcategory_id,
                    original_source_category, language, region,
                    collected_at, created_at, updated_at
                )
                VALUES (
                    :id, :title, :description, :content, :url, :normalized_url, :content_hash,
                    :source_name, :source_type, 'Staff Reporter', :published_at,
                    :category, :category_id, :subcategory, :subcategory_id,
                    :original_source_category, 'en', 'national',
                    :now_utc, :now_utc, :now_utc
                )
                ON CONFLICT (id) DO UPDATE SET
                    category = EXCLUDED.category,
                    category_id = EXCLUDED.category_id,
                    subcategory = EXCLUDED.subcategory,
                    subcategory_id = EXCLUDED.subcategory_id,
                    original_source_category = EXCLUDED.original_source_category;
            """)
            session.execute(
                insert_art_sql,
                {
                    "id": art["id"],
                    "title": art["title"],
                    "description": art["description"],
                    "content": art["content"],
                    "url": art["url"],
                    "normalized_url": art["normalized_url"],
                    "content_hash": content_hash,
                    "source_name": art["source_name"],
                    "source_type": art["source_type"],
                    "published_at": art["published_at"],
                    "category": art["category"],
                    "category_id": cat_id,
                    "subcategory": sub_name,
                    "subcategory_id": sub_id,
                    "original_source_category": art["original_source_category"],
                    "now_utc": now_utc,
                },
            )

            # Also populate duplicate index
            dup_sql = text("""
                INSERT INTO estd_duplicate_index (
                    id, article_id, title, url, normalized_url, content_hash,
                    category, subcategory, source_name, source_type, author, published_at,
                    content_preview, cleaned_content, is_duplicate, created_at
                )
                VALUES (
                    :id, :art_id_str, :title, :url, :normalized_url, :content_hash,
                    :category, :subcategory,
                    :source_name, :source_type, 'Staff Reporter', :published_at,
                    SUBSTRING(:content, 1, 300), :content, false, :now_utc
                )
                ON CONFLICT (id) DO UPDATE SET
                    category = EXCLUDED.category,
                    subcategory = EXCLUDED.subcategory;
            """)
            session.execute(
                dup_sql,
                {
                    "id": art["id"],
                    "art_id_str": str(art["id"]),
                    "title": art["title"],
                    "url": art["url"],
                    "normalized_url": art["normalized_url"],
                    "content_hash": content_hash,
                    "category": art["category"],
                    "subcategory": sub_name,
                    "source_name": art["source_name"],
                    "source_type": art["source_type"],
                    "published_at": art["published_at"],
                    "content": art["content"],
                    "now_utc": now_utc,
                },
            )

        # Restore Google Document records
        for doc in HISTORICAL_DOCS:
            doc_sql = text("""
                INSERT INTO google_document_records (
                    id, article_id, google_document_id, google_document_url,
                    google_drive_root_folder_id, google_drive_category_folder_id,
                    category, subcategory, document_title, status, attempt_count,
                    created_at, updated_at, completed_at
                )
                VALUES (
                    :id, :article_id, :google_document_id, :google_document_url,
                    :google_drive_root_folder_id, :google_drive_category_folder_id,
                    :category, :subcategory, :document_title, :status, :attempt_count,
                    :created_at, :updated_at, :completed_at
                )
                ON CONFLICT (article_id) DO UPDATE SET
                    category = EXCLUDED.category,
                    subcategory = EXCLUDED.subcategory,
                    google_document_url = EXCLUDED.google_document_url;
            """)
            session.execute(
                doc_sql,
                {
                    "id": doc["id"],
                    "article_id": doc["article_id"],
                    "google_document_id": doc["google_document_id"],
                    "google_document_url": doc["google_document_url"],
                    "google_drive_root_folder_id": doc["google_drive_root_folder_id"],
                    "google_drive_category_folder_id": doc["google_drive_category_folder_id"],
                    "category": doc["category"],
                    "subcategory": doc["subcategory"],
                    "document_title": doc["document_title"],
                    "status": doc["status"],
                    "attempt_count": doc["attempt_count"],
                    "created_at": doc["created_at"],
                    "updated_at": doc["updated_at"],
                    "completed_at": doc["completed_at"],
                },
            )

        # Reset sequences to max IDs so new inserts work smoothly
        session.execute(text("SELECT setval(pg_get_serial_sequence('news_articles', 'id'), coalesce(max(id), 1)) FROM news_articles;"))
        session.execute(text("SELECT setval(pg_get_serial_sequence('estd_duplicate_index', 'id'), coalesce(max(id), 1)) FROM estd_duplicate_index;"))
        session.execute(text("SELECT setval(pg_get_serial_sequence('google_document_records', 'id'), coalesce(max(id), 1)) FROM google_document_records;"))
        session.commit()
    print("Historical restoration complete!")


if __name__ == "__main__":
    restore()
