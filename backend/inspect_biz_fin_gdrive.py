import json
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent
project_root = backend_dir.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from backend.step8_gdrive_output.services.gdrive_service import GoogleDriveService, GDRIVE_API_BASE

def inspect_biz_fin_drive():
    service = GoogleDriveService()
    root_id = "1RjdnF8JcwGp-OyNipwM20Gg8XrcQJEk8"
    biz_folder_id = "1832eaKMfMEq-wS27eLwpOxqvAW7ZzkLu"
    
    print("=" * 80)
    print("INSPECTING GOOGLE DRIVE FOR BUSINESS & FINANCE")
    print("=" * 80)
    
    print(f"\n1. Checking ESTD CONTENT Root: {root_id}")
    root_meta = service.get_file_metadata(root_id)
    print(f"Root Meta: name={root_meta.get('name')}, id={root_meta.get('id')}, trashed={root_meta.get('trashed')}")
    
    print(f"\n2. Listing all category folders under Root ({root_id}):")
    query = f"'{root_id}' in parents and trashed = false"
    params = {
        "q": query,
        "fields": "files(id, name, mimeType, webViewLink, createdTime)",
        "pageSize": 100
    }
    resp = service._request_with_retry("GET", f"{GDRIVE_API_BASE}/files", params=params)
    root_children = resp.json().get("files", [])
    for c in root_children:
        print(f" - [{c.get('mimeType')}] {c.get('name')} (ID: {c.get('id')})")
        
    print(f"\n3. Checking Business & Finance Folder ({biz_folder_id}):")
    try:
        biz_meta = service.get_file_metadata(biz_folder_id)
        print(f"B&F Meta: name={biz_meta.get('name')}, id={biz_meta.get('id')}, parents={biz_meta.get('parents')}, trashed={biz_meta.get('trashed')}")
    except Exception as exc:
        print(f"Error fetching B&F folder metadata: {exc}")
        
    print(f"\n4. Listing children inside Business & Finance Folder ({biz_folder_id}):")
    query = f"'{biz_folder_id}' in parents and trashed = false"
    params = {
        "q": query,
        "fields": "files(id, name, mimeType, webViewLink, createdTime)",
        "pageSize": 100
    }
    resp = service._request_with_retry("GET", f"{GDRIVE_API_BASE}/files", params=params)
    biz_children = resp.json().get("files", [])
    print(f"Found {len(biz_children)} items in Business & Finance folder:")
    for c in biz_children:
        print(f" - [{c.get('mimeType')}] {c.get('name')} (ID: {c.get('id')})")
        
    print("\n5. Checking historical document 1 (Article 3): 1QPcN5maIXN-ZnaSEnff0FJMLCQqUKqMOrcE_N6U8sMs")
    try:
        doc1 = service.get_file_metadata("1QPcN5maIXN-ZnaSEnff0FJMLCQqUKqMOrcE_N6U8sMs")
        print(f"Doc 1 Meta: name={doc1.get('name')}, parents={doc1.get('parents')}, trashed={doc1.get('trashed')}")
    except Exception as exc:
        print(f"Error checking Doc 1: {exc}")

    print("\n6. Checking historical document 2 (Article 561): 1UMXX07YBhEcNzqlpqe2bQw7kmlSaDP6aXpNDYtbKOF8")
    try:
        doc2 = service.get_file_metadata("1UMXX07YBhEcNzqlpqe2bQw7kmlSaDP6aXpNDYtbKOF8")
        print(f"Doc 2 Meta: name={doc2.get('name')}, parents={doc2.get('parents')}, trashed={doc2.get('trashed')}")
    except Exception as exc:
        print(f"Error checking Doc 2: {exc}")

if __name__ == "__main__":
    inspect_biz_fin_drive()
