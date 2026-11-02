import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent
project_root = backend_dir.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from backend.step8_gdrive_output.services.gdrive_service import GoogleDriveService, GDRIVE_API_BASE

def inspect_drive():
    service = GoogleDriveService()
    root_id = "1RjdnF8JcwGp-OyNipwM20Gg8XrcQJEk8"
    dev_folder_id = "14ENJOk8LkChMt792K5s3_jD6FzVc_g1D"
    
    print(f"Checking ESTD CONTENT Root: {root_id}")
    root_meta = service.get_file_metadata(root_id)
    print(f"Root Meta: name={root_meta.get('name')}, id={root_meta.get('id')}, trashed={root_meta.get('trashed')}")
    
    print(f"\nChecking Developments Folder: {dev_folder_id}")
    dev_meta = service.get_file_metadata(dev_folder_id)
    print(f"Developments Meta: name={dev_meta.get('name')}, id={dev_meta.get('id')}, parents={dev_meta.get('parents')}, trashed={dev_meta.get('trashed')}")
    
    print(f"\nListing children inside Developments Folder ({dev_folder_id}):")
    query = f"'{dev_folder_id}' in parents and trashed = false"
    params = {
        "q": query,
        "fields": "files(id, name, mimeType, webViewLink, createdTime)",
        "pageSize": 100
    }
    resp = service._request_with_retry("GET", f"{GDRIVE_API_BASE}/files", params=params)
    children = resp.json().get("files", [])
    
    print(f"Found {len(children)} items:")
    for c in children:
        print(f" - [{c.get('mimeType')}] {c.get('name')} (ID: {c.get('id')})")

if __name__ == "__main__":
    inspect_drive()
