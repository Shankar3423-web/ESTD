"""Create and verify all 7 Canonical Developments Subcategory Folders in Google Drive.

Subcategories:
1. Government & Public Policy (DEV_GOV_POLICY, ID: 25)
2. Infrastructure & Urban Planning (DEV_INFRA, ID: 26)
3. Energy, Climate & Environment (DEV_ENERGY_CLIMATE, ID: 27)
4. Health & Medical Sciences (DEV_HEALTH_MED, ID: 28)
5. Education & Learning Policy (DEV_EDUCATION, ID: 29)
6. Science & Research Discoveries (DEV_SCIENCE_RESEARCH, ID: 30)
7. Global Affairs & Geopolitics (DEV_GLOBAL_AFFAIRS, ID: 31)
"""
import json
import sys
from pathlib import Path

# Setup paths
backend_dir = Path(__file__).resolve().parent
project_root = backend_dir.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from backend.step8_gdrive_output.services.gdrive_service import GoogleDriveService

DEVELOPMENTS_ROOT_FOLDER_ID = "14ENJOk8LkChMt792K5s3_jD6FzVc_g1D"

DEVELOPMENTS_SUBCATEGORIES = [
    "Government & Public Policy",
    "Infrastructure & Urban Planning",
    "Energy, Climate & Environment",
    "Health & Medical Sciences",
    "Education & Learning Policy",
    "Science & Research Discoveries",
    "Global Affairs & Geopolitics",
]


def main():
    print("=" * 80)
    print("ESTD - CREATE & VERIFY DEVELOPMENTS SUBCATEGORY FOLDERS IN GOOGLE DRIVE")
    print(f"Parent Developments Folder ID: {DEVELOPMENTS_ROOT_FOLDER_ID}")
    print("=" * 80)

    gdrive_service = GoogleDriveService()

    # Verify parent folder metadata
    root_meta = gdrive_service.get_file_metadata(DEVELOPMENTS_ROOT_FOLDER_ID)
    print(f"Verified Parent: {root_meta.get('name')} (ID: {root_meta.get('id')}, Parents: {root_meta.get('parents')})\n")

    folder_map = {}
    for subcat in DEVELOPMENTS_SUBCATEGORIES:
        try:
            folder = gdrive_service.get_or_create_folder(
                name=subcat,
                parent_id=DEVELOPMENTS_ROOT_FOLDER_ID,
            )
            folder_map[subcat] = {
                "id": folder["id"],
                "name": folder.get("name", subcat),
                "parent_id": DEVELOPMENTS_ROOT_FOLDER_ID,
                "webViewLink": folder.get("webViewLink", f"https://drive.google.com/drive/folders/{folder['id']}"),
            }
            print(f" [VERIFIED/CREATED] {subcat:<35} -> ID: {folder['id']}")
        except Exception as exc:
            print(f" [FAILED]           {subcat:<35} -> Error: {exc}")

    print("\n" + "=" * 80)
    print("CANONICAL DEVELOPMENTS SUBCATEGORY FOLDERS SUMMARY:")
    print("=" * 80)
    for name, info in folder_map.items():
        print(f"\"{name}\": \"{info['id']}\",")
    print("=" * 80)
    print(f"Total Folders: {len(folder_map)} / {len(DEVELOPMENTS_SUBCATEGORIES)}")


if __name__ == "__main__":
    main()
