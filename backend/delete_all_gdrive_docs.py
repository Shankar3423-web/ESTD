"""Script to delete all article documents from Google Drive while preserving all folders and subfolders."""
import os
import sys
import time
import urllib.parse
from pathlib import Path

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
from backend.step8_gdrive_output.services.gdrive_service import GoogleDriveService, GDRIVE_API_BASE
from backend.step8_gdrive_output.services.folder_resolver import CANONICAL_SUBCATEGORY_FOLDERS

def main():
    # 1. Check if auth code passed via command line
    auth_code = None
    for i, arg in enumerate(sys.argv):
        if arg == "--code" and i + 1 < len(sys.argv):
            auth_code = sys.argv[i + 1]
            break
        elif arg.startswith("--code="):
            auth_code = arg.split("=", 1)[1]
            break

    if auth_code:
        # If user passes full URL like https://antigravity.google/oauth-callback?code=4/0A...
        if "code=" in auth_code:
            parsed = urllib.parse.urlparse(auth_code)
            params = urllib.parse.parse_qs(parsed.query)
            if "code" in params:
                auth_code = params["code"][0]
            else:
                auth_code = auth_code.split("code=")[-1].split("&")[0]

        auth_code = urllib.parse.unquote(auth_code.strip())
        print(f"[OAuth] Exchanging authorization code for fresh tokens...")
        try:
            exchange_code_for_tokens(auth_code)
            print("[OAuth] SUCCESS: Fresh tokens obtained and saved!")
        except Exception as e:
            print(f"[OAuth] ERROR exchanging code: {e}")
            sys.exit(1)

    # 2. Verify token
    try:
        svc = GoogleDriveService()
        headers = svc._get_headers()
        import httpx
        test_resp = httpx.get(f"{GDRIVE_API_BASE}/about?fields=user", headers=headers, timeout=10.0)
        if test_resp.status_code != 200:
            raise Exception(f"HTTP {test_resp.status_code}: {test_resp.text}")
        user_info = test_resp.json().get('user', {})
        print(f"[OAuth] Authenticated as Google user: {user_info.get('displayName')} ({user_info.get('emailAddress')})")
    except Exception as exc:
        auth_url = generate_authorization_url()
        print("\n" + "=" * 70)
        print("GOOGLE DRIVE AUTHORIZATION REQUIRED")
        print("=" * 70)
        print(f"Error validating token: {exc}\n")
        print("Please authorize with Google Drive by opening:")
        print(auth_url)
        print("\nThen run this script with:")
        print("python delete_all_gdrive_docs.py --code <YOUR_AUTH_CODE>")
        print("=" * 70)
        sys.exit(2)

    # 3. Scan and collect all documents across all category and subcategory folders
    print("\n" + "=" * 60)
    print("SCANNING GOOGLE DRIVE FOR ALL ARTICLE DOCUMENTS")
    print("=" * 60)

    # Load root folder and category folder IDs from environment
    from backend.step8_gdrive_output.config.gdrive_settings import get_step8_settings
    settings = get_step8_settings()

    folder_ids_to_scan = [settings.root_folder_id]
    category_folders = [
        settings.tech_folder_id,
        settings.entertainment_folder_id,
        settings.sports_folder_id,
        settings.developments_folder_id,
        settings.business_finance_folder_id,
    ]
    folder_ids_to_scan.extend([f for f in category_folders if f])

    # Add all 37 canonical subcategory folders
    for cat_name, subcats in CANONICAL_SUBCATEGORY_FOLDERS.items():
        for subcat_name, f_id in subcats.items():
            if f_id and f_id not in folder_ids_to_scan:
                folder_ids_to_scan.append(f_id)

    print(f"Total folder locations being inspected: {len(folder_ids_to_scan)}")

    documents_to_delete = {}

    for folder_id in folder_ids_to_scan:
        query = f"'{folder_id}' in parents and mimeType != 'application/vnd.google-apps.folder' and trashed = false"
        try:
            files = svc.search_files(query=query, limit=100)
            for f in files:
                documents_to_delete[f['id']] = {
                    'name': f.get('name'),
                    'mimeType': f.get('mimeType'),
                    'parent': folder_id
                }
        except Exception as e:
            print(f"  Warning querying folder {folder_id}: {e}")

    # Also search any file named starting with 'ESTD - ' anywhere in Drive that isn't a folder
    try:
        estd_files = svc.search_files(
            query="name contains 'ESTD -' and mimeType != 'application/vnd.google-apps.folder' and trashed = false",
            limit=100
        )
        for f in estd_files:
            if f['id'] not in documents_to_delete:
                documents_to_delete[f['id']] = {
                    'name': f.get('name'),
                    'mimeType': f.get('mimeType'),
                    'parent': 'ESTD Name Match'
                }
    except Exception as e:
        print(f"  Warning searching for ESTD named files: {e}")

    print(f"\nDiscovered {len(documents_to_delete)} document files to delete.")
    if not documents_to_delete:
        print("Zero article documents found in Google Drive. All folders are clean!")
        return

    # 4. Delete each document permanently (NOT folders or subfolders)
    print("\n" + "=" * 60)
    print(f"DELETING {len(documents_to_delete)} DOCUMENTS (FOLDERS PRESERVED)")
    print("=" * 60)

    deleted_count = 0
    failed_count = 0

    for doc_id, meta in documents_to_delete.items():
        doc_name = meta['name']
        try:
            svc.delete_file(doc_id)
            deleted_count += 1
            print(f"[{deleted_count}/{len(documents_to_delete)}] Deleted doc: '{doc_name}' (ID: {doc_id})")
        except Exception as err:
            failed_count += 1
            print(f"FAILED deleting doc '{doc_name}' (ID: {doc_id}): {err}")

    print("\n" + "=" * 60)
    print("DELETION SUMMARY:")
    print(f"Total documents targeted: {len(documents_to_delete)}")
    print(f"Successfully deleted:     {deleted_count}")
    print(f"Failed:                   {failed_count}")
    print("All category and subcategory folders remain completely untouched and preserved.")
    print("=" * 60)

if __name__ == "__main__":
    main()
