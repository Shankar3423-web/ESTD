"""Inspection script to list all articles and Google Drive documents before deletion."""
import os
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent
project_root = backend_dir.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from backend.database.connection.session import get_db_session
from backend.database.models.news_article import NewsArticle
from backend.database.models.category import Category
from backend.database.models.subcategory import Subcategory
from backend.database.models.google_document_record import GoogleDocumentRecord
from backend.database.models.duplicate_index_record import DuplicateIndexRecord
from backend.step8_gdrive_output.services.gdrive_service import GoogleDriveService
from backend.step8_gdrive_output.services.folder_resolver import CANONICAL_SUBCATEGORY_FOLDERS

def main():
    svc = GoogleDriveService()
    
    with get_db_session() as s:
        articles_count = s.query(NewsArticle).count()
        gdocs_count = s.query(GoogleDocumentRecord).count()
        duplicates_count = s.query(DuplicateIndexRecord).count()
        categories_count = s.query(Category).count()
        subcategories_count = s.query(Subcategory).count()
        
        print("=== DATABASE CURRENT STATE ===")
        print(f"NewsArticles count: {articles_count}")
        print(f"GoogleDocumentRecords count: {gdocs_count}")
        print(f"DuplicateIndexRecord count: {duplicates_count}")
        print(f"Categories count (Taxonomy): {categories_count}")
        print(f"Subcategories count (Taxonomy): {subcategories_count}")
        
        # Collect all google_document_ids from DB
        gdoc_records = s.query(GoogleDocumentRecord).all()
        db_doc_ids = {r.google_document_id: r.document_title for r in gdoc_records if r.google_document_id}
        print(f"Distinct Google Doc IDs in DB: {len(db_doc_ids)}")

    # Check Google Drive files across canonical subfolders
    print("\n=== SCANNING GOOGLE DRIVE SUBFOLDERS FOR DOCUMENTS ===")
    total_gdrive_docs = {}
    
    for cat_name, subcats in CANONICAL_SUBCATEGORY_FOLDERS.items():
        for subcat_name, folder_id in subcats.items():
            # Query files in folder that are NOT folders
            query = f"'{folder_id}' in parents and mimeType != 'application/vnd.google-apps.folder' and trashed = false"
            try:
                files = svc.search_files(query=query, limit=100)
                if files:
                    print(f"[{cat_name} -> {subcat_name}] Found {len(files)} docs in folder {folder_id}")
                    for f in files:
                        total_gdrive_docs[f['id']] = {
                            'name': f.get('name'),
                            'category': cat_name,
                            'subcategory': subcat_name,
                            'folder_id': folder_id
                        }
            except Exception as e:
                print(f"Error querying folder {folder_id} for {cat_name}/{subcat_name}: {e}")

    # Also search general files with name starting with 'ESTD -' or in root
    print(f"\nTotal non-folder documents found inside canonical subfolders: {len(total_gdrive_docs)}")
    
    # Check if any db_doc_ids were outside canonical subfolders
    missing_from_scan = set(db_doc_ids.keys()) - set(total_gdrive_docs.keys())
    print(f"DB doc IDs not in scanned subfolders (maybe in parent category folder or root): {len(missing_from_scan)}")
    for missing_id in list(missing_from_scan)[:10]:
        try:
            meta = svc.get_file_metadata(missing_id)
            print(f"  Missing Doc ID {missing_id}: '{meta.get('name')}', trashed={meta.get('trashed')}, parents={meta.get('parents')}")
            total_gdrive_docs[missing_id] = {
                'name': meta.get('name'),
                'category': 'Unknown/Direct',
                'subcategory': 'Direct',
                'folder_id': str(meta.get('parents'))
            }
        except Exception as e:
            print(f"  Could not get metadata for missing ID {missing_id}: {e}")

    print(f"\nTOTAL ALL UNIQUE GOOGLE DOCUMENTS TO DELETE: {len(total_gdrive_docs)}")

if __name__ == "__main__":
    main()
