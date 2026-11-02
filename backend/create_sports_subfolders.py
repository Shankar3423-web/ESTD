"""Create and verify all 9 Canonical Sports Subcategory Folders in Google Drive.

Subcategories:
1. Cricket
2. Football
3. Tennis
4. Badminton
5. Motorsport
6. Hockey
7. Athletics & Olympic Sports
8. Esports & Competitive Gaming
9. Other Sports
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

from backend.step6_mcp.google.auth import (
    exchange_code_for_tokens,
    generate_authorization_url,
    refresh_access_token_if_needed,
)
from backend.step8_gdrive_output.services.gdrive_service import GoogleDriveService
from backend.step8_gdrive_output.services.folder_resolver import DriveFolderResolver

SPORTS_FOLDER_ID = "1KbF5HuofvQaB7fYhaNFQESn2Xq_xBFLs"

SPORTS_SUBCATEGORIES = [
    "Cricket",
    "Football",
    "Tennis",
    "Badminton",
    "Motorsport",
    "Hockey",
    "Athletics & Olympic Sports",
    "Esports & Competitive Gaming",
    "Other Sports",
]


def check_live_api():
    try:
        gdrive_service = GoogleDriveService()
        meta = gdrive_service.get_file_metadata(SPORTS_FOLDER_ID)
        return isinstance(meta, dict) and meta.get("id") == SPORTS_FOLDER_ID
    except Exception:
        return False


def main():
    print("=" * 80)
    print("ESTD - CREATE SPORTS SUBCATEGORY FOLDERS IN GOOGLE DRIVE")
    print("=" * 80)

    # Handle --code argument if provided
    auth_code = None
    for i, arg in enumerate(sys.argv):
        if arg == "--code" and i + 1 < len(sys.argv):
            auth_code = sys.argv[i + 1]
            break
        elif arg.startswith("--code="):
            auth_code = arg.split("=", 1)[1]
            break

    if auth_code:
        print("\n[OAuth] Exchanging authorization code...")
        try:
            exchange_code_for_tokens(auth_code)
            print("[OAuth] SUCCESS: Fresh tokens obtained and saved!")
        except Exception as exc:
            print(f"[OAuth] ERROR exchanging code: {exc}")
            sys.exit(1)

    # Check live API connection
    if not check_live_api():
        auth_url = generate_authorization_url()
        print("\n" + "!" * 80)
        print("GOOGLE OAUTH AUTHENTICATION REQUIRED")
        print("!" * 80)
        print("To create folders in your Google Drive, authorization is required.")
        print("\nPlease follow these 2 steps:")
        print("1. Open this link and authorize with shankar13052005@gmail.com:")
        print(f"\n   {auth_url}\n")
        print("2. Copy the authorization code from the redirected page, and run:")
        print("   python create_sports_subfolders.py --code <YOUR_CODE>")
        print("!" * 80)
        sys.exit(1)

    print(f"\nParent Sports Folder ID: {SPORTS_FOLDER_ID}")
    print("Creating all 9 subcategory folders in Google Drive under Sports...\n")

    gdrive_service = GoogleDriveService()
    resolver = DriveFolderResolver(gdrive_service)

    created_folders = {}
    for subcat in SPORTS_SUBCATEGORIES:
        try:
            folder = gdrive_service.get_or_create_folder(
                name=subcat,
                parent_id=SPORTS_FOLDER_ID,
            )
            created_folders[subcat] = {
                "id": folder["id"],
                "name": folder.get("name", subcat),
                "parent_id": SPORTS_FOLDER_ID,
                "webViewLink": folder.get("webViewLink", f"https://drive.google.com/drive/folders/{folder['id']}"),
            }
            print(f" [CREATED/VERIFIED] {subcat:<32} -> ID: {folder['id']}")
        except Exception as exc:
            print(f" [FAILED]           {subcat:<32} -> Error: {exc}")

    print("\n" + "=" * 80)
    print("SUMMARY OF SPORTS SUBCATEGORY FOLDERS IN GOOGLE DRIVE:")
    print("=" * 80)
    for name, info in created_folders.items():
        print(f"Subcategory: {name:<30} | Folder ID: {info['id']} | Link: {info.get('webViewLink')}")
    print("=" * 80)
    print(f"Total Folders: {len(created_folders)} / 9")


if __name__ == "__main__":
    main()
