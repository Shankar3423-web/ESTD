import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent
project_root = backend_dir.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from backend.step8_gdrive_output.services.gdrive_service import GoogleDriveService, GDRIVE_API_BASE

def inspect_subfolder_contents():
    service = GoogleDriveService()
    folders = [
        ("Government & Public Policy", "1PyI-Yv7c2HGsHMDNsd07ANRTtzqzGgTN"),
        ("Education & Learning Policy", "1v0gcs8WgaKIu9hFFisHFfsqSk9xH-DYX"),
        ("Energy & Green Technology", "1shwyIduVOaqlPjuu95s67ILFvRdzh_GL"),
        ("Scientific Discoveries & Research", "1XXwPetJeZ59AdYRh6J8QhYdIADsdj4np"),
    ]
    for name, fid in folders:
        q = f"'{fid}' in parents and trashed = false"
        params = {"q": q, "fields": "files(id, name, mimeType)", "pageSize": 50}
        resp = service._request_with_retry("GET", f"{GDRIVE_API_BASE}/files", params=params)
        files = resp.json().get("files", [])
        print(f"\nFolder '{name}' ({fid}): {len(files)} files")
        for f in files:
            print(f"  - [{f.get('mimeType')}] {f.get('name')} (ID: {f.get('id')})")

if __name__ == "__main__":
    inspect_subfolder_contents()
