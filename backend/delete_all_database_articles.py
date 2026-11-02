"""Script to cleanly delete all news articles, document records, and duplicate index records from PostgreSQL."""
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent
project_root = backend_dir.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from sqlalchemy import text
from backend.database.connection.session import get_db_session

def delete_all_articles():
    print("=" * 60)
    print("STARTING COMPLETE ARTICLE DATA DELETION FROM DATABASE")
    print("=" * 60)
    
    with get_db_session() as session:
        # Pre-deletion counts
        gdoc_count = session.execute(text("SELECT count(*) FROM google_document_records")).scalar()
        dup_count = session.execute(text("SELECT count(*) FROM estd_duplicate_index")).scalar()
        art_count = session.execute(text("SELECT count(*) FROM news_articles")).scalar()
        cat_count = session.execute(text("SELECT count(*) FROM categories")).scalar()
        subcat_count = session.execute(text("SELECT count(*) FROM subcategories")).scalar()

        print(f"Current google_document_records: {gdoc_count}")
        print(f"Current estd_duplicate_index:   {dup_count}")
        print(f"Current news_articles:           {art_count}")
        print(f"Preserving categories:           {cat_count}")
        print(f"Preserving subcategories:        {subcat_count}")
        print("-" * 60)

        # 1. Delete google_document_records (references news_articles)
        print("Deleting all google_document_records...")
        res_gdoc = session.execute(text("DELETE FROM google_document_records"))
        print(f"Deleted {res_gdoc.rowcount} rows from google_document_records.")

        # 2. Delete duplicate index entries
        print("Deleting all estd_duplicate_index records...")
        res_dup = session.execute(text("DELETE FROM estd_duplicate_index"))
        print(f"Deleted {res_dup.rowcount} rows from estd_duplicate_index.")

        # 3. Delete news_articles
        print("Deleting all news_articles...")
        res_art = session.execute(text("DELETE FROM news_articles"))
        print(f"Deleted {res_art.rowcount} rows from news_articles.")

        # Reset sequences if any
        try:
            session.execute(text("ALTER SEQUENCE IF EXISTS news_articles_id_seq RESTART WITH 1"))
            session.execute(text("ALTER SEQUENCE IF EXISTS google_document_records_id_seq RESTART WITH 1"))
            session.execute(text("ALTER SEQUENCE IF EXISTS estd_duplicate_index_id_seq RESTART WITH 1"))
            print("Restarted primary key sequences to 1.")
        except Exception as seq_err:
            print(f"Sequence reset note: {seq_err}")

        session.commit()
        print("=" * 60)
        print("POST-DELETION VERIFICATION:")
        gdoc_after = session.execute(text("SELECT count(*) FROM google_document_records")).scalar()
        dup_after = session.execute(text("SELECT count(*) FROM estd_duplicate_index")).scalar()
        art_after = session.execute(text("SELECT count(*) FROM news_articles")).scalar()
        cat_after = session.execute(text("SELECT count(*) FROM categories")).scalar()
        subcat_after = session.execute(text("SELECT count(*) FROM subcategories")).scalar()

        print(f"google_document_records count: {gdoc_after}")
        print(f"estd_duplicate_index count:   {dup_after}")
        print(f"news_articles count:           {art_after}")
        print(f"categories count (intact):     {cat_after}")
        print(f"subcategories count (intact):  {subcat_after}")
        print("=" * 60)
        
        if art_after == 0 and gdoc_after == 0 and dup_after == 0:
            print("SUCCESS: All news articles data deleted cleanly from the database!")
        else:
            print("WARNING: Some records could not be deleted.")

if __name__ == "__main__":
    delete_all_articles()
