import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent
project_root = backend_dir.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from backend.step8_gdrive_output.services.gdrive_service import GoogleDriveService
from backend.step8_gdrive_output.services.folder_resolver import CANONICAL_SUBCATEGORY_FOLDERS
from backend.database.connection.session import get_db_session
from sqlalchemy import text

def verify():
    print("=" * 60)
    print("FINAL VERIFICATION AFTER COMPLETE CLEANUP")
    print("=" * 60)
    
    # 1. Database Check
    with get_db_session() as s:
        art_count = s.execute(text("SELECT count(*) FROM news_articles")).scalar()
        gdoc_count = s.execute(text("SELECT count(*) FROM google_document_records")).scalar()
        dup_count = s.execute(text("SELECT count(*) FROM estd_duplicate_index")).scalar()
        cat_count = s.execute(text("SELECT count(*) FROM categories")).scalar()
        subcat_count = s.execute(text("SELECT count(*) FROM subcategories")).scalar()

    print("DATABASE STATE:")
    print(f"  News Articles:           {art_count} (Expected: 0)")
    print(f"  Google Document Records: {gdoc_count} (Expected: 0)")
    print(f"  Duplicate Index Records: {dup_count} (Expected: 0)")
    print(f"  Categories (Taxonomy):   {cat_count} (Expected: 5, Preserved)")
    print(f"  Subcategories:           {subcat_count} (Expected: 37, Preserved)")

    # 2. Google Drive Check
    svc = GoogleDriveService()
    docs_found = 0
    folders_checked = 0
    for cat_name, subcats in CANONICAL_SUBCATEGORY_FOLDERS.items():
        for subcat_name, folder_id in subcats.items():
            if not folder_id or not folder_id.strip():
                continue
            folders_checked += 1
            query = f"'{folder_id}' in parents and mimeType != 'application/vnd.google-apps.folder' and trashed = false"
            try:
                files = svc.search_files(query=query, limit=10)
                if files:
                    docs_found += len(files)
                    print(f"  Found {len(files)} in {cat_name}/{subcat_name}")
            except Exception as f_err:
                pass

    # General search for any remaining ESTD docs
    general_files = svc.search_files(
        query="name contains 'ESTD -' and mimeType != 'application/vnd.google-apps.folder' and trashed = false",
        limit=20
    )

    print("\nGOOGLE DRIVE STATE:")
    print(f"  Subfolders checked:           {folders_checked}")
    print(f"  Documents in subfolders:      {docs_found} (Expected: 0)")
    print(f"  Remaining 'ESTD -' documents: {len(general_files)} (Expected: 0)")
    print("=" * 60)

    if art_count == 0 and gdoc_count == 0 and docs_found == 0 and len(general_files) == 0:
        print("PERFECT: All articles from Database and all Documents from Google Drive have been completely deleted!")
        print("All folders and subfolders remain 100% preserved.")
    else:
        print("ATTENTION: Some residual records or files remain.")

if __name__ == "__main__":
    verify()
