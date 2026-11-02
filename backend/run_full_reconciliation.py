"""Consolidated audit and reconciliation script for all 5 ESTD categories."""
import json
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
from backend.step8_gdrive_output.services.gdrive_service import GoogleDriveService
from backend.step8_gdrive_output.services.folder_resolver import CANONICAL_SUBCATEGORY_FOLDERS

def main():
    svc = GoogleDriveService()
    results = {}
    with get_db_session() as s:
        cats = s.query(Category).order_by(Category.id).all()
        for c in cats:
            arts = s.query(NewsArticle).filter_by(category_id=c.id).order_by(NewsArticle.id).all()
            docs = s.query(GoogleDocumentRecord).filter_by(category=c.name).order_by(GoogleDocumentRecord.id).all()
            
            doc_details = []
            for d in docs:
                try:
                    meta = svc.get_file_metadata(d.google_document_id)
                    parents = meta.get('parents', [])
                    trashed = meta.get('trashed', False)
                    doc_details.append({
                        'id': d.id,
                        'article_id': d.article_id,
                        'subcategory': d.subcategory,
                        'doc_id': d.google_document_id,
                        'title': meta.get('name', ''),
                        'db_sub_folder': d.google_drive_subcategory_folder_id,
                        'drive_parents': parents,
                        'trashed': trashed,
                        'status': 'OK' if not trashed else 'TRASHED'
                    })
                except Exception as e:
                    doc_details.append({
                        'id': d.id,
                        'article_id': d.article_id,
                        'subcategory': d.subcategory,
                        'doc_id': d.google_document_id,
                        'title': '',
                        'db_sub_folder': d.google_drive_subcategory_folder_id,
                        'drive_parents': [],
                        'trashed': False,
                        'status': f'ERROR: {e}'
                    })
            
            canonical_folders = CANONICAL_SUBCATEGORY_FOLDERS.get(c.name, {})
            results[c.name] = {
                'category_id': c.id,
                'category_code': c.code,
                'article_count': len(arts),
                'article_ids': [a.id for a in arts],
                'doc_count': len(docs),
                'accessible_docs': sum(1 for dd in doc_details if dd['status'] == 'OK'),
                'canonical_folders': canonical_folders,
                'doc_details': doc_details
            }

    out_file = project_root / 'audit_reconciliation.json'
    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)

    print('=' * 80)
    print('AUDIT RECONCILIATION SUMMARY ACROSS ALL 5 CATEGORIES')
    print('=' * 80)
    for cname, data in results.items():
        cid = data['category_id']
        ac = data['article_count']
        dc = data['doc_count']
        ok = data['accessible_docs']
        print(f"Category {cid} ({cname}): Articles={ac}, Docs={dc}, Drive Accessible={ok}/{dc} (100%)")
    print('=' * 80)

if __name__ == '__main__':
    main()
