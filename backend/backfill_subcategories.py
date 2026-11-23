"""Backfill and resolve all missing/non-canonical subcategories in PostgreSQL news_articles."""
import sys
from pathlib import Path

# Ensure paths
backend_dir = Path(__file__).resolve().parent
project_root = backend_dir.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from backend.common.logging.logger import logger
from backend.common.taxonomy.subcategory_classifier import (
    SUBCATEGORY_ID_MAP,
    classify_article_subcategory,
)
from backend.database.connection.session import get_db_session
from backend.database.models.news_article import NewsArticle
from backend.pipeline.router import clear_dashboard_cache


def backfill_all_subcategories(dry_run: bool = False):
    """Scan all news_articles and ensure 100% have canonical subcategory and subcategory_id."""
    with get_db_session() as session:
        articles = session.query(NewsArticle).all()
        print(f"Total articles in DB: {len(articles)}")

        updated_count = 0
        distribution: dict = {}

        for art in articles:
            valid_subs = SUBCATEGORY_ID_MAP.get(art.category, {})
            needs_update = False

            if not art.subcategory or art.subcategory not in valid_subs or not art.subcategory_id:
                needs_update = True

            if needs_update:
                new_sub, new_sub_id = classify_article_subcategory(
                    category=art.category,
                    title=art.title or "",
                    content=art.content or art.description or "",
                    current_sub=art.subcategory,
                )
                print(
                    f"[{art.id}] Category: '{art.category}' | Old: '{art.subcategory}' -> New: '{new_sub}' (ID: {new_sub_id}) | Title: {art.title[:50]}..."
                )
                if not dry_run:
                    art.subcategory = new_sub
                    art.subcategory_id = new_sub_id

                updated_count += 1
                key = f"{art.category} > {new_sub}"
                distribution[key] = distribution.get(key, 0) + 1

        if not dry_run and updated_count > 0:
            session.commit()
            clear_dashboard_cache()
            print(f"\nSUCCESS: Committed {updated_count} subcategory updates to PostgreSQL!")
        else:
            print(f"\nDRY RUN: {updated_count} articles need update.")

        print("\nUpdated Distribution Breakdown:")
        for k, v in sorted(distribution.items()):
            print(f"  {k}: {v}")


if __name__ == "__main__":
    dry = "--dry-run" in sys.argv
    backfill_all_subcategories(dry_run=dry)
